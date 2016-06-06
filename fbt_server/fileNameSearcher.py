#!/usr/bin/env python
# -*- coding: utf-8 -*-

import jieba
import uuid
import operator
import heapq
import sys
import getopt
from tornado import gen
import codecs
import mongoclient
import motorclient
from time import time
from collections import defaultdict
from redis_handler import RedisHandler
from redis_async_lru_scheduler import RedisDelegate, StaticAllResources, Users, ResourcesOfUser, EXPIRE_TIME
from async_redis.asyncRedis import AsyncStrictRedis
from util import getFriendsById
from constant import USER_IP_CACHE_SET_KEY

'''
mode = 'test'
if mode:
    REDIS_MASTER_HOST = 'localhost'
    REDIS_PORT = [0, 0, 6379]
    REDIS_PWD = [None, None, None]
else:
    from constant import REDIS_MASTER_HOST, REDIS_PORT, REDIS_PWD
'''

__author__ = 'spark'

'''
before searching, run this script to create index on redis, and this redis MUST be a single db!
In redis:
    stop_keyword_list [set] : file frequence of keys which is more than STOP_KEYWORD_FREQUENCE
    k1 [key_name: key:k1] [set] : [file_id1, file_id2,...]
    k2...

In mongoDB:
    key_fileids : {'key': k, 'file_ids': list()}
    all_resources : resource in all_resources DB such as
    {
        file_name: xxx,
        main_type: 0~5, #see ResourceType
        sub_type: 0~3,
        file_size: 1234,
        mtime: 2014-3-4,
        tags: [tag1,tag2,...]
        owners: [{uid:uid1, is_public: 1},...]  # used as set
        grades: [{uid:uid1, score: grade1},...]
        ...
    },
    resources_of_user : a resource in resources_of_user DB such as
    {uid : uid1, file_ids : [file_id1, file_2, ...]}    # file_ids used as set
    users :
    {
        uid : uid1,
        friends : [
            {
                nick_name : nk,
                user : e-mail,
                isStar : 0,
                uid : uid2
            },...
        ]
        ...
    }
'''

# the port of redis
#PORT = 7777
MEM_LIMIT = 1 * 1024 * 1024 * 1024
#MEM_LIMIT = 2 * 1024 * 1024
STOP_KEYWORD_FREQUENCE = 1000
#searchRedisPassWd = '123-fbt-res-search-!@#'

class Singleton(object) :
    def __new__(cls, *args, **kw) :
        if not hasattr(cls, '_instance') :
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance

def make_key_for_keyword(key):
    return ':'.join(['key', key])

def make_key_for_global_search():
    uid = str(uuid.uuid4())
    return ':'.join(['res', uid])

def make_key_for_private_search():
    uid = str(uuid.uuid4())
    return ':'.join(['pres', uid])

def make_key_for_friend_type_list(uid, _type):
    return "fft:{0}.{1}".format(_type, uid)

def make_key_for_friend_fileids(uid):
    return "ff:{0}".format(uid)

def make_key_for_all_type_list(uid, _type):
    return "aft:{0}.{1}".format(_type, uid)

class FileNameSearcher(Singleton) :
    def __init__(self, analyzer = jieba.cut_for_search) :
        self.mongoDB = mongoclient.fbt
        self.motorDB = motorclient.fbt
        self.db = RedisHandler(RedisHandler.type_search) #redis.Redis(host='127.0.0.1', port=PORT, db =0, password = searchRedisPassWd)
        #self.adb = AsyncStrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[2], password=REDIS_PWD[2])
        # for mock
        self.db.init()
        connection_kwargs = self.db.redis_client(RedisHandler.type_search, 'master').connection_pool.connection_kwargs
        self.adb = AsyncStrictRedis(host=connection_kwargs.get('host', 'localhost'), port=connection_kwargs.get('port', 6379), 
                                                        password=connection_kwargs.get('password', None))
        self.redis_delegator = RedisDelegate(self.adb, self.motorDB)
        #users = Users(expire=EXPIRE_TIME)
        all_resources = StaticAllResources(expire=EXPIRE_TIME)
        resource_of_user = ResourcesOfUser(expire=EXPIRE_TIME)
        #self.redis_delegator.add_collection(users)
        self.redis_delegator.add_collection(all_resources)
        self.redis_delegator.add_collection(resource_of_user)
        # async
        self.pipeline = self.adb.pipeline()

        # just for cache, at most time, may be for the same user
        self.global_search_key_res_dict = dict()
        self.private_search_key_res_dict = dict()
        self.search_key_heapq = list()

        # cache for friend type list
        # friend_type_dict: (uid, type): fild_id list
        '''
        self.friend_type_dict = dict()
        self.friend_type_heapq = list()
        '''

        # sync
        self.pipe = self.db.pipeline()
        self.analyzer = analyzer
        self.key_fileidSetDict = dict()

    '''
    def get_friend_type_file_ids(self, uid, tp):
        info = (uid, tp)
        res = self.friend_type_dict.get(info, None)
        if res is not None:
            for i, v in enumerate(self.friend_type_heapq):
                if info == v[1]:
                    self.friend_type_heapq[i][0] = time()
                    heapq.heapify(self.friend_type_heapq)
                    break

        while self.friend_type_heapq and self.friend_type_heapq[0][0] + EXPIRE_TIME < time():
            _time, _info = heapq.heappop(self.friend_type_heapq)
            self.friend_type_dict.pop(_info)

        return res

    def put_friend_type_file_ids(self, uid, tp, file_ids_set):
        info = (uid, tp)
        if info in self.friend_type_dict:
            for i, v in enumerate(self.friend_type_heapq):
                if info == v[1]:
                    self.friend_type_heapq[i][0] = time()
                    heapq.heapify(self.friend_type_heapq)
                    break
        else:
            heapq.heappush(self.friend_type_heapq, [time(), info])

        self.friend_type_dict[info] = file_ids_set
    '''

    def get_search_key(self, info):
        if isinstance(info[0], tuple):
            search_key_res_dict = self.private_search_key_res_dict
        else:
            search_key_res_dict = self.global_search_key_res_dict

        res = search_key_res_dict.get(info, None)
        if res is not None:
            for i, v in enumerate(self.search_key_heapq):
                if info == v[1]:
                    self.search_key_heapq[i][0] = time()
                    heapq.heapify(self.search_key_heapq)
                    break

        while self.search_key_heapq and self.search_key_heapq[0][0] + EXPIRE_TIME < time():
            _time, _info = heapq.heappop(self.search_key_heapq)
            search_key_res_dict.pop(_info)

        return res

    def put_search_key(self, info, key):
        if isinstance(info[0], tuple):
            search_key_res_dict = self.private_search_key_res_dict
        else:
            search_key_res_dict = self.global_search_key_res_dict

        if info in search_key_res_dict:
            for i, v in enumerate(self.search_key_heapq):
                if info == v[1]:
                    self.search_key_heapq[i][0] = time()
                    heapq.heapify(self.search_key_heapq)
                    break
        else:
            heapq.heappush(self.search_key_heapq, [time(), info])

        search_key_res_dict[info] = key

    def flush(self):
        ''' executes the pipeline, returns a list of results '''
        return self.pipe.execute()
    
    def drop(self):
        ''' drops the entire index '''
        return self.db.flushdb()

    @gen.coroutine
    def check_exists(self, key, expire=EXPIRE_TIME):
        is_exists = yield self.adb.expire(key, expire)
        raise gen.Return(is_exists)

    @gen.coroutine
    def check_multi_exists(self, key_list, expire=EXPIRE_TIME):
        for key in key_list:
            self.pipeline.expire(key, expire)
        res = yield self.pipeline.execute()
        raise gen.Return(res)

    def getKeys(self, file_name) :
        return set(filter( lambda x : len(x) > 1 or (u'\u4e00' <= x <= u'\u9fff'), self.analyzer(file_name.lower()) ))

    '''
    functions ending with '_sync' are just for pub_sub
    '''
    def file_id_add_title_sync(self, file_id, file_name) :
        keys = self.getKeys(file_name)
        for k in keys :
            if not self.db.sismember('stop_keyword_list', k) :
                key_name = make_key_for_keyword(k)
                self.db.sadd(key_name, file_id)
                self.mongoDB.key_fileids.update({"key": k}, {"$addToSet": {"file_ids": file_id}}, True)
                if self.db.scard(key_name) > STOP_KEYWORD_FREQUENCE :
                    self.db.sadd('stop_keyword_list', k)
                    self.db.delete(key_name)

    def remove_file_id_sync(self, file_id, file_name)  :
        keys = self.getKeys(file_name)
        for k in keys:
            key_name = make_key_for_keyword(k)
            self.pipe.srem(key_name, file_id)
            self.mongoDB.key_fileids.update({"key": k}, {"$pull": {"file_ids": file_id}}, True)
        self.flush()

    @gen.coroutine
    def file_id_add_title(self, file_id, file_name):
        pipeline = self.pipeline
        adb = self.adb
        keys = self.getKeys(file_name)
        key_list = list()
        for k in keys :
            ismembers = yield adb.sismember('stop_keyword_list', k)
            if not ismembers:
                key_name = make_key_for_keyword(k)
                key_list.append(k)
                pipeline.sadd(key_name, file_id)
                yield self.motorDB.key_fileids.update({"key": k}, {"$addToSet": {"file_ids": file_id}}, True)
        yield pipeline.execute()
        for key in key_list:
            key_name = make_key_for_keyword(k)
            pipeline.scard(key_name)
        scard_list = yield pipeline.execute()
        for card, k in zip(scard_list, key_list):
            if card > STOP_KEYWORD_FREQUENCE:
                key_name = make_key_for_keyword(k)
                pipeline.sadd('stop_keyword_list', k)
                pipeline.delete(key_name)
        yield pipeline.execute()

    @gen.coroutine
    def remove_file_id(self, file_id, file_name)  :
        keys = self.getKeys(file_name)
        pipeline = self.pipeline
        to_yield = list()
        for k in keys:
            key_name = make_key_for_keyword(k)
            pipeline.srem(key_name, file_id)
            y = self.motorDB.key_fileids.update({"key": k}, {"$pull": {"file_ids": file_id}}, True)
            to_yield.append(y)
        to_yield.append(pipeline.execute())
        yield to_yield

    # def file_id_add_title_from_init(self, pymongoDB, file_id, file_name) :
    #     keys = self.getKeys(file_name)
    #     flag = self.db.info()['used_memory']  < MEM_LIMIT
    #     for k in keys :
    #         if not self.db.sismember('stop_keyword_list', k) :
    #             res = pymongoDB.key_fileids.find_and_modify(query={'key': k}, update= {"$addToSet": {"file_ids": file_id}}, upsert=True, full_response= True)
    #             if res and res['value'] and ('file_ids' in res['value']) and (len(res['value']['file_ids']) > STOP_KEYWORD_FREQUENCE) :
    #                 self.db.sadd('stop_keyword_list', k)
    #                 self.db.delete(k)
    #             if flag :
    #                 self.pipe.sadd(k, file_id)
    #             else :
    #                 self.db.delete(k)
    #     if flag :
    #         self.flush()

    def file_id_add_title_from_init(self, file_id, file_name) :
        keys = self.getKeys(file_name)
        for k in keys :
            if k not in self.key_fileidSetDict :
                self.key_fileidSetDict[k] = set([file_id])
            else :
                self.key_fileidSetDict[k].add(file_id)

    def init_index_in_redis(self, pymongoDB) :
        for k, v in self.key_fileidSetDict.iteritems() :
            if len(v) <= STOP_KEYWORD_FREQUENCE :
                if self.db.info()['used_memory']  < MEM_LIMIT :
                    key_name = make_key_for_keyword(k)
                    self.db.sadd(key_name, *v)
                    #for f in v :
                    #    self.db.sadd(k, f)
                pymongoDB.key_fileids.insert({'key': k, 'file_ids': list(v)})
            else :
                self.db.sadd('stop_keyword_list', k)

    @gen.coroutine
    def query_file_ids_by_file_name(self, file_name, page, max_resources_cnt_in_page, sort=None, desc=True):
        keys = tuple(self.getKeys(file_name))
        rd = self.redis_delegator
        global_search_key  = yield self._query_file_ids_by_file_name(keys)
        file_ids = yield self.adb.smembers(global_search_key)
        if sort:
            # sort all, TODO: check sufficiency
            yield rd.all_resources.find(file_ids)
            file_ids = yield self.sort(global_search_key, sort, None, None, desc)
        ret = list()
        size = len(file_ids)
        index = 0
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        for file_id in file_ids:
            resource = yield rd.all_resources.find(file_id)
            if resource and (1 != resource.get("hidden", None)) and (1 == resource.get("public", None)):
                if end_index == index:
                    break
                elif index >= start_index:
                    resource['file_id'] = file_id
                    ret.append(resource)
                index += 1
        raise gen.Return((size, ret))

    @gen.coroutine
    def query_file_ids_by_file_name_private(self, my_uid, file_name, page, max_resources_cnt_in_page, sort=None, desc=True) :
        keys = tuple(self.getKeys(file_name))
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        rd = self.redis_delegator
        adb = self.adb

        private_search_key = self.get_search_key((keys, my_uid))
        is_exists = False
        if private_search_key:
            is_exists = yield self.check_exists(private_search_key)
        if not is_exists:
            global_search_key  = yield self._query_file_ids_by_file_name(keys)
            friend_fileids_set_key = make_key_for_friend_fileids(my_uid)
            is_exists = yield self.check_exists(friend_fileids_set_key)
            #res = yield adb.smembers(global_search_key)
            #print res
            # Becouse empty is not so likely, it has a good chance of epiration
            if not is_exists:
                res = yield self.load_private_resources(my_uid)
            #res = yield adb.smembers(friend_fileids_set_key)
            #print res
            private_search_key = make_key_for_private_search()
            size = yield adb.sinterstore(private_search_key, global_search_key, friend_fileids_set_key)
            yield adb.expire(private_search_key, EXPIRE_TIME)
            res =  yield self.adb.smembers(private_search_key)
        else:
            size = yield adb.scard(private_search_key)

        if sort:
            file_ids = yield self.sort(private_search_key, sort, start_index, max_resources_cnt_in_page, desc)
        else:
            file_ids = yield self.adb.smembers(private_search_key)
            file_ids = list(file_ids)
            file_ids = file_ids[start_index: end_index]

        ret = yield rd.all_resources.find(file_ids, keep_order=bool(sort))
        self.put_search_key((keys, my_uid), private_search_key)
        raise gen.Return((size, ret))

    @gen.coroutine
    def _query_file_ids_by_file_name(self, keys) :
        ukey = make_key_for_global_search()
        if not keys:
            raise gen.Return(ukey)
        global_search_key = self.get_search_key(keys)
        if global_search_key:
            is_exists = yield self.check_exists(global_search_key)
            if is_exists:
                #res = yield self.adb.smembers(global_search_key)
                raise gen.Return(global_search_key)

        pipeline = self.pipeline
        if not keys :
            raise gen.Return([])

        key_list = list()
        for k in keys :
            ismembers = yield self.adb.sismember('stop_keyword_list', k)
            if not ismembers:
                key_name = make_key_for_keyword(k)
                key_list.append(key_name)
                is_exists = yield self.adb.exists(key_name)
                if not is_exists :
                    res = yield self.motorDB.key_fileids.find_one({'key': k}, {'file_ids': 1, '_id' : 0})
                    if res :
                        '''
                        try:
                            print 'HIT: ', k
                        except Exception, e:
                            print e
                        '''
                        pipeline.sadd(key_name, *res['file_ids'])

        pipeline.sinterstore(ukey, *key_list)
        #pipeline.smembers(ukey)
        pipeline.expire(ukey, EXPIRE_TIME)
        res = yield pipeline.execute()
        self.put_search_key(keys, ukey)
        raise gen.Return(ukey)

    @gen.coroutine
    def sort(self, key, sort, start=0, num=20, desc=True):
        alpha = sort not in ('mtime', 'download_num')
        by = "all_resources:*->" + sort
        res = yield self.adb.sort(key, by=by, alpha=alpha,desc=desc, start=start, num=num)
        raise gen.Return(res)

    @gen.coroutine
    def get_private_resources_by_type(self, my_uid, _type, page, max_resources_cnt_in_page, sort=None, desc=True):
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        rd = self.redis_delegator
        size = yield self.load_private_resources(my_uid, _type)
        if 0 == size:
            raise gen.Return((0, []))
        friend_type_key = make_key_for_all_type_list(my_uid, _type)
        if sort:
            res = yield self.sort(friend_type_key, sort, start_index, max_resources_cnt_in_page, desc)
        else:
            res = yield self.adb.smembers(friend_type_key)
            res = list(res)
            res = res[start_index: end_index]

        ret = yield rd.all_resources.find(res, keep_order=bool(sort))
        raise gen.Return((size, ret))

    @gen.coroutine
    def get_private_resources(self, my_uid, page, max_resources_cnt_in_page, sort=None, desc=True):
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        rd = self.redis_delegator
        file_ids = yield self.load_private_resources(my_uid)
        size = len(file_ids)
        if sort:
            friend_fileids_set_key = make_key_for_friend_fileids(my_uid)
            file_ids = yield self.sort(friend_fileids_set_key, sort, start_index, max_resources_cnt_in_page, desc)
        else:
            file_ids = file_ids[start_index: end_index]

        ret = yield rd.all_resources.find(file_ids, keep_order=bool(sort))
        raise gen.Return((size, ret))

    @gen.coroutine
    def get_online_friends(self, my_uid):
        pipeline = self.pipeline
        online_friends_key = ':'.join(['my_friends', str(my_uid)])
        is_exists = yield self.check_exists(online_friends_key)
        if not is_exists:
            friend_uid_list = yield getFriendsById(my_uid)
            if friend_uid_list:
                pipeline.sadd(online_friends_key, *[_['uid'] for _ in friend_uid_list])
                pipeline.expire(online_friends_key, EXPIRE_TIME)
                yield pipeline.execute()
        online_friends_uid_list = yield self.adb.sinter(online_friends_key, USER_IP_CACHE_SET_KEY)
        online_friends_uid_list = [long(_) for _ in online_friends_uid_list]
        raise gen.Return(online_friends_uid_list)

    @gen.coroutine
    def load_private_resources_helper(self, my_uid, tp=None):
        pipeline = self.pipeline
        rd = self.redis_delegator
        my_type_resource_set = set()
        my_resource_set = set()
        friend_uid_list = yield self.get_online_friends(my_uid)# yield getFriendsById(my_uid)
        for uid in friend_uid_list:
            assert uid > 0
            friend_resource = yield rd.resources_of_user(uid).file_ids.get()
            if friend_resource:
                file_in_dir = {}
                fileids_of_one_friend = set()
                for f in friend_resource:
                    if '+' in f:
                        dir_id, file_id = f.split('+')
                        if dir_id in file_in_dir:
                            file_in_dir[dir_id].append(file_id)
                        else:
                            file_in_dir[dir_id] = [file_id]
                    else:
                        fileids_of_one_friend.add(f)
                if file_in_dir:
                    fileids_of_one_friend = fileids_of_one_friend.union(file_in_dir.keys())
                if fileids_of_one_friend:
                    #res = yield [rd.all_resources.find(_) for _ in fileids_of_one_friend]
                    key_fileids_dict = defaultdict(list)
                    #for r, file_id in zip(res, fileids_of_one_friend):
                    resources = yield rd.all_resources.find(fileids_of_one_friend)
                    for r in resources:
                        if r and 'main_type' in r:
                            _type = r['main_type']
                            file_id = r['file_id']
                            key_fileids_dict[_type].append(file_id)
                    for _type, fileids in key_fileids_dict.iteritems():
                        one_friend_type_key = make_key_for_friend_type_list(uid, _type)
                        is_exists = yield self.check_exists(one_friend_type_key)
                        # write when expire
                        if not is_exists:
                            pipeline.sadd(one_friend_type_key, *fileids)
                            pipeline.expire(one_friend_type_key, EXPIRE_TIME)
                        if _type == tp:
                            my_type_resource_set = my_type_resource_set.union(fileids)
                    yield pipeline.execute()
                my_resource_set = my_resource_set.union(fileids_of_one_friend)

        if my_resource_set:
            friend_fileids_set_key = make_key_for_friend_fileids(my_uid)
            pipeline.sadd(friend_fileids_set_key, *my_resource_set)
            pipeline.expire(friend_fileids_set_key, EXPIRE_TIME)
            yield pipeline.execute()
        if my_type_resource_set:
            friend_type_key = make_key_for_all_type_list(my_uid, tp)
            pipeline.sadd(friend_type_key, *my_type_resource_set)
            pipeline.expire(friend_type_key, EXPIRE_TIME)
            yield pipeline.execute()
        if tp:
            raise gen.Return(my_type_resource_set)
        else:
            raise gen.Return(my_resource_set)

    @gen.coroutine
    def load_private_resources(self, my_uid, tp=None):
        adb = self.adb
        #friend_uid_list = yield rd.users(my_uid).friends.get()

        if tp is None:
            friend_fileids_set_key = make_key_for_friend_fileids(my_uid)
            is_exists = yield self.check_exists(friend_fileids_set_key)
            if is_exists:
                my_resource_set = yield adb.smembers(friend_fileids_set_key)
                raise gen.Return(list(my_resource_set))
            else:
                res = yield self.load_private_resources_helper(my_uid, tp)
                raise gen.Return(list(res))
        else:
            friend_type_key = make_key_for_all_type_list(my_uid, tp)
            is_exists = yield self.check_exists(friend_type_key)
            if is_exists:
                size = yield self.adb.scard(friend_type_key)
                raise gen.Return(size)
            else:
                friend_uid_list = yield self.get_online_friends(my_uid) # yield getFriendsById(my_uid)
                if 0 == len(friend_uid_list):
                    raise gen.Return(0)
                else:
                    exists_list = yield self.check_multi_exists([make_key_for_friend_type_list(_, tp) for _ in friend_uid_list])
                    if any(exists_list):
                        size = yield self.adb.sunionstore(friend_type_key, *[make_key_for_friend_type_list(_, tp) for _ in friend_uid_list])
                        raise gen.Return(size)
                    else:
                        res = yield self.load_private_resources_helper(my_uid, tp)
                        raise gen.Return(len(res))

    def init_from_mongo(self):
        db = mongoclient.fbt
        with codecs.open('fn', 'w','utf-8') as f :
            for record in db.all_resources.find({"hidden": {"$ne": 1}, "public": 1}, {'file_id': 1, 'file_name': 1, '_id': 0}) :
                if 'file_id' in record and 'file_name' in record :
                    self.file_id_add_title_from_init(record['file_id'], record['file_name'])
                    f.write("%s\t%s\n" % (record['file_id'], record['file_name']))
        self.init_index_in_redis(db)
        db.key_fileids.create_index('key', background=True)

    def add_index_in_redis(self, pymongoDB) :
        pipeline = self.pipe
        rdb = self.db
        key_list = list()
        for k, v in self.key_fileidSetDict.iteritems() :
            ismembers = rdb.sismember('stop_keyword_list', k)
            if not ismembers:
                if self.db.info()['used_memory']  < MEM_LIMIT:
                    key_list.append(k)
                    key_name = make_key_for_keyword(k)
                    pipeline.sadd(key_name, *v)
            self.mongoDB.key_fileids.update({"key": k}, {"$addToSet": {"file_ids": {"$each" : list(v)}}}, True)
        for key in key_list:
            key_name = make_key_for_keyword(k)
            pipeline.scard(key_name)
        scard_list =  pipeline.execute()
        for card, k in zip(scard_list, key_list):
            if card > STOP_KEYWORD_FREQUENCE:
                key_name = make_key_for_keyword(k)
                pipeline.sadd('stop_keyword_list', k)
                pipeline.delete(key_name)
        pipeline.execute()

    def scan_from_mongo(self, last_mtime):
        db = mongoclient.fbt
        if 0 == last_mtime:
            records_list = db.all_resources.find({"hidden": {"$ne": 1}, "public": 1}, {'file_id': 1, 'file_name': 1, 'mtime': 1, '_id': 0})
        else:
            records_list = db.all_resources.find({"hidden": {"$ne": 1}, "public": 1, 'mtime': {"$gt": last_mtime}}, {'file_id': 1, 'file_name': 1, 'mtime': 1, '_id': 0})

        for record in records_list:
            if 'file_id' in record and 'file_name' in record :
                self.file_id_add_title_from_init(record['file_id'], record['file_name'])
                if 'mtime' in record:
                    last_mtime = max(last_mtime, record['mtime'])
        self.add_index_in_redis(db)
        return last_mtime

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "is", ["init", "scan"])
    except getopt.GetoptError as err:
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)
    
    options =[_[0] for _ in opts]
    searcher = FileNameSearcher()
    if "-i" in options or "--init" in options:
        searcher.drop()
        searcher.init_from_mongo()
    else:
        """
        last_mtime = 0
        last_mtime_filename = 'last_mtime'
        import os
        last_mtime_filename = os.path.join(os.path.dirname(sys.argv[0]), last_mtime_filename)
        if os.path.exists(last_mtime_filename):
            with open(last_mtime_filename, 'r') as f:
                last_mtime = long(f.read().strip())
        last_mtime = searcher.scan_from_mongo(last_mtime)
        with open(last_mtime_filename, 'w') as out:
            out.write(str(last_mtime))
        """
        searcher.scan_from_mongo(0)
