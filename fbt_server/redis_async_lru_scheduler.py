#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
data structures in redis
keys_modified: set, key_names have been modified since readed from mongodb to redis
lru_queue: zset, member: key_name, score: time

mongo <<==>> redis

common field name means field name stored in hash, complex field( subfield) name means field name stored in set, list, or zset.

NOTE: 
for names Not exists, smembers return set([])
                      lrange return []
                      zrange return []
                      hgetall return {}
                      hmget return [None,...]
                      get return None

for key Not exists, hmget return a None in a list in the same order as args
                      zrank return None

DO NOT do this for complex field
when unset a field of a document, just hdel the key and unset mongo at the same time.
when set a field of a document to None, just hdel the key and write update to mongo at the same time.

when empty a complex field, deleting it in redis is just OK. This update will be handled by write-back.

when a field in mongo is None, results from redis will not contain it, so field NOT IN the dict of results.
when writing back, a field name is in the keys_modified list but we get None from redis, just write empty_val in ComplexField to mongo
"""

import redis
import getopt
import sys
import time
import uuid
import json
#import heapq
from collections import deque
from time import time, sleep
from bson import json_util
from functools import partial
from itertools import izip
from copy import deepcopy, copy

from tornado.concurrent import Future
from tornado import ioloop, gen
#from async_redis.asyncRedis import AsyncStrictRedis as StrictRedis
from redis_handler import RedisHandler
#import motorclient
import mongoclient
#from tasks_lru import write_redis, keep_longer

__author__ = 'spark'

KEYS_MODIFIED_SET = 'keys_modified'
LRU_QUEUE = 'lru_queue'
LRU_QUEUE_NUM_MIN = 10000
LRU_QUEUE_NUM_MAX = 15000
EVERY_ZRANGE_NUM = 1000
LOCK_TIMEOUT = 10
EXPIRE_TIME = 600   # 20

def is_future(x):
    return isinstance(x, Future)

def make_lockname(key_name):
    return 'lock:' + key_name

def acquire_lock_with_timeout(conn, key_name, lock_timeout=LOCK_TIMEOUT):
    """
    Tell scheduler that I will do sth. with this key in LOCK_TIMEOUT seconds, so it can't write it back to mongo
    """
    identifier = str(uuid.uuid4())
    lockname = make_lockname(key_name)
    return conn.setex(lockname, lock_timeout, identifier)

def make_key_name(*args):
    return ':'.join(map(str, args))

# make complex field key name in redis
def make_sub_key_name(*args):
    return '.'.join(map(str, args))

class LocalLRUCache(object):
    """docstring for LocalLRUCache"""
    def __init__(self, expire_time):
        self.expire_time = expire_time
        self.cache_dict = dict()
        # {key: [value, count_in_heapq]}
        self.lru_queue = deque()

    def _expire_worker(self):
        while self.lru_queue and self.lru_queue[0][0] + self.expire_time < time():
            _time, _key = self.lru_queue.popleft()
            pop_res = self.cache_dict[_key]
            pop_res[1] -= 1
            if 0 == pop_res[1]:
                self.cache_dict.pop(_key)

    def get(self, key):
        res = self.cache_dict.get(key, None)
        if res is not None:
            res[1] += 1
            self.lru_queue.append((time(), key))
            res = res[0]
        self._expire_worker()
        return res[0]

    def set(self, key, value):
        self.lru_queue.append((time(), key))
        res = self.cache_dict.get(key, None)
        if res is not None:
            res[1] += 1
        else:
            self.cache_dict[key] = [value, 1]
        self._expire_worker()

    def mget(self, *keys):
        value_list  = list()
        for key in keys:
            res = self.cache_dict.get(key, None)
            if res is not None:
                value_list.append(res[0])
                self.lru_queue.append((time(), key))
                res[1] += 1
            else:
                value_list.append(None)
        self._expire_worker()
        return value_list

    def mset(self, key_value_pair_list):
        not_in_cache_list = list()
        for key, value in key_value_pair_list:
            res = self.cache_dict.get(key, None)
            if res:
                res[0] = value
                res[1] += 1
            else:
                not_in_cache_list.append((key, [value, 1]))
            self.lru_queue.append((time(), key))

        self._expire_worker()
        self.cache_dict.update(dict(not_in_cache_list))

class IndirectField(object):
    def set(self, val) :
        raise NotImplementedError()
    def get(self, val):
        raise NotImplementedError()

    def __call__(self, val):
        return self.get(val)

class DictField(IndirectField):
    def set(self, val) :
        if not isinstance(val, str):
            return json.dumps(val, default=json_util.default)
        else:
            return val
    def get(self, val):
        if isinstance(val, str):
            return json.loads(val, object_hook=json_util.object_hook)
        else:
            return val

class NumberField(IndirectField):
    def __init__(self, field_type=int):
        self.field_type = field_type
    def set(self, val) :
        return val
    def get(self, val):
        return self.field_type(val)

class ComplexField(object):
    """docstring for ComplexField"""
    empty_val = list()
    def __init__(self, field_name, field_type=None):
        self.field_name = field_name
        self.field_type = field_type

    def __get__(self, obj, objtype):
        self.conn = obj.redis_delegate.conn
        self.pipeline = self.conn.pipeline()
        self.col = obj
        self.col_key_name = obj._key
        self.key_name = make_sub_key_name(obj._key, self.field_name)
        return self

    def get(self):
        raise NotImplementedError()

    def set(self, val):
        raise NotImplementedError()

    def get_for_writeback(self):
        raise NotImplementedError()

    def _handle_members_list(self, member_score_list, is_set=True):
        if isinstance(self.field_type, IndirectField):
            tmp = list()
            if is_set:
                f = self.field_type.set
            else:
                f = self.field_type.get
            for v in member_score_list:
                tmp.append(f(v))
            return tmp
        else:
            return member_score_list

    def _handle_one_member(self, val, is_set=True):
        if isinstance(self.field_type, IndirectField):
            if is_set:
                return self.field_type.set(val)
            else:
                return self.field_type.get(val)
        else:
            return val

    # need to be called after update
    def record_modify(self):
        pipeline = self.pipeline
        if self.col.expire <= 0:
            pipeline.sadd(KEYS_MODIFIED_SET, self.key_name)
            pipeline.zadd(LRU_QUEUE, time.time(), self.key_name)
        return pipeline.execute()

class ZsetField(ComplexField):
    """
    docstring for ZsetField
    Member type other than string, float, int and long are not concerned currently!
    """
    def __init__(self, field_name, member_name, member_type, score_name, score_type):
        super(ZsetField, self).__init__(field_name)
        #assert type(member_type) in [str, int, long, float]
        self.member_name = member_name
        self.member_type = member_type
        self.score_name = score_name
        self.score_type = score_type

    def _handle_members_list(self, member_score_list):
        if isinstance(self.member_type, IndirectField):
            i = 1
            tmp = list()
            while i < len(member_score_list):
                tmp.append(self.member_type.set(member_score_list[i]))
                i += 2
            return tmp
        else:
            return member_score_list

    # val: [{score: score, member_name: member_name}]
    @gen.coroutine
    def set(self, val):
        pipeline = self.pipeline

        pipeline.delete(self.key_name)
        if val:
            member_score_list = list()
            for v in val:
                if self.member_name in v and self.score_name in v:
                    member_score_list.append(v[self.score_name])
                    member_score_list.append(v[self.member_name])
                else :
                    raise Exception("Error: %s miss %s or %s" % (str(v), self.member_name, self.score_name))
            if member_score_list:
                self._handle_members_list(member_score_list)
                pipeline.zadd(self.key_name, *member_score_list)
        yield self.record_modify()

    @gen.coroutine
    def zcard(self):
        yield self.col.make_data_in_redis(False, self.field_name)
        res = yield self.conn.zcard(self.key_name)
        raise gen.Return(res)

    @gen.coroutine
    def zadd(self, *values, **kwargs):
        yield self.col.make_data_in_redis(False, self.field_name)

        values = self._handle_members_list(values)
        self.pipeline.zadd(self.key_name, *values, **kwargs)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def zscore(self, member):
        yield self.col.make_data_in_redis(False, self.field_name)
        score = yield self.conn.zscore(self.key_name, member)
        if score and self.score_type is not float:
            score = self.score_type(score)
        raise gen.Return(score)

    @gen.coroutine
    def zrem(self, *values):
        yield self.col.make_data_in_redis(False, self.field_name)

        values = self._handle_members_list(values)
        self.pipeline.zrem(self.key_name, *values)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    # Output: The return type is a list of (value, score) pairs
    @gen.coroutine
    def _zrange(self, start, end, need_lock):
        yield self.col._make_data_in_redis(need_lock, False, self.field_name)
        values = yield self.conn.zrange(self.key_name, start, end, withscores=True, score_cast_func=self.score_type)
        res = list()
        for v in values:
            res.append({self.member_name: self.member_type(v[0]), self.score_name: v[1]})
        raise gen.Return(res)

    def zrange(self, start, end):
        return self._zrange(start, end, True)

    def get(self):
        return self.zrange(0, -1)

    def get_for_writeback(self):
        return self._zrange(0, -1, False)

class SetField(ComplexField):
    @gen.coroutine
    def set(self, val):
        pipeline = self.pipeline
        pipeline.delete(self.key_name)
        if val:
            val = self._handle_members_list(val)
            self.pipeline.sadd(self.key_name, *val)
        yield self.record_modify()

    @gen.coroutine
    def scard(self):
        load_dict = yield self.col.make_data_in_redis(False, self.field_name)
        if self.field_name in load_dict:
            res = len(load_dict[self.field_name])
        else:
            res = yield self.conn.scard(self.key_name)
        raise gen.Return(res)

    @gen.coroutine
    def sadd(self, *values):
        pipeline = self.pipeline
        yield self.col.make_data_in_redis(False, self.field_name)
        values = self._handle_members_list(values)
        pipeline.sadd(self.key_name, *values)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def sismember(self, val):
        load_dict = yield self.col.make_data_in_redis(False, self.field_name)
        if self.field_name in load_dict:
            res = val in load_dict[self.field_name]
        else:
            val = self._handle_one_member(val)
            res = yield self.conn.sismember(self.key_name, val)
        raise gen.Return(res)

    @gen.coroutine
    def _smembers(self, need_lock):
        load_dict = yield self.col._make_data_in_redis(need_lock, False, self.field_name)
        if self.field_name in load_dict:
            res = load_dict[self.field_name]
        else:
            res = yield self.conn.smembers(self.key_name)
            if self.field_type:
                res = map(self.field_type, res)
        raise gen.Return(set(res))

    @gen.coroutine
    def srem(self, *values):
        pipeline = self.pipeline
        yield self.col.make_data_in_redis(False, self.field_name)
        values = self._handle_members_list(values)
        pipeline.srem(self.key_name, *values)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    def smembers(self):
        return self._smembers(True)

    def get(self):
        return self.smembers()

    def get_for_writeback(self):
        return self._smembers(False)

class ListField(ComplexField):
    @gen.coroutine
    def set(self, val):
        pipeline = self.pipeline
        pipeline.delete(self.key_name)
        if val:
            val = self._handle_members_list(val)
            pipeline.rpush(self.key_name, *val)
        yield self.record_modify()

    @gen.coroutine
    def llen(self):
        load_dict = yield self.col.make_data_in_redis(False, self.field_name)
        if self.field_name in load_dict:
            res = len(load_dict[self.field_name])
        else:
            res = yield self.conn.llen(self.key_name)
        raise gen.Return(res)

    @gen.coroutine
    def lrem(self, count, val):
        pipeline = self.pipeline
        yield self.col.make_data_in_redis(False, self.field_name)
        val = self._handle_one_member(val)
        pipeline.lrem(self.key_name, count, val)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def ltrim(self, start, end):
        pipeline = self.pipeline
        yield self.col.make_data_in_redis(False, self.field_name)
        pipeline.ltrim(self.key_name, start, end)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def lindex(self, index):
        load_dict = yield self.col.make_data_in_redis(False, self.field_name)
        if self.field_name in load_dict:
            mem_list = load_dict[self.field_name]
            if index < len(mem_list) and index > - len(mem_list):
                res = mem_list[index]
            else :
                res = None
        else:
            res = yield self.conn.lindex(self.key_name, index)
            res = self._handle_one_member(res, False)
        raise gen.Return(res)

    @gen.coroutine
    def lpop(self):
        pipeline = self.pipeline
        yield self.col.make_data_in_redis(False, self.field_name)
        pipeline.lpop(self.key_name)
        res = yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def rpush(self, *val):
        pipeline = self.pipeline
        if val:
            val = self._handle_members_list(val)
            pipeline.rpush(self.key_name, *val)
        res =  yield self.record_modify()
        raise gen.Return(res[-3])

    @gen.coroutine
    def _lrange(self, start, end, need_lock):
        load_dict = yield self.col._make_data_in_redis(need_lock, False, self.field_name)
        if self.field_name in load_dict:
            mem_list = load_dict[self.field_name]
            if -1 != end:
                res = mem_list[start: end+1]
            else:
                res = mem_list[start:]
        else:
            res = yield self.conn.lrange(self.key_name, start, end)
            res = self._handle_members_list(res, False)
        raise gen.Return(res)

    def lrange(self, start, end):
        return self._lrange(start, end, True)

    def get(self):
        return self.lrange(0, -1)

    def get_for_writeback(self):
        return self._lrange(0, -1, False)

class CollectionMetaclass(type):
    def __new__(cls, name, bases, attrs):
        subfield_names = list()
        for k, v in attrs.iteritems():
            if isinstance(v, ComplexField):
                subfield_names.append(k)
            elif isinstance(v, IndirectField):
                cls._none_string_key_name_dict[k] = v
        attrs['_subfield_names'] = subfield_names
        if '_ignore_field_names' in attrs:
            ignore_field_name_list = attrs['_ignore_field_names'] + ['_id', attrs['_key_name']]
        else:
            ignore_field_name_list = ['_id', attrs['_key_name']]
        attrs['_ignore_field_names'] = dict.fromkeys(ignore_field_name_list, 0)
        return type.__new__(cls, name, bases, attrs)

class CollectionBase(object):
    """
    Don't define vars not starting with '_' by yourself
    """
    __metaclass__ = CollectionMetaclass
    _mongo_key = None
    # _key in the redis
    _key = None
    # key name in mongo
    _key_name = ""
    _key_type = None
    _col_name = ""
    _none_string_key_name_dict = dict()
    _ignore_field_names = list()
    redis_delegate = None

    '''
    if expire <= 0, when loading date into redis, add key names of this collection to  LRU_QUEUE;
    else give a expire time to it, and acquire_lock_with_timeout and write_back are of no use
    '''
    def __init__(self, key_name=None, expire=0):
        if key_name:
            self._key_name = key_name
        self.expire = expire
    
    # need to be called after update
    @gen.coroutine
    def record_modify(self):
        pipeline = self.pipeline
        if self.expire <= 0:
            pipeline.sadd(KEYS_MODIFIED_SET, self._key)
            pipeline.zadd(LRU_QUEUE, time.time(), self._key)
        return pipeline.execute()

    def _get_hashes_by_dict(self, hashes_dict):
        for k, v in self._none_string_key_name_dict.iteritems():
            if k in hashes_dict:
                hashes_dict[k] = v(hashes_dict[k])
        return hashes_dict

    def get_all_subfield_names(self):
        subfield_names = self.get_subfield_names()
        subfield_key_names = map(partial(make_sub_key_name, self._key), subfield_names)
        return subfield_key_names, subfield_names

    def get_subfield_names(self):
        return self._subfield_names

    def set_redis_delegate(self, redis_delegate):
        self.redis_delegate = redis_delegate
        self.conn = redis_delegate.conn
        self.pipeline = self.conn.pipeline()

    def __call__(self, key):
        self._mongo_key = key
        self._key = make_key_name(self._col_name, key)
        return self

    # get only common field
    @gen.coroutine
    def get(self, field_name):
        res = yield self.make_data_in_redis(True, field_name)
        res = res.get(field_name, None)
        if res and field_name in self._none_string_key_name_dict:
            # Tranform it
            res = self._none_string_key_name_dict[field_name](res)
        raise gen.Return(res)

    @gen.coroutine
    def set(self, field_name, value):
        assert field_name not in self.get_subfield_names()
        if value is None:
            mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
            mongo_key = self._mongo_key
            yield [self.conn.hdel(self._key, field_name), mongo_col.update({self._key_name: mongo_key}, {"$set": {field_name: None}}, True)]
        else:
            self.pipeline.hset(self._key, field_name, value)
            yield self.record_modify()

    def make_data_in_redis(self, need_load, *args):
        return self._make_data_in_redis(True, need_load, *args)

    @gen.coroutine
    def _make_data_in_redis(self, need_lock, need_load, *args):
        '''
        self: collection_self
        args: field names
        need_load: whether need to load all field in args to return, if False, only return fields not in redis which load from mongo
        '''
        conn = self.conn
        pipeline = self.pipeline
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)

        need_common_fields = False
        subfield_names = list()
        field_name_not_in_redis_list = list()
        load_result = dict()
        if args:
            for f in args:
                if f not in self.get_subfield_names():
                    need_common_fields = True
                else:
                    subfield_names.append(f)
            sub_key_names = map(partial(make_sub_key_name, self._key), subfield_names)
        else:
            sub_key_names, subfield_names = self.get_all_subfield_names()
            need_common_fields = True

        for sub_key_name, subfield_name in zip(sub_key_names, subfield_names):
            if self.expire <= 0:
                if need_lock:
                    yield [acquire_lock_with_timeout(conn, sub_key_name), conn.zadd(LRU_QUEUE, time.time(), sub_key_name)]
                else:
                    yield conn.zadd(LRU_QUEUE, time.time(), sub_key_name)
                is_exists = yield conn.exists(sub_key_name)
            else:
                # check whether it exists, if so, make it exists longer
                is_exists = yield conn.expire(subfield_name, self.expire)

            if not is_exists:
                ##print "try_fetch:", sub_key_name
                field_name_not_in_redis_list.append(subfield_name)
            elif need_load:
                load_result[subfield_name] = yield getattr(self, subfield_name).get() 

        if need_common_fields:
            if self.expire <= 0:
                if need_lock:
                    yield [acquire_lock_with_timeout(conn, self._key), conn.zadd(LRU_QUEUE, time.time(), self._key)]
                else:
                    yield conn.zadd(LRU_QUEUE, time.time(), self._key)
                is_exists = yield conn.exists(self._key)
            else:
                is_exists = yield conn.expire(self._key, self.expire)

            if is_exists:
                need_common_fields = False
                common_field_dict = yield self._get_all_hashes(self._mongo_key)
                if need_load:
                    load_result.update(common_field_dict)

        if field_name_not_in_redis_list or need_common_fields:
            mongo_key = self._mongo_key
            # don't kown all the common fields' name, so just reload all
            res = yield mongo_col.find_one({self._key_name: mongo_key}, self._ignore_field_names)
            #print res, self._col_name, self._key_name
            if res:
                # rm empty val
                to_be_pop_list = list()
                for k, v in res.iteritems():
                    if v is None:
                        to_be_pop_list.append(k)
                for k in to_be_pop_list:
                    res.pop(k)

                to_expire = list()
                for subfield_name in self.get_subfield_names():
                    if subfield_name in res:
                        val = res.pop(subfield_name)
                        if subfield_name in field_name_not_in_redis_list:
                            load_result[subfield_name] = val
                            yield getattr(self, subfield_name).set(val)
                            if self.expire > 0:
                                sub_key_name = make_sub_key_name(self._key, subfield_names)
                                to_expire.append(sub_key_name)

                if need_common_fields:
                    load_result.update(res)
                    yield conn.hmset(self._key, res)
                    if self.expire > 0:
                        to_expire.append(self._key)
                
                if to_expire:
                    for sk in to_expire:
                        pipeline.expire(sk, self.expire)
                yield pipeline.execute()

        raise gen.Return(load_result)

    @gen.coroutine
    def _get_all_hashes(self, key):
        res = yield self.conn.hgetall(make_key_name(self._col_name, key))
        raise gen.Return(self._get_hashes_by_dict(res))

    @gen.coroutine
    def update(self, key, doc_dict):
        #assert (self._key_name in doc_dict)
        doc_dict = deepcopy(doc_dict)
        #key = doc_dict.pop(self._key_name)
        self._key = make_key_name(self._col_name, key)
        self._mongo_key = key
        key_name = self._key_name
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)

        for field_name in self.get_subfield_names():
            if field_name in doc_dict:
                yield getattr(self, field_name).set(doc_dict.pop(field_name))

        if doc_dict:
            value_none_field_list = list()
            for k, v in doc_dict.items():
                if v is None:
                    doc_dict.pop(k)
                    value_none_field_list.append(k)
            if doc_dict:
                self.pipeline.hmset(self._key, doc_dict)
            if value_none_field_list:
                for k in value_none_field_list:
                    self.pipeline.hdel(self._key, k)
                yield [self.record_modify(), mongo_col.update({key_name: self._mongo_key}, {"$set": dict.fromkeys(value_none_field_list)}, True)]
            else:
                yield self.record_modify()
        else:
            yield self.record_modify()

    @gen.coroutine
    def find(self, key, field_name_list=None):
        self._key = make_key_name(self._col_name, key)
        self._mongo_key = key
        if field_name_list:
            res = yield self.make_data_in_redis(True, *field_name_list)
        else:
            res = yield self.make_data_in_redis(True)
        raise gen.Return(res)

    # only for common field, there is no need to record modification
    @gen.coroutine
    def delete(self, key, field):
        assert field not in self.get_subfield_names()
        self._key = make_key_name(self._col_name, key)
        self._mongo_key = key
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        yield [self.conn.hdel(self._key, field), mongo_col.update({self._key_name: key}, {"$unset": {field: 1}}, True)]

    @gen.coroutine
    def write_back(self, key, field_name=None):
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        #conn = self.redis_delegate.conn
        if field_name and field_name in self.get_subfield_names():
            res_list = yield getattr(self(key), field_name).get_for_writeback()
            res_list = list(res_list)
            yield mongo_col.update({self._key_name: key}, {"$set": {field_name: res_list}}, True)
        else:
            res_dict = yield self._get_all_hashes(key)
            if res_dict:
                yield mongo_col.update({self._key_name: key}, {"$set": res_dict}, True)

class StaticCollectionBase(object):
    """
    Don't define vars not starting with '_' by yourself, StaticCollectionBase just load all doc into a key
    """
    #_mongo_key = None
    # _key in the redis
    #_key = None
    # key name in mongo
    _key_name = ""
    _key_type = None
    _col_name = ""
    _ignore_field_names = list()
    _sort_field_names_dict = dict()
    redis_delegate = None

    '''
    if expire <= 0, when loading date into redis, add key names of this collection to  LRU_QUEUE;
    else give a expire time to it, and acquire_lock_with_timeout and write_back are of no use
    '''
    def __init__(self, key_name=None, expire=0):
        if key_name:
            self._key_name = key_name
        self.expire = expire
        self.local_cache = LocalLRUCache(expire or EXPIRE_TIME)

    def set_redis_delegate(self, redis_delegate):
        self.redis_delegate = redis_delegate
        self.conn = redis_delegate.conn
        self.pipeline = self.conn.pipeline()

    @gen.coroutine
    def find(self, mongo_key, query_dict=None, keep_order=False):
        if not mongo_key:
            raise gen.Return([])
        is_multi = True
        pipeline = self.pipeline
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        if isinstance(mongo_key, list):
            mongo_key_list = mongo_key
        elif isinstance(mongo_key, tuple) or isinstance(mongo_key, set):
            mongo_key_list = list(mongo_key)
        else:
            mongo_key_list = [mongo_key]
            is_multi = False

        res = list()
        not_in_local_mongo_key_list = list()
        local_res = list()

        cache_value_list = self.local_cache.mget(*mongo_key_list)
        for cache_value, k in zip(cache_value_list, mongo_key_list):
            if cache_value is not None:
                local_res.append(cache_value)
                if self.expire > 0:
                    redis_key = make_key_name(self._col_name, k)
                    pipeline.expire(redis_key, self.expire)
            else:
                not_in_local_mongo_key_list.append(k)
        yield pipeline.execute()

        if not_in_local_mongo_key_list:
            if query_dict:
                query_dict.update({self._key_name: {'$in': not_in_local_mongo_key_list}})
                res = yield mongo_col.find(query_dict, {'_id': 0}).to_list(None)
            else:
                res = yield mongo_col.find({self._key_name: {'$in': not_in_local_mongo_key_list}}, {'_id': 0}).to_list(None)

            if res:
                self.local_cache.mset([(r[self._key_name], r) for r in res])

        res = filter(None, res)
        redis_key_list = list()
        for r in res:
            mapping = dict()
            mongo_key = r[self._key_name]
            redis_key = make_key_name(self._col_name, mongo_key)
            redis_key_list.append(redis_key)

            for sort_field_name in self._sort_field_names_dict.keys():
                if sort_field_name in r:
                    mapping[sort_field_name] = r[sort_field_name]

            pipeline.hmset(redis_key, mapping)

        if self.expire > 0:
            for rk in redis_key_list:
                pipeline.expire(rk, self.expire)
        yield pipeline.execute()
        res += local_res

        # for debug
        if not res:
            raise gen.Return([])

        if is_multi:
            if keep_order:
                res = sorted(res, key=lambda x: mongo_key_list.index(x[self._key_name]))
            raise gen.Return(res)
        else:
            raise gen.Return(res[0])

    @gen.coroutine
    def old_find(self, mongo_key, query_dict=None, keep_order=False):
        if not mongo_key:
            raise gen.Return([])
        is_multi = True
        pipeline = self.pipeline
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        not_in_redis_mongo_key_list = list()
        in_redis_redis_key_list = list()
        if isinstance(mongo_key, list):
            mongo_key_list = mongo_key
        elif isinstance(mongo_key, tuple) or isinstance(mongo_key, set):
            mongo_key_list = list(mongo_key)
        else:
            mongo_key_list = [mongo_key]
            is_multi = False

        res = list()
        not_in_local_mongo_key_list = list()
        local_res = list()

        cache_redis_key_list = list()
        cache_value_list = self.local_cache.mget(*mongo_key_list)
        for cache_value, k in zip(cache_value_list, mongo_key_list):
            if cache_value is not None:
                local_res.append(cache_value)
                if self.expire > 0:
                    redis_key = make_key_name(self._col_name, k)
                    cache_redis_key_list.append(redis_key)
            else:
                not_in_local_mongo_key_list.append(k)
        #if cache_redis_key_list and self.expire > 0:
        #    keep_longer.delay(cache_redis_key_list, self.expire)
        '''
        if self.expire > 0:
            for rk in cache_redis_key_list:
                pipeline.expire(rk, self.expire)
            yield pipeline.execute()
        '''
        if not_in_local_mongo_key_list:
            for k in not_in_local_mongo_key_list:
                redis_key = make_key_name(self._col_name, k)
                if self.expire <= 0:
                    pipeline.exists(redis_key)
                else:
                    # check whether it exists, if so, make it exists longer
                    pipeline.expire(redis_key, self.expire)
            exists_list = yield pipeline.execute()
            for is_exists, mongo_key in zip(exists_list, not_in_local_mongo_key_list):
                if is_exists:
                    in_redis_redis_key_list.append(make_key_name(self._col_name, mongo_key))
                else:
                    not_in_redis_mongo_key_list.append(mongo_key)

            to_yield = list()
            redis_res = list()

            if in_redis_redis_key_list:
                for rk in in_redis_redis_key_list:
                    pipeline.hgetall(rk)
                to_yield = [pipeline.execute()]
            if not_in_redis_mongo_key_list:
                if query_dict:
                    query_dict.update({self._key_name: {'$in': not_in_redis_mongo_key_list}})
                    to_yield.append(mongo_col.find(query_dict, {'_id': 0}).to_list(None))
                else:
                    to_yield.append(mongo_col.find({self._key_name: {'$in': not_in_redis_mongo_key_list}}, {'_id': 0}).to_list(None))

            if in_redis_redis_key_list and not_in_redis_mongo_key_list:
                redis_res, res = yield to_yield
            elif in_redis_redis_key_list:
                redis_res = yield to_yield[0]
            elif not_in_redis_mongo_key_list:
                res = yield to_yield[0]

            for i, rr in enumerate(redis_res):
                if rr:
                    redis_key = in_redis_redis_key_list[i]
                    for sort_field_name, sort_field_name_type in self._sort_field_names_dict.iteritems():
                        if sort_field_name in rr:
                            rr[sort_field_name] = sort_field_name_type(float(rr[sort_field_name]))
                    if '_' in rr:
                        main_val = rr.pop('_')
                        rr.update(json.loads(main_val, object_hook=json_util.object_hook))
                    rr[self._key_name] = self._key_type(self.redis_delegate.parse_sub_key_name(redis_key)[1])
                    redis_res[i] = rr
            #write_redis.delay(res, self._key_name, self._col_name, self._sort_field_names_dict, self.expire)

            redis_key_list = list()
            for r in res:
                mapping = dict()
                new_r = copy(r)
                mongo_key = new_r.pop(self._key_name)
                redis_key = make_key_name(self._col_name, mongo_key)
                redis_key_list.append(redis_key)

                for sort_field_name in self._sort_field_names_dict.keys():
                    if sort_field_name in new_r:
                        mapping[sort_field_name] = new_r.pop(sort_field_name)
                mapping['_'] = json.dumps(new_r, default=json_util.default)
                pipeline.hmset(redis_key, mapping)
                yield pipeline.execute()

            #if redis_key_list and self.expire > 0:
            #    keep_longer.delay(redis_key_list, self.expire)
            '''
            if self.expire > 0:
                for rk in redis_key_list:
                    pipeline.expire(rk, self.expire)
                yield pipeline.execute()
            '''

            res += redis_res
            res = filter(None, res)

            if res:
                self.local_cache.mset([(r[self._key_name], r) for r in res])

        res += local_res

        # for debug
        if not res:
            raise gen.Return([])

        if is_multi:
            if keep_order:
                res = sorted(res, key=lambda x: mongo_key_list.index(x[self._key_name]))
            raise gen.Return(res)
        else:
            raise gen.Return(res[0])

class RedisDelegate(object):
    """docstring for RedisDelegate"""
    def __init__(self, redis_conn=None, sync_db=None):
        if redis_conn:
            self.conn = redis_conn
        else:
            self.conn = RedisHandler(RedisHandler.type_lru)

        if sync_db:
            self.mongo_conn = sync_db
        else:
            self.mongo_conn = mongoclient.fbt

        self.col_name_list = list()

    def set_redis_conn(self, redis_conn):
        self.conn = redis_conn

    def set_mongo(self, sync_db):
        self.mongo_conn = sync_db

    def init_from_mongodb(self):
        pass

    def add_collection(self, collection, col_name=None):
        if col_name:
            assert (isinstance(col_name, str) and 1 == len(col_name.split()))
        else:
            col_name = collection._col_name or collection.__class__.__name__

        if hasattr(self, col_name):
            raise AttributeError, col_name + 'already exists'

        collection.set_redis_delegate(self)
        self.__dict__[col_name] = collection
        self.col_name_list.append(col_name)

    def parse_sub_key_name(self, sub_key_name):
        col_name, others = sub_key_name.split(':', 2)
        others = others.split('.', 2)
        if 2 == len(others):
            key, field_name = others
        else:
            key = others[0]
            field_name = ""
        key = getattr(self, col_name)._key_type(key)
        return col_name, key, field_name

    @gen.coroutine
    def try_write_back(self, conn, key_name):
        pipe = conn.pipeline()
        identifier = str(uuid.uuid4())
        lockname = make_lockname(key_name)
        isSuccess = yield conn.setnx(lockname, identifier)
        if isSuccess:
            try:
                yield pipe.watch(lockname)
                pre_identifier = yield pipe.get(lockname)
                ismember = yield pipe.sismember(KEYS_MODIFIED_SET, key_name)

                # the lock isn't modified by other clients, otherwise just ignore it
                if pre_identifier != identifier:
                    yield pipe.unwatch()
                    raise gen.Return(False)
                else:
                    if ismember:
                        col_name, key, field_name = self.parse_sub_key_name(key_name)
                        yield getattr(self, col_name).write_back(key, field_name)
                        ##print "write_back", key_name

                    pipe.multi()
                    pipe.delete(key_name)
                    if ismember:
                        pipe.srem(KEYS_MODIFIED_SET, key_name)
                    pipe.zrem(LRU_QUEUE, key_name)
                    pipe.delete(lockname)
                    yield pipe.execute()
                    raise gen.Return(True)
            except redis.exceptions.WatchError:
                raise gen.Return(False)
    # scheduler_dict for example {time: col_name_list[when empty, means all!]}
    # time such as 3:10
    @gen.coroutine
    def check_overload(self, interval=5, scheduler_dict=None):
        from datetime import date, datetime, time as nomal_time

        scheduler_list = list()
        last_write_all_back_day = date.today()  # date(1970, 1, 1)
        # the keys we want to write back when writing all back but are using
        left_key_list = list()
        scheduler_list_index = 0

        if scheduler_dict:
            for k, v in scheduler_dict.iteritems():
                sche_time = map(int, k.split(':'))
                sche_time = nomal_time(*sche_time)
                scheduler_list.append((sche_time, v))
            scheduler_list = sorted(scheduler_list, key=lambda x: x[0])

        half_interval = interval / 2
        while True:
            conn = self.conn
            now = datetime.now().time()
            if scheduler_list and last_write_all_back_day < date.today() and now >= scheduler_list[scheduler_list_index][0]:
                col_name_list = scheduler_list[scheduler_list_index][1]
                to_be_writeback_list = yield conn.zrange(LRU_QUEUE, len(left_key_list), EVERY_ZRANGE_NUM + len(left_key_list))
                while to_be_writeback_list:
                    '''
                    for key_name in to_be_writeback_list:
                        if key_name.split(':', 1)[0] in col_name_list:
                            isSuccess = yield self.try_write_back(conn, key_name)
                            if not isSuccess:
                                left_key_list.append(key_name)
                    '''
                    writeback_list = list()
                    yield_list = list()
                    for key_name in to_be_writeback_list:
                        if key_name.split(':', 1)[0] in col_name_list:
                            writeback_list.append(key_name)
                            yield_list.append(self.try_write_back(conn, key_name))
                    if yield_list:
                        res_list = yield yield_list
                        for r, k in izip(res_list, writeback_list):
                            if not r:
                                left_key_list.append(k)

                    to_be_writeback_list = yield conn.zrange(LRU_QUEUE, len(left_key_list), EVERY_ZRANGE_NUM + len(left_key_list))
                    scheduler_list_index += 1
                    if scheduler_list_index == len(scheduler_list):
                        scheduler_list_index = 0
                        last_write_all_back_day = date.today()

            # try left_key_list again
            if left_key_list:
                for i, key_name in enumerate(left_key_list):
                    isSuccess = yield self.try_write_back(conn, key_name)
                    if isSuccess:
                        del left_key_list[i]

            num = yield conn.zcard(LRU_QUEUE)
            if num >= LRU_QUEUE_NUM_MAX:
                rm_num = num - LRU_QUEUE_NUM_MIN
                to_be_writeback_list = yield conn.zrange(LRU_QUEUE, 0, rm_num)
                yield [self.try_write_back(conn, key_name) for key_name in to_be_writeback_list]
            elif num >= LRU_QUEUE_NUM_MIN:
                # because in a single thread, the ioloop is not the same one as web server, sleep is OK
                time.sleep(half_interval)
            else:
                time.sleep(interval)
        #self.turn_off_already_in_redis()

class CoinsOfUser(CollectionBase):
    """
    uid
    
    coins_of_ystday
    total_coins

    public_download_queue
    """
    _key_name = 'uid'
    _key_type = long
    _col_name = "coins_of_user"
    _none_string_key_name_dict = {_key_name: long, "total_coins": float, "coins_of_ystday": float}
    public_download_queue = SetField('public_download_queue', NumberField(long))

class StaticAllResources(StaticCollectionBase):
    _key_name = 'file_id'
    _key_type = str
    _col_name = "all_resources"
    _sort_field_names_dict = {'mtime': long, 'download_num': int}

class AllResources(CollectionBase):
    _key_name = 'file_id'
    _key_type = str
    _col_name = "all_resources"
    """
    "download_num_day" and "hot_day" in hot are seprate into two key
    _none_string_key_name_dict = {_key_name: str, 'main_type': int, 'sub_type': int, 
                                     'file_size': int, 'public': int, 'mtime': long,
                                     'download_num_day': int, 'hot_day': int, 'sticky': int,
                                     'hidden': int, 'tobeaudit': int, 'download_num': int}
    This time just ignore them
    """
    #_ignore_field_names = ['hot']
    _none_string_key_name_dict = {_key_name: str, 'main_type': int, 'sub_type': int, 
                                 'file_size': int, 'public': int, 'mtime': long,'sticky': int, 'hidden': int,
                                 'tobeaudit': int, 'download_num': int, 'reward': int}
    tags = SetField('tags')
    comments = ListField('comments', DictField())
    scores = ListField('scores', DictField())
    exp_info = ListField('exp_info', DictField()) # one item in the list
    owners = ZsetField('owners', 'uid', long, 'is_public', int)
    file_ids = SetField('file_ids')
    hot = ListField('hot', DictField())

class DirResources(CollectionBase):
    _key_name = 'file_id'
    _key_type = str
    _col_name = "dir_resources"
    _none_string_key_name_dict = {_key_name: str, 'file_size': int, 'public': int, 'download_num': int}
    owner = ZsetField('owners', 'uid', long, 'is_public', int)

class ResourcesOfUser(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = "resources_of_user"
    _none_string_key_name_dict = {_key_name: long}
    file_ids = SetField('file_ids')

class Tags(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = "tags"
    _none_string_key_name_dict = {_key_name: long}
    file_ids = SetField('file_ids')

class Fblog(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = 'fblog'
    _none_string_key_name_dict = {_key_name: long, "online_time": float}
    log = ListField('log', DictField())

class Users(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = 'users'
    _none_string_key_name_dict = {_key_name: long, "haslog": int}
    # deprecate     "nick_name", "user" in friends list
    friends = ZsetField('friends', 'uid', long, 'isStar', int)
        
def main():
    '''
    coins_of_user = CoinsOfUser()
    all_resources = AllResources()
    redis_delegator.add_collection(coins_of_user)
    redis_delegator.add_collection(all_resources)
    '''

    try:
        opts, args = getopt.getopt(sys.argv[1:], "id", ["init", "debug"])
    except getopt.GetoptError as err:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)

    #for o, a in opts:
    options =[_[0] for _ in opts]
    if "-d" in options or "--debug" in options:
        from pymongo import MongoClient
        sync_db = MongoClient('localhost', 27017).fbt
        redis_conn = redis.StrictRedis()
        redis_delegator = RedisDelegate(redis_conn, sync_db)
    else:
        redis_delegator = RedisDelegate()

    fblog = Fblog()
    redis_delegator.add_collection(fblog)

    if "-i" in options or "--init" in options:
        redis_delegator.init_from_mongodb()
        sys.exit()

    func = partial(redis_delegator.check_overload, 100, {"3:30": ['fblog']})
    ioloop.IOLoop.instance().run_sync(func)

if __name__ == "__main__":
    main()
