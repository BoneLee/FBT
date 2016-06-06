# -*- coding: utf-8 -*-
__author__ = 'bone'

import os
import sys
fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from redis_proxy import RedisProxy
from user_ip_cache import UserIPCache

import tornado.testing
import tornado.gen
import redis


class RedisProxyTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=5)
    def test_user_ip_cache(self):
        client = redis.StrictRedis()
        client.flushdb()
        r = RedisProxy(redis_client=client)
        user_ip_cache = UserIPCache()
        user_ip_cache.set_cache(r)
        user_ip_cache.reset()

        user = 1234
        ip = "1.2.3.4"
        ip2 = user_ip_cache.get_user_ip(user)
        self.assertEqual(ip2, None)
        self.assertEqual(len(user_ip_cache.get_all_users()), 0)

        user_ip_cache.load()
        user_ip_list = user_ip_cache.get_user_ip_list()
        self.assertEqual(len(user_ip_list), 0)

        user_ip_cache.update_my_ip(user, ip)
        ip2 = user_ip_cache.get_user_ip(user)
        self.assertEqual(ip2, ip)
        self.assertEqual(len(user_ip_cache.get_all_users()), 1)

        user222 = 4321
        ip222 = "43.21.21.12"
        user_ip_cache.update_my_ip(user222, ip222)
        self.assertEqual(len(user_ip_cache.get_all_users()), 2)

        user_ip_cache.delete_my_ip(user)
        ip2 = user_ip_cache.get_user_ip(user)
        self.assertEqual(ip2, None)
        self.assertEqual(len(user_ip_cache.get_all_users()), 1)

        user_ip_cache.load()
        user_ip_list = user_ip_cache.get_user_ip_list()
        self.assertEqual(len(user_ip_list), 1)

        user = 12345
        ip = "1.2.3.5"
        user_ip_cache.update_my_ip(user, ip)
        user_ip_cache.reset()
        user_ip_cache.load()

        user_ip_list = user_ip_cache.get_user_ip_list()
        self.assertEqual(len(user_ip_list), 2)

if __name__ == '__main__':
    import unittest
    unittest.main()

