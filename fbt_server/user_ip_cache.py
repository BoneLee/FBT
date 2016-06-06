#-*- coding:utf-8 -*-
__author__ = 'bone-lee'

from redis_proxy import RedisProxy
from constant import USER_IP_CACHE_HASH_KEY, USER_IP_CACHE_SET_KEY

import cPickle as pickle
import os
import logging


# TODO(bone): should remove pub sub

class UserIPCache(object):
    '''
    memory user ip
    '''
    _user_ip_list = dict()  # such as {fbt_user1: 112.12.23.4,fbt_user2: 123.2.3.1}
    _redis_cache = RedisProxy()

    @classmethod
    def set_cache(cls, cache):
        cls._redis_cache = cache

    @classmethod
    def reset(cls):
        cls._user_ip_list = dict()

    @classmethod
    def update_my_ip(cls, user, ip):
        assert user >= 0
        cls._user_ip_list[user] = ip
        pipeline = cls._redis_cache.pipeline()
        pipeline.sadd(USER_IP_CACHE_SET_KEY, user)
        pipeline.hset(USER_IP_CACHE_HASH_KEY, user, ip)
        pipeline.execute()

    @classmethod
    def delete_my_ip(cls, user):
        assert user >= 0
        if user in cls._user_ip_list:
            del cls._user_ip_list[user]
        pipeline = cls._redis_cache.pipeline()
        pipeline.srem(USER_IP_CACHE_SET_KEY, user)
        pipeline.hdel(USER_IP_CACHE_HASH_KEY, user)
        pipeline.execute()

    @classmethod
    def get_user_ip_list(cls):
        return cls._user_ip_list

    @classmethod
    def get_all_users(cls):
        ret = cls._redis_cache.smembers(USER_IP_CACHE_SET_KEY)
        if ret:
            return ret
        else:
            return []

    @classmethod
    def user_online(cls, user):
        assert user >= 0
        return user in cls._user_ip_list

    @classmethod
    def get_user_ip(cls, user):
        assert user >= 0
        if user in cls._user_ip_list:
            return cls._user_ip_list[user]
        else:
            return None

    @classmethod
    def _get_pkl_file(cls, port):
        file_name = "users"+str(port)+".pkl"
        return file_name

    @classmethod
    def load(cls, port=None):
        user_ip_cache = cls._redis_cache.hgetall(USER_IP_CACHE_HASH_KEY)
        if not user_ip_cache:
            logging.info("load user ip from redis failed")
            file_name = cls._get_pkl_file(port)
            if os.path.isfile(file_name):
                with open(file_name,'r+') as infile:
                    cls._user_ip_list = pickle.load(infile)
                    pipeline = cls._redis_cache.pipeline()
                    for user, ip in cls._user_ip_list.iteritems():
                        pipeline.sadd(USER_IP_CACHE_SET_KEY, user)
                        pipeline.hset(USER_IP_CACHE_HASH_KEY, user, ip)
                    pipeline.execute()
                    logging.info("load user ip from local file")
        else:
            for user, ip in user_ip_cache.iteritems():
                cls._user_ip_list[long(user)] = ip
            logging.info("load user ip from redis Ok")

    @classmethod
    def save(cls, port):
        pass
        # file_name = cls._get_pkl_file(port)
        # with open(file_name, 'wb') as outfile:
        #     pickle.dump(cls._user_ip_list, outfile)
        #     logging.info("save user ip to local file")
