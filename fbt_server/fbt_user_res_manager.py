# -*- coding: utf-8 -*-
__author__ = 'bone-lee'

from redis_cache_client import RedisCacheClient
from constant import USER_RES_CACHE_KEY

from tornado import gen
import motorclient


class FBTUserResourceManager(object):
    EXPIRE_TIME = 300 * 60

    def __init__(self, db=None, cache=None):
        if db:
            self._db = db
        else:
            self._db = motorclient.fbt
        if cache:
            self._cache = cache
        else:
            self._cache = RedisCacheClient().get_instance()

    def key_of(self, uid):
        return USER_RES_CACHE_KEY+str(uid)

    @gen.coroutine
    def get_resource_of_user(self, uid):
        uid = long(uid)
        key = self.key_of(uid)
        res_list = self._cache.lrange(key, 0, -1)
        if res_list:
            raise gen.Return(res_list)
        else:
            resource_of_user = yield self.get_collection().find_one({'uid': uid}, {'file_ids': 1})
            if resource_of_user and 'file_ids' in resource_of_user:
                ret = resource_of_user["file_ids"][::-1]
                pipe = self._cache.pipeline()
                for file_id in ret:
                    pipe.rpush(key, file_id)
                pipe.expire(key, self.EXPIRE_TIME)
                pipe.execute()
                raise gen.Return(ret)
            else:
                raise gen.Return([])

    def get_resource_of_user2(self, uid, sync_db):
        uid = long(uid)
        key = self.key_of(uid)
        res_list = self._cache.lrange(key, 0, -1)
        if res_list:
            return res_list
        else:
            resource_of_user = sync_db.resources_of_user.find_one({'uid': uid}, {'file_ids': 1})
            if resource_of_user and 'file_ids' in resource_of_user:
                ret = resource_of_user["file_ids"][::-1]
                pipe = self._cache.pipeline()
                for file_id in ret:
                    pipe.rpush(key, file_id)
                pipe.expire(key, self.EXPIRE_TIME)
                pipe.execute()
                return ret
            else:
                return []

    def get_collection(self):
        return self._db.resources_of_user

    @gen.coroutine
    def add_to_my_resource_list(self, uid, file_id):
        uid = long(uid)
        key = self.key_of(uid)
        pipe = self._cache.pipeline()
        pipe.lpush(key, file_id)
        pipe.expire(key, self.EXPIRE_TIME)
        pipe.execute()
        yield self.get_collection().update({"uid": uid}, {"$push": {"file_ids": file_id}}, True)

    @gen.coroutine
    def add_file_in_dir_to_my_resource_list(self, uid, file_ids):  # file_ids is a list of file_id
        assert (isinstance(file_ids, list))
        uid = long(uid)
        key = self.key_of(uid)
        pipe = self._cache.pipeline()
        for file_id in file_ids:
            pipe.lpush(key, file_id)
        # pipe.lpush(key, file_ids)
        pipe.expire(key, self.EXPIRE_TIME)
        pipe.execute()
        yield self.get_collection().update({"uid": uid}, {"$push": {"file_ids": {"$each": file_ids}}}, True)

    @gen.coroutine
    def remove_from_my_resource_list(self, uid, file_id):
        uid = long(uid)
        modified_doc = yield self.get_collection().find_and_modify({"uid": uid}, {"$pull": {"file_ids": file_id}},
                                                                       new=True)
        key = self.key_of(uid)
        self._cache.lrem(key, 0, file_id)
        raise gen.Return(modified_doc)

    single_instance = None

    @classmethod
    def instance(cls):
        if cls.single_instance is None:
            cls.single_instance = FBTUserResourceManager()
        return cls.single_instance

    def set_db_cache(self, db, cache):
        self._db = db
        self._cache = cache