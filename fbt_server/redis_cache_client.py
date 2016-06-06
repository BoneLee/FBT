__author__ = 'bone-lee'

from redis_handler import RedisHandler
from singleton import singleton
# import redis

@singleton
class RedisCacheClient(object):
    def __init__(self):
        # self._redis_cache = redis.StrictRedis(password="123-fbt-all-cache-!@#", port=6382)
        self._redis_cache = RedisHandler()


    def get_instance(self):
        return self._redis_cache

