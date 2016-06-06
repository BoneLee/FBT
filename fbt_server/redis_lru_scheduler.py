#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
data structures in redis
keys_modified: set, key_names have been modified since readed from mongodb to redis
lru_queue: zset, member: key_name, score: time
"""

import redis
import getopt
import sys
import time
import uuid
import json
from bson import json_util
from functools import partial
from copy import deepcopy

from redis_handler import RedisHandler
import mongoclient

__author__ = 'spark'

KEYS_MODIFIED_SET = 'keys_modified'
LRU_QUEUE = 'lru_queue'
LRU_QUEUE_NUM_MIN = 10000
LRU_QUEUE_NUM_MAX = 15000
EVERY_ZRANGE_NUM = 1000
LOCK_TIMEOUT = 10

def make_lockname(key_name):
    return 'lock:' + key_name

def acquire_lock_with_timeout(conn, key_name, lock_timeout=LOCK_TIMEOUT):
    """
    Tell scheduler that I will do sth with this key in LOCK_TIMEOUT seconds, so it can't write it back to mango
    """
    identifier = str(uuid.uuid4())
    lockname = make_lockname(key_name)
    conn.setex(lockname, lock_timeout, identifier)

def make_key_name(*args):
    return ':'.join(map(str, args))

def make_sub_key_name(*args):
    return '.'.join(map(str, args))

def handle_result_from_redis(is_single_value=True):
    def _handle_result_from_redis(function):
        def __handle_result_from_redis(*args, **kw):
            res = function(*args, **kw)
            self = args[0]
            
            if self.field_type:
                if is_single_value:
                    if res:
                        res = self.field_type.get(res)
                else:
                    res = [self.field_type.get(v) for v in res]
            elif not is_single_value:
                res = list(res)

            return res
        return __handle_result_from_redis
    return _handle_result_from_redis

class IndirectField(object):
    def set(self, val) :
        raise NotImplementedError()
    def get(self, val):
        raise NotImplementedError() 

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
    def __init__(self, field_name, field_type=None):
        self.field_name = field_name
        self.field_type = field_type

    def __get__(self, obj, objtype):
        self.conn = obj.redis_delegate.conn
        self.col = obj
        self.key_name = make_sub_key_name(obj._key, self.field_name)
        obj.make_data_in_redis([self.field_name])
        return self

    def __set__(self, obj, val):
        """
        only for non transitional command using =
        """
        raise NotImplementedError()

    def get_all_items(self):
        raise NotImplementedError()

    def record_modify(self):
        self.conn.sadd(KEYS_MODIFIED_SET, self.key_name)
        self.conn.zadd(LRU_QUEUE, time.time(), self.key_name)

class ZsetField(ComplexField):
    """
    docstring for ZsetField
    """
    def __init__(self, field_name, member_name, member_type, score_name, score_type):
        super(ZsetField, self).__init__(field_name)
        self.member_name = member_name
        self.member_type = member_type
        self.score_name = score_name
        self.score_type = score_type

    def __set__(self, obj, val):
        self.key_name = make_sub_key_name(obj._key, self.field_name)
        self.conn = obj.redis_delegate.conn.pipeline()

        if obj.need_record_modify():
            self.record_modify()

        self.conn.delete(self.key_name)
        if val:
            member_score_list = list()
            for v in val:
                if self.member_name in v and self.score_name in v:
                    member_score_list.append(v[self.score])
                    member_score_list.append(v[self.member_name])
                else :
                    print "Error: %s miss %s or %s" % (str(v), self.member_name, self.score_name)
            if member_score_list:
                self.conn.zadd(self.key_name, *member_score_list)
        self.conn.execute()

        # change to not transaction
        self.conn = obj.redis_delegate.conn

    def __getattr__(self, attr):
        raise AttributeError, attr + ' not allowed currently'

    def zcard(self):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return len(res)
        else :
            return self.conn.zcard(self.key_name)

    def zadd(self, *values, **kwargs):
        self.record_modify()
        return self.conn.zadd(self.key_name, *values, **kwargs)

    def zscore(self, member):
        """
        ignore _document_just_loaded_from_mongo, because zscore is more direct and easy
        """
        score = self.conn.zscore(self.key_name, member)
        if self.score_type is not float:
            score = self.score_type(score)
        return score

    def zrem(self, *values):
        self.record_modify()
        return self.conn.zrem(self.key_name, *values)

    def zrange(self, start, end):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return res[start: end]
        else:
            values = self.conn.zrange(self.key_name, start, end, withscores=True, score_cast_func=self.score_type)
            res = list()
            for v in values:
                res.append({self.member_name: self.member_type(v[0]), self.score_name: v[1]})
            return res

    def get_all_items(self):
        return self.zrange(0, -1)

class SetField(ComplexField):
    def __set__(self, obj, val):
        self.key_name = make_sub_key_name(obj._key, self.field_name)
        self.conn = obj.redis_delegate.conn.pipeline()

        if obj.need_record_modify():
            self.record_modify()

        self.conn.delete(self.key_name)
        if val:
            if self.field_type:
                val = [self.field_type.set(v) for v in val]
            self.conn.sadd(self.key_name, *val)
        self.conn.execute()

        # change to not transaction
        self.conn = obj.redis_delegate.conn

    def __getattr__(self, attr):
        raise AttributeError, attr + ' not allowed currently'

    def scard(self):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return len(res)
        else :
            return self.conn.scard(self.key_name)

    def sadd(self, *values):
        self.record_modify()
        if self.field_type:
            values = [self.field_type.set(v) for v in values]
        return self.conn.sadd(self.key_name, *values)

    def sismember(self, val):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return val in res
        else:
            if self.field_type:
                val = self.field_type.set(val)
            return self.conn.sismember(self.key_name, val)

    @handle_result_from_redis(False)
    def smembers(self):
        """
        return list!
        """
        val = self.col.get_from_just_loaded(self.field_name)
        if not val:
            val = self.conn.smembers(self.key_name)
        return val

    get_all_items = smembers

    def srem(self, *values):
        self.record_modify()

        if self.field_type:
            values = [self.field_type.set(v) for v in values]
        return self.conn.srem(self.key_name, *values)

class ListField(ComplexField):
    def __set__(self, obj, val):
        self.key_name = make_sub_key_name(obj._key, self.field_name)
        self.conn = obj.redis_delegate.conn.pipeline()
        if obj.need_record_modify():
            self.record_modify()

        self.conn.delete(self.key_name)
        if val:
            if self.field_type:
                val = [self.field_type.set(v) for v in val]
            self.conn.rpush(self.key_name, *val)
        self.conn.execute()

        self.conn = obj.redis_delegate.conn

    def __getattr__(self, name):
        if name in ['lrem', 'ltrim']:
            self.record_modify()

            return partial(self.conn.__getattr__(name), self.key_name)
        else:
            raise AttributeError, name + 'not allowed currently'

    def llen(self):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return len(res)
        else:
            return self.conn.llen(self.key_name)

    @handle_result_from_redis()
    def lindex(self, index):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            if index < len(res):
                return res[index]
            else :
                return None
        else:
            val = self.conn.lindex(self.key_name, index)
            return val

    @handle_result_from_redis()
    def lpop(self):
        self.record_modify()

        val = self.conn.lpop(self.key_name)
        return val

    def rpush(self, *values):
        self.record_modify()

        if values:
            if self.field_type:
                values = [self.field_type.set(v) for v in values]
            return self.conn.rpush(self.key_name, *values)

    @handle_result_from_redis(False)
    def lrange(self, start, end):
        res = self.col.get_from_just_loaded(self.field_name)
        if res:
            return res[start: end]
        else:
            values = self.conn.lrange(self.key_name, start, end)
            return values

    def get_all_items(self):
        return self.lrange(0, -1)

class CollectionBase(object):
    """
    Don't define vars not starting with '_' by yourself
    """
    _mongo_key = None
    _key = None
    _key_name = ""
    _key_type = None
    _col_name = ""
    _int_long_float_key_name_dict = dict()
    # just parts of one document, the key and its value are not in it!
    _document_just_loaded_from_mongo = dict()
    # just a trick for find funciton
    _is_already_in_redis = False
    # just a trick for make_data_in_redis
    _need_record_modify = True

    redis_delegate = None

    def __init__(self, key_name=None):
        if key_name:
            self._key_name = key_name

    def record_modify(self):
        if self.need_record_modify():
            self.redis_delegate.conn.sadd(KEYS_MODIFIED_SET, self._key)
            self.redis_delegate.conn.zadd(LRU_QUEUE, time.time(), self._key)

    def get_hashes_by_dict(self, hashes_dict):
        for k, v in self._int_long_float_key_name_dict.iteritems():
            if k in hashes_dict:
                hashes_dict[k] = v(hashes_dict[k])
        return hashes_dict

    def need_record_modify(self):
        return self._need_record_modify

    def turn_on_record_modify(self):
        self._need_record_modify = True

    def turn_off_record_modify(self):
        self._need_record_modify = False

    def is_already_in_redis(self):
        return self._is_already_in_redis

    def turn_on_already_in_redis(self):
        self._is_already_in_redis = True

    def turn_off_already_in_redis(self):
        self._is_already_in_redis = False

    def get_all_key_names(self):
        field_names = self.get_all_class_var_names()
        sub_key_names =  map(partial(make_sub_key_name, self._key), field_names)
        return sub_key_names, field_names

    def get_from_just_loaded(self, key_name):
        return self._document_just_loaded_from_mongo.get(key_name)

    def get_all_class_var_names(self):
        return [_ for _ in self.__class__.__dict__ if not _.startswith('_')]

    def set_redis_delegate(self, redis_delegate):
        self.redis_delegate = redis_delegate

    def __call__(self, key):
        self._mongo_key = key
        self._key = make_key_name(self._col_name, key)
        return self

    def __setattr__(self, attr, value):
        """
        set one common field with =
        """
        # thanks to http://stackoverflow.com/questions/9161302/using-both-setattr-and-descriptors-for-a-python-class
        for cls in self.__class__.__mro__ + (self, ):
            if attr in cls.__dict__:
                return object.__setattr__(self, attr, value)
        self.make_data_in_redis(need_hash=True)
        self.redis_delegate.conn.hset(self._key, attr, value)

        self.record_modify()

    def __getattr__(self, attr):
        self.make_data_in_redis(need_hash=True)
        res = self.get_from_just_loaded(attr)
        if res:
            return res
        else : # not likely!
            res = self.redis_delegate.conn.hget(self._key, attr)
            if attr in self._int_long_float_key_name_dict:
                return self._int_long_float_key_name_dict[attr](res)
            else:
                return res

    def make_data_in_redis(self, field_names=(), need_hash=False):
        '''
        self: collection_self
        if sub_key_names=None, need_hash=False, reload all data in the collection
        '''
        if self.is_already_in_redis():
            return

        self.turn_off_record_modify()

        conn = self.redis_delegate.conn
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        key_name = self._key_name

        self._document_just_loaded_from_mongo.clear()

        field_name_not_in_redis_list = list()
        all_sub_key_names, all_field_names = self.get_all_key_names()

        if not field_names and not need_hash:
            sub_key_names, field_names = all_sub_key_names, all_field_names
        else:
            sub_key_names = map(partial(make_sub_key_name, self._key), field_names)

        for sub_key_name, field_name in zip(sub_key_names, field_names):
            acquire_lock_with_timeout(conn, sub_key_name)
            
            if not conn.exists(sub_key_name):
                ##print "try_fetch:", sub_key_name
                field_name_not_in_redis_list.append(field_name)

        if need_hash:
            acquire_lock_with_timeout(conn, self._key)

            if conn.exists(self._key):
                need_hash = False
            ##else:
            ##    print "try_fetch:", self._key

        if field_name_not_in_redis_list or need_hash:
            mongo_key = self._mongo_key
            res = mongo_col.find_one({key_name: self._mongo_key}, {'_id': 0, self._key_name: 0})
            if not res:
                self.turn_on_record_modify()
                return
            
            for field_name in all_field_names:
                if field_name in res:
                    val = res.pop(field_name)
                    if field_name in field_name_not_in_redis_list:
                        self.turn_on_already_in_redis()
                        getattr(self, field_name).__set__(self, val)
                        self.turn_off_already_in_redis()
                        self._document_just_loaded_from_mongo[field_name] = val

            if need_hash:
                self._document_just_loaded_from_mongo.update(res)
                # rm empty val
                to_be_pop_list = list()
                for k, v in res.iteritems():
                    if not v:
                        to_be_pop_list.append(k)
                for k in to_be_pop_list:
                        res.pop(k)

                conn.hmset(self._key, res)

        self.turn_on_record_modify()

    def _get_all_hashes(self, key):
        res = self.redis_delegate.conn.hgetall(make_key_name(self._col_name, key))
        return self.get_hashes_by_dict(res)

    def update(self, doc_dict):
        assert (self._key_name in doc_dict)
        doc_dict = deepcopy(doc_dict)
        key = doc_dict.pop(self._key_name)
        self._key = make_key_name(self._col_name, key)
        self._mongo_key = key

        for field_name in self.get_all_class_var_names():
            if field_name in doc_dict:
                getattr(self, field_name).__set__(self, doc_dict.pop(field_name))

        if doc_dict:
            self.redis_delegate.conn.hmset(self._key, doc_dict)
            self.record_modify()

    def find(self, key, field_name_list):
        res = dict()
        common_field_name_list = list()
        complex_field_name_list = list()
        self._key = make_key_name(self._col_name, key)
        self._mongo_key = key

        all_complex_field_name = self.get_all_class_var_names()
        for field_name in field_name_list:
            if field_name in all_complex_field_name:
                complex_field_name_list.append(field_name)
            else:
                common_field_name_list.append(field_name)

        self.make_data_in_redis(complex_field_name_list, bool(common_field_name_list))
        self.turn_on_already_in_redis()
        for field_name in complex_field_name_list:
            _res = self.get_from_just_loaded(field_name)
            if _res:
                res[field_name] = _res
            else:
                res[field_name] = getattr(self, field_name).get_all_items()

        for field_name in common_field_name_list:
            _res = self.get_from_just_loaded(field_name)
            if _res:
                res[field_name] = _res
            else:
                res[field_name] = getattr(self, field_name)
        self.turn_off_already_in_redis()
        return res

    def write_back(self, key, field_name):
        mongo_col = getattr(self.redis_delegate.mongo_conn, self._col_name)
        #conn = self.redis_delegate.conn
        if field_name:
            res_list = getattr(self(key), field_name).get_all_items()
            mongo_col.update({self._key_name: key}, {"$set": {field_name: res_list}}, True)
        else:
            res_dict = self._get_all_hashes(key)
            mongo_col.update({self._key_name: key}, {"$set": res_dict}, True)

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
            assert (isinstance(col_name, str) and 0 == col_name.split())
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

    def try_write_back(self, conn, key_name):
        pipe = conn.pipeline()
        identifier = str(uuid.uuid4())
        lockname = make_lockname(key_name)
        if conn.setnx(lockname, identifier):
            try:
                pipe.watch(lockname)
                pre_identifier = pipe.get(lockname)
                ismember = pipe.sismember(KEYS_MODIFIED_SET, key_name)

                # the lock isn't modified by other clients, otherwise just ignore it
                if pre_identifier != identifier:
                    pipe.unwatch()
                    return False
                else:
                    if ismember:
                        col_name, key, field_name = self.parse_sub_key_name(key_name)
                        getattr(self, col_name).write_back(key, field_name)
                        ##print "write_back", key_name

                    pipe.multi()
                    pipe.delete(key_name)
                    if ismember:
                        pipe.srem(KEYS_MODIFIED_SET, key_name)
                    pipe.zrem(LRU_QUEUE, key_name)
                    pipe.delete(lockname)
                    pipe.execute()
                    return True
            except redis.exceptions.WatchError:
                return False
    # scheduler_dict for example {time: col_name_list[when empty, means all!]}
    # time such as 3:10
    def check_overload(self, interval=5, scheduler_dict=None):
        from datetime import date, datetime, time as nomal_time
        for col_name in self.col_name_list:
            getattr(self, col_name).turn_on_already_in_redis()

        scheduler_list = list()
        last_write_all_back_day = date(1970, 1, 1)
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
                to_be_writeback_list = conn.zrange(LRU_QUEUE, len(left_key_list), EVERY_ZRANGE_NUM + len(left_key_list))
                while to_be_writeback_list:
                    for key_name in to_be_writeback_list:
                        if key_name.split(':', 1)[0] in col_name_list:
                            isSuccess = self.try_write_back(conn, key_name)
                            if not isSuccess:
                                left_key_list.append(key_name)
                    to_be_writeback_list = conn.zrange(LRU_QUEUE, len(left_key_list), EVERY_ZRANGE_NUM + len(left_key_list))
                    scheduler_list_index += 1
                    if scheduler_list_index == len(scheduler_list):
                        scheduler_list_index = 0
                        last_write_all_back_day = date.today()

            # try left_key_list again
            if left_key_list:
                for i, key_name in enumerate(left_key_list):
                    isSuccess = self.try_write_back(conn, key_name)
                    if isSuccess:
                        del left_key_list[i]

            num = conn.zcard(LRU_QUEUE)
            if num >= LRU_QUEUE_NUM_MAX:
                rm_num = num - LRU_QUEUE_NUM_MIN
                to_be_writeback_list = conn.zrange(LRU_QUEUE, 0, rm_num)
                for key_name in to_be_writeback_list:
                    self.try_write_back(conn, key_name)
            elif num >= LRU_QUEUE_NUM_MIN:
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
    _int_long_float_key_name_dict = {_key_name: long, "total_coins": float, "coins_of_ystday": float}
    public_download_queue = SetField('public_download_queue', NumberField(long))

class AllResources(CollectionBase):
    _key_name = 'file_id'
    _key_type = str
    _col_name = "all_resources"
    """
    "download_num_day" and "hot_day" in hot are seprate into two key
    """
    _int_long_float_key_name_dict = {_key_name: str, 'main_type': int, 'sub_type': int, 
                                     'file_size': int, 'public': int, 'mtime': long,
                                     'download_num_day': int, 'hot_day': int, 'sticky': int,
                                     'hidden': int, 'tobeaudit': int, 'download_num': int}
    tags = SetField('tags')
    comments = ListField('comments', DictField())
    scores = ListField('scores', DictField())
    exp_info = ListField('exp_info', DictField()) # one item in the list
    owners = ZsetField('owners', 'uid', long, 'is_public', int)
    file_ids = SetField('file_ids')

class DirResources(CollectionBase):
    _key_name = 'file_id'
    _key_type = str
    _col_name = "dir_resources"
    _int_long_float_key_name_dict = {_key_name: str, 'file_size': int, 'public': int, 'download_num': int}
    owners = ZsetField('owners', 'uid', long, 'is_public', int)

class ResourcesOfUser(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = "resources_of_user"
    _int_long_float_key_name_dict = {_key_name: long}
    file_ids = SetField('file_ids')

class Tags(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = "tags"
    _int_long_float_key_name_dict = {_key_name: long}
    file_ids = SetField('file_ids')

class Fblog(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = 'fblog'
    _int_long_float_key_name_dict = {_key_name: long, "online_time": float}
    log = ListField('log', DictField())

class Users(CollectionBase):
    _key_name = 'uid'
    _key_type = long
    _col_name = 'users'
    _int_long_float_key_name_dict = {_key_name: long, "haslog": int}
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
        import redis
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

    redis_delegator.check_overload(100, {"3:30": ['fblog']})

if __name__ == "__main__":
    main()