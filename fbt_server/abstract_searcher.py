# -*- coding: utf-8 -*-

__author__ = 'bone'

from redis_cluster_proxy import Redis
from tornado.escape import utf8


class AbstractSearcher(object):
    def __init__(self, redis_cache=None):
        self._redis = redis_cache or Redis()

    def get_search_record_key(self):
        return type(self).__name__

    def record_keyword(self, keyword):
        keyword = utf8(keyword)
        key = 'top-search:keyword:' + self.get_search_record_key()
        exists = self._redis.exists(key)
        self._redis.zincrby(key, keyword, 1)
        if not exists:
            self._redis.expire(key, 7*24*60*60)

    def top_search_keywords(self):
        key = 'top-search:keyword:' + self.get_search_record_key()
        ret = self._redis.zrevrange(key, 0, 20, withscores=True)
        if ret:
            return ret
        else:
            return []
