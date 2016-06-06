# -*- coding: utf-8 -*-
__author__ = 'bone'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

import os
import sys
fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from redis_proxy import RedisProxy
from redis_cluster_proxy import Redis

import tornado.testing
import tornado.gen
import redis


class RedisProxyTestCase(tornado.testing.AsyncTestCase):
    def setUp(self):
        super(RedisProxyTestCase, self).setUp()
        hosts = [('127.0.0.1', 6379, '127.0.0.1', 6379), ('127.0.0.2', 6379, '127.0.0.2', 6379),]
        self._redis = Redis(Redis.FOR_CACHE, hosts)

    def tearDown(self):
        pass

    @tornado.testing.gen_test(timeout=5)
    def test_redis_cluster(self):
        r = self._redis
        k = 1
        r.set("name"+str(k), "bone")
        assert r.get("name"+str(k)) == "bone"
        k = 99
        r.set("name"+str(k), "bone")
        assert r.get("name"+str(k)) == "bone"
        k = 9999
        r.set("name"+str(k), "bone")
        assert r.get("name"+str(k)) == "bone"
        k = 1111
        r.hset("name"+str(k), "bone", 1111)
        assert r.hget("name"+str(k), "bone") == "1111"
        pipe = r.pipeline()
        pipe.hset("person", "gogo", "OK")
        pipe.execute()
        assert r.hget("person", "gogo") == "OK"

    @tornado.testing.gen_test(timeout=5)
    def test_redis_proxy(self):
        client = redis.StrictRedis()
        client.flushdb()
        r = RedisProxy(redis_client=client)
        r.set("name", "bone")
        self.assertEqual(r.get("name"), "bone")
        r.hset("k", "f", "123")
        self.assertEqual(r.hget('k','f'), "123")

if __name__ == '__main__':
    import unittest
    unittest.main()

