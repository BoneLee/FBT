__author__ = 'bone-lee'

from redis_pub_sub_client import RedisSubscribeClient
from constant import CACHE_OWNER_OF_RESOURCE, CHANNEL_ON_OFF
from constant import CHANNEL_RES_DEL, CHANNEL_RES_UPLOAD, CHANNEL_RES_PASS
from redis_cache_client import RedisCacheClient
from resource_manager import ResourceStoreManager
from cipher import WaveCipher as Cipher
from redis_sub_helper import RedisSubHelper

import simplejson as json
from tornado import gen
from concurrent.futures import ThreadPoolExecutor

class OnlineResources(object):
    _redis = None

    _RES_TYPE_SET_CACHE_KEY = "fbt:resources:type:"
    _ONLINE_UID_CACHE_KEY = "fbt:online-uid-list"

    _user_online_offline_sub = None
    _resource_add_sub = None
    _resource_del_sub = None
    _resource_pass_audit_sub = None

    _sync_db = None
    _async_db = None
    _executor = None

    @classmethod
    def initialize(cls, sync_db, async_db):
        assert sync_db is not None and async_db is not None
        cls._sync_db = sync_db
        cls._async_db = async_db
        cls._redis = RedisCacheClient().get_instance()
        cls._executor = ThreadPoolExecutor(max_workers=10)
        cls._init_subscribe()

    @classmethod
    def init(cls, async_db):
        assert async_db is not None
        cls._async_db = async_db
        cls._redis = RedisCacheClient().get_instance()

    @classmethod
    def _init_subscribe(cls):
        cls._user_online_offline_sub = RedisSubscribeClient(cls.on_user_online_offline, CHANNEL_ON_OFF)
        cls._resource_add_sub = RedisSubscribeClient(cls.on_resource_add, CHANNEL_RES_UPLOAD)
        cls._resource_del_sub = RedisSubscribeClient(cls.on_resource_del, CHANNEL_RES_DEL)
        cls._resource_pass_audit_sub = RedisSubscribeClient(cls.on_resource_add, CHANNEL_RES_PASS)

    @classmethod
    def get_resource_of_user(cls, uid):
        uid = long(uid)
        resource_of_user = cls._sync_db.resources_of_user.find_one({'uid': uid}, {'file_ids': 1})
        if resource_of_user and 'file_ids' in resource_of_user:
            return resource_of_user['file_ids']
        else:
            return []

    @classmethod
    def _increase_online_owners(cls, file_id, uid):
        cls._redis.sadd(CACHE_OWNER_OF_RESOURCE + str(file_id), uid)

    @classmethod
    def _decrease_online_owners(cls, file_id, uid):
        cls._redis.srem(CACHE_OWNER_OF_RESOURCE + str(file_id), uid)

    @classmethod
    def _add_online_info_to_public_res(cls, file_id, uid):
        type_info = cls._sync_db.all_resources.find_one({'file_id': file_id}, {'main_type': 1, "public": 1})
        if type_info and 'main_type' in type_info and 'public' in type_info:
            if type_info['public']:
                res_type = type_info['main_type']
                cls._redis.sadd(cls._RES_TYPE_SET_CACHE_KEY + str(res_type), file_id)
            cls._increase_online_owners(file_id, uid)

    @classmethod
    def _rm_online_info_from_res(cls, file_id, uid):
        type_info = cls._sync_db.all_resources.find_one({'file_id': file_id}, {'main_type': 1, "public": 1})
        if type_info and 'main_type' in type_info and 'public' in type_info:
            if type_info['public']:
                res_type = type_info['main_type']
                cls._redis.srem(cls._RES_TYPE_SET_CACHE_KEY + str(res_type), file_id)
            cls._decrease_online_owners(file_id, uid)

    @classmethod
    def _is_subfile(cls, file_id):
        return '+' in file_id

    @classmethod
    def _get_subfile_id(cls, file_id):
        return file_id.split('+')

    @classmethod
    def on_user_online_offline(cls, msg):
        if RedisSubHelper().is_located_myself(msg):
            cls._executor.submit(cls._process_online_offline_msg, msg)

    @classmethod
    def _process_online_offline_msg(cls, msg):
        msg = json.loads(msg)
        msg_type = int(msg['type'])
        uid = long(msg['uid'])
        msg = {"online": 0, "offline": 1}
        dir_set = set()
        if msg_type == msg["online"]:
            cls._redis.sadd(cls._ONLINE_UID_CACHE_KEY, uid)
            for file_id in cls.get_resource_of_user(uid):
                if cls._is_subfile(file_id):
                    (dir_id, subfile_id) = cls._get_subfile_id(file_id)
                    cls._increase_online_owners(subfile_id, uid)
                    if dir_id not in dir_set:
                        dir_set.add(dir_id)
                        cls._add_online_info_to_public_res(dir_id, uid)
                else:
                    cls._add_online_info_to_public_res(file_id, uid)
        elif msg_type == msg["offline"]:
            cls._redis.srem(cls._ONLINE_UID_CACHE_KEY, uid)
            for file_id in cls.get_resource_of_user(uid):
                if cls._is_subfile(file_id):
                    (dir_id, subfile_id) = cls._get_subfile_id(file_id)
                    cls._decrease_online_owners(subfile_id, uid)
                    if dir_id not in dir_set:
                        dir_set.add(dir_id)
                        cls._rm_online_info_from_res(dir_id, uid)
                else:
                    cls._rm_online_info_from_res(file_id, uid)

    @classmethod
    def on_resource_add(cls, msg):
        if RedisSubHelper().is_located_myself(msg):
            print "add msg:"+msg
            msg = json.loads(msg)
            file_id = str(msg['file_id'])
            uid = long(msg['uid'])
            if cls._redis.sismember(cls._ONLINE_UID_CACHE_KEY, uid):
                if "is_subfile" in msg and msg["is_subfile"]:
                    cls._increase_online_owners(file_id, uid)
                else:
                    cls._add_online_info_to_public_res(file_id, uid)

    @classmethod
    def on_resource_del(cls, msg):
        if RedisSubHelper().is_located_myself(msg):
            msg = json.loads(msg)
            print "sub msg:"+msg
            file_id = str(msg['file_id'])
            uid = long(msg['uid'])
            if cls._redis.sismember(cls._ONLINE_UID_CACHE_KEY, uid):
                if "is_subfile" in msg and msg["is_subfile"]:
                    cls._decrease_online_owners(file_id, uid)
                else:
                    cls._rm_online_info_from_res(file_id, uid)

    @classmethod
    def finalize(cls):
        if cls._user_online_offline_sub:
            cls._user_online_offline_sub.close()
        if cls._resource_add_sub:
            cls._resource_add_sub.close()
        if cls._resource_del_sub:
            cls._resource_del_sub.close()
        if cls._resource_pass_audit_sub:
            cls._resource_pass_audit_sub.close()
        if cls._executor:
            cls._executor.shutdown(wait=False)

    @classmethod
    @gen.coroutine
    def get_online_resources_by_type(cls, main_type=1, page=1, max_cnt_in_page=20):
        (start, end) = (max_cnt_in_page * (page - 1), max_cnt_in_page * page)

        # cache for all page resources
        cache_key = "online-resource:type:"+str(main_type)
        cached_data = cls._redis.get(cache_key)
        if cached_data:
            resource_pairs = json.loads(cached_data)
        else:
            resources = cls._redis.smembers(cls._RES_TYPE_SET_CACHE_KEY + str(main_type))
            if not resources: raise gen.Return([])
            resource_pairs = [(file_id, int(cls._redis.scard(CACHE_OWNER_OF_RESOURCE + str(file_id)))) for file_id in
                              resources]
            resource_pairs.sort(lambda x, y: cmp(y[1], x[1]))

            pipe = cls._redis.pipeline(transaction=False)
            pipe.set(cache_key, json.dumps(resource_pairs))
            pipe.expire(cache_key, 60 * 60)
            pipe.execute()

        ret = []
        for file_id, online_num in resource_pairs[start: end]:
            res = yield cls._async_db.all_resources.find_one({'file_id': file_id})
            if not res: 
                print "file_id not found:"+file_id
                continue
            one_resource = ResourceStoreManager.extract_resource_from_db(res)
            one_resource["online_owners_num"] = online_num
            for comment in one_resource['comments']:
                comment['content'] = Cipher.encrypt(comment['content'])
            one_resource['tags'] = Cipher.encrypt(one_resource['tags'])
            one_resource['file_name'] = Cipher.encrypt(one_resource['file_name'])
            ret.append(one_resource)
        raise gen.Return(ret)

    @classmethod
    def get_online_resources_count(cls, main_type):
        return cls._redis.scard(cls._RES_TYPE_SET_CACHE_KEY + str(main_type))

    @classmethod
    def get_online_uids(cls):
        return cls._redis.smembers(cls._ONLINE_UID_CACHE_KEY)

    @classmethod
    def get_online_uids_of_resource(cls, fid):
        return cls._redis.smembers(CACHE_OWNER_OF_RESOURCE + str(fid))
