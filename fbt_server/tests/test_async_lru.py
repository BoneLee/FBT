#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import redis
import mock
import copy
from tornado import gen
from tornado.testing import gen_test, AsyncTestCase
from motor import MotorClient
import time

sys.path.append('..')
from redis_async_lru_scheduler import RedisDelegate, StaticAllResources, Tags, Fblog, Users, KEYS_MODIFIED_SET, LRU_QUEUE, acquire_lock_with_timeout
from async_redis.asyncRedis import AsyncStrictRedis

__author__ = 'spark'

class AsyncLRUTest(AsyncTestCase):
    def setUp(self):
        super(AsyncLRUTest, self).setUp()
        self.sr = redis.StrictRedis()
        self.ar = AsyncStrictRedis()
        self.m = MotorClient()
        self.c = self.m.my_test
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        yield self.ar.flushdb()
        yield self.m.drop_database('my_test')

        self.redis_delegator = RedisDelegate(self.ar, self.c)
    
        tag = Tags()
        users = Users()
        fblog = Fblog()
        static_all_resources = StaticAllResources()
        self.redis_delegator.add_collection(tag)
        self.redis_delegator.add_collection(users)
        self.redis_delegator.add_collection(fblog)
        self.redis_delegator.add_collection(static_all_resources, 'all_resources')

    @gen_test
    def test_SetField_get_and_set(self):
        file_ids = self.redis_delegator.tags(1).file_ids
        sr = self.sr
        res = yield file_ids.get()
        self.assertEqual(res, set())
        file_ids_list = ['1','2','3']
        yield file_ids.set(file_ids_list)
        self.assertEqual(sr.scard(file_ids.key_name), 3)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, file_ids.key_name))
        self.assertTrue(sr.zrank(LRU_QUEUE, file_ids.key_name) is not None)
        res = yield file_ids.get()
        self.assertEqual(res, set(file_ids_list))
        self.stop()


    @gen_test
    def test_SetField_scard_sadd_srem_sismember(self):
        file_ids = self.redis_delegator.tags(1).file_ids
        sr = self.sr
        res = yield file_ids.scard()
        self.assertEqual(res, 0)
        res = yield file_ids.sadd('1')
        self.assertEqual(res, 1)
        res = yield file_ids.scard()
        self.assertEqual(res, 1)
        res = yield file_ids.sadd('1', '2', '3')
        self.assertEqual(res, 2)
        res = yield file_ids.sismember('2')
        self.assertTrue(res)
        res = yield file_ids.srem('2')
        self.assertEqual(res, 1)
        res = yield file_ids.sismember('2')
        self.assertFalse(res)
        res = yield file_ids.scard()
        self.assertEqual(res, 2)
        self.stop()


    @gen_test
    def test_SetField_make_data_in_redis(self):
        file_ids = self.redis_delegator.tags(1).file_ids
        sr = self.sr
        file_ids_list = ['1','2','3', '4']
        yield self.c.tags.insert({'uid': 1, 'file_ids': file_ids_list})
        res = yield file_ids.get()
        self.assertEqual(res, set(file_ids_list))
        self.stop()


    @gen_test
    def test_ListField_get_and_set(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        res = yield log.get()
        self.assertEqual(res, list())
        log_list = [{'1':[1,2]},{'2': {'2':1}},{'3':[1,2]}]
        yield log.set(log_list)
        self.assertEqual(sr.llen(log.key_name), 3)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, log.key_name))
        self.assertTrue(sr.zrank(LRU_QUEUE, log.key_name) is not None)
        res = yield log.get()
        self.assertEqual(res, log_list)
        self.stop()


    @gen_test
    def test_ListField_llen_ltrim(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        log_list = [{'1':[1,2]},{'2': {'2':1}},{'3':[1,2]}, {'4':[2,3,4]}]
        yield log.set(log_list)
        res = yield log.llen()
        self.assertEqual(res, 4)
        res = yield log.ltrim(0, 5)
        self.assertTrue(res)
        res = yield log.llen()
        self.assertEqual(res, 4)  
        res = yield log.ltrim(0, 1)
        #self.assertEqual(res, 2)
        res = yield log.llen()
        self.assertEqual(res, 2)      
        res = yield log.get()
        self.assertEqual(res, log_list[:2])
        self.stop()


    @gen_test
    def test_ListField_lindex(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        log_list = [{'1':[1,2]},{'2': {'2':1}},{'3':[1,2]}, {'4':[2,3,4]}]
        yield log.set(log_list)
        res = yield log.lindex(0)
        self.assertEqual(res, log_list[0])
        res = yield log.lindex(1)
        self.assertEqual(res, log_list[1])
        res = yield log.lindex(-1)
        self.assertEqual(res, log_list[-1]) 
        res = yield log.lindex(-5)
        self.assertEqual(res, None)
        res = yield log.lindex(5)
        self.assertEqual(res, None)
        self.stop()
    
    @gen_test
    def test_ListField_lrem(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        log_list = [{'1':[1,2]},{'2': {'2':1}},{'3':[1,2]}, {'2': {'2':1}}, {'2': {'2':1}}, {'4':[2,3,4]}, {'2': {'2':1}}]
        yield log.set(log_list)
        res = yield log.lrem(1, {'2': {'2':1}})
        res = yield log.get()
        del log_list[1]
        self.assertEqual(res, log_list)
        res = yield log.lrem(-1, {'2': {'2':1}})
        res = yield log.get()
        del log_list[-1]
        self.assertEqual(res, log_list)
        res = yield log.lrem(0, {'2': {'2':1}})
        res = yield log.get()
        del log_list[2:4]
        self.assertEqual(res, log_list)
        self.stop()


    @gen_test
    def test_ListField_lindex_rpush_lpop_lrange(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        log_list = [{'1':[1,2]},{'4':[2,3,4]}, {'2': {'2':1}},{'3':[1,2]}]
        res = yield log.rpush({'1':[1,2]})
        self.assertEqual(res, 1) 
        res = yield log.rpush({'4':[2,3,4]})
        self.assertEqual(res, 2) 
        res = yield log.rpush({'2': {'2':1}},{'3':[1,2]})
        self.assertEqual(res, 4) 
        res = yield log.lrange(0, -1)
        self.assertEqual(res, log_list)
        res = yield log.lrange(0, 5)
        self.assertEqual(res, log_list)
        res = yield log.lrange(0, -5)
        self.assertEqual(res, [])
        res = yield log.lrange(0, 2)
        self.assertEqual(res, log_list[:3])
        res = yield log.lrange(1, 3)
        self.assertEqual(res, log_list[1:4])
        self.stop()


    @gen_test
    def test_ListField_make_data_in_redis(self):
        log = self.redis_delegator.fblog(1).log
        sr = self.sr
        log_list = [{'1':[1,2]},{'4':[2,3,4]}, {'2': {'2':1}},{'3':[1,2]}]
        yield self.c.fblog.insert({'uid': 1, 'online_time': 1.0, 'log': log_list})
        #res = yield self.c.fblog.find_one()
        #print res
        res = yield  log.get()
        self.assertEqual(res, log_list)
        self.stop()


    @gen_test
    def test_ZsetField_get_and_set(self):
        friends = self.redis_delegator.users(1).friends
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 0}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield friends.set(friends_list)
        self.assertEqual(sr.zcard(friends.key_name), 4)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, friends.key_name))
        self.assertTrue(sr.zrank(LRU_QUEUE, friends.key_name) is not None)
        res = yield friends.get()
        self.assertEqual(res, sorted(friends_list, key = lambda x: x['isStar']))
        self.stop()


    @gen_test
    def test_ZsetField_zscore(self):
        friends = self.redis_delegator.users(1).friends
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield friends.set(friends_list)
        res = yield friends.zscore(1)
        self.assertEqual(res, 5)
        res = yield friends.zscore(3)
        self.assertEqual(res, 1)
        res = yield friends.zscore(8)
        self.assertEqual(res, None)
        self.stop()


    @gen_test
    def test_ZsetField_zadd_zrem_zrange(self):
        friends = self.redis_delegator.users(1).friends
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield friends.zadd(5, 1, 0, 2, 1, 3, 0, 4)
        res = yield friends.zcard()
        self.assertEqual(res, len(friends_list))
        res = yield friends.zrange(0, -1)
        self.assertEqual(res, sorted(friends_list, key = lambda x: x['isStar']))
        res = yield friends.zrem(1)
        self.assertEqual(res, 1)
        res = yield friends.zrange(0, -1)
        self.assertEqual(res, sorted(friends_list[1:], key = lambda x: x['isStar']))
        res = yield friends.zrem(5)
        self.assertEqual(res, 0)
        res = yield friends.zrange(0, -1)
        self.assertEqual(res, sorted(friends_list[1:], key = lambda x: x['isStar']))

        res = yield friends.zrem(2, 3)
        self.assertEqual(res, 2)
        res = yield friends.zrange(0, -1)
        self.assertEqual(res, sorted(friends_list[3:], key = lambda x: x['isStar']))
        self.stop()


    @gen_test
    def test_ZsetField_make_data_in_redis(self):
        friends = self.redis_delegator.users(1).friends
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz','friends': friends_list})
        #res = yield self.c.fblog.find_one()
        #print res
        res = yield  friends.get()
        self.assertEqual(res, sorted(friends_list, key = lambda x: x['isStar']))
        self.stop()


    @gen_test
    def test_set_None(self):
        users = self.redis_delegator.users(1)
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': friends_list})
        doc = yield self.c.users.find_one({'uid': 1})
        res = yield users.get('haslog')
        self.assertEqual(res, 1)
        res = yield users.get('test')
        self.assertEqual(res, 'xyz')
        res = yield users.find(1, ['test', 'xyz'])
        self.assertEqual(res, {'haslog': 1, 'test': 'xyz'})

        yield users.set('test', None)
        self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users._key))
        self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is not None)
        self.assertEqual(sr.hgetall(users._key), {'haslog': '1'})
        doc1 = yield self.c.users.find_one({'uid': 1})
        doc['test'] = None
        self.assertEqual(doc, doc1)
        self.stop()


    @gen_test
    def test_common_field_get_and_set(self):
        users = self.redis_delegator.users(1)
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': friends_list})
        yield users.set('haslog', 0)
        res = yield users.get('haslog')
        self.assertEqual(res, 0)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users._key))
        self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is not None)
        self.stop()


    @gen_test
    def test_unset_field(self):
        users = self.redis_delegator.users(1)
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': friends_list})
        doc = yield self.c.users.find_one({'uid': 1})
        res = yield users.get('test')
        self.assertEqual(res, 'xyz')

        yield users.delete(1, 'test')
        self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users._key))
        self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is not None)
        self.assertEqual(sr.hgetall(users._key), {'haslog': '1'})
        doc1 = yield self.c.users.find_one({'uid': 1})
        doc.pop('test')
        self.assertEqual(doc, doc1)
        self.stop()

    @gen_test
    def test_static_find(self):
        sr = self.sr
        test_resources = [{'file_id': str(i), 'file_name': 'file' + str(i), 'main_type': i % 2, 'mtime': i, 'download_num': i} for i in range(15)]
        test_resources_copy = copy.deepcopy(test_resources)
        for t in test_resources_copy:
            self.c.all_resources.insert(t)
        res = yield self.redis_delegator.all_resources.find('0')
        self.assertEqual(res, test_resources[0])
        self.assertTrue(sr.exists('all_resources:0'))
        res = yield self.redis_delegator.all_resources.find([str(_) for _ in range(6)])
        res = sorted(res, key=lambda x: x['file_id'])
        self.assertEqual(res, test_resources[:6])
        res = yield self.redis_delegator.all_resources.find([str(_) for _ in range(7, 12)], {'main_type': 1})
        res = sorted(res, key=lambda x: int(x['file_id']))
        self.assertEqual(res, test_resources[7:12:2])


    @gen_test
    def test_find_update(self):
        users = self.redis_delegator.users(1)
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        doc = {'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])}
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])})
        #doc = yield self.c.users.find_one({'uid': 1})
        res = yield users.find(1)
        self.assertEqual(res, doc)

        update_doc = {'haslog': 3, 'friends': [{'uid': 2, 'isStar': 11}]}
        yield users.update(1, update_doc)
        doc.update(update_doc)
        res = yield users.find(1)
        self.assertEqual(res, doc)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users._key))
        self.assertFalse(sr.zrank(LRU_QUEUE, users._key) is None)
        self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users.friends.key_name))
        self.assertFalse(sr.zrank(LRU_QUEUE, users.friends.key_name) is None)
        
        update_doc = {'haslog': None}
        yield users.update(1, update_doc)
        #doc.update(update_doc)
        doc.pop('haslog')
        res = yield users.find(1)
        self.assertEqual(res, doc)

        update_doc = {'test': '123', 'abc': 'aaa'}
        yield users.update(1, update_doc)
        doc.update(update_doc)
        res = yield users.find(1)
        self.assertEqual(res, doc)
        self.stop()


    @gen_test
    def test_write_back(self):
        users = self.redis_delegator.users(1)
        sr = self.sr
        friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
        doc = {'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])}
        yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])})
        #doc = yield self.c.users.find_one({'uid': 1})
        res = yield users.find(1)
        self.assertEqual(res, doc)

        update_doc = {'test': '123', 'abc': 'aaa'}
        yield users.update(1, update_doc)
        doc.update(update_doc)
        res = yield users.find(1)
        self.assertEqual(res, doc)
        #self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users._key))
        #self.assertFalse(sr.zrank(LRU_QUEUE, users._key) is None)
        yield users.write_back(1)
        #self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users._key))
        #self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is None)
        doc1 = yield self.c.users.find_one({'uid': 1}, {'uid': 0, '_id': 0})
        self.assertEqual(doc, doc1)

        update_doc = {'haslog': 3, 'friends': [{'uid': 2, 'isStar': 11}]}
        yield users.update(1, update_doc)
        doc.update(update_doc)
        yield users.write_back(1, 'friends')
        yield users.write_back(1)
        doc1 = yield self.c.users.find_one({'uid': 1}, {'uid': 0, '_id': 0})
        self.assertEqual(doc, doc1)
        self.stop()

    @gen_test(timeout=10)
    def test_try_write_back(self):
        def side_effect(*args, **kwargs):
            kwargs['lock_timeout'] = 1
            return acquire_lock_with_timeout(*args, **kwargs)
        with mock.patch('redis_async_lru_scheduler.acquire_lock_with_timeout', side_effect=side_effect) as whate_ever:
        #with mock.patch('redis_async_lru_scheduler.LOCK_TIMEOUT', 1) as whate_ever:
            LOCK_TIMEOUT = 1
            users = self.redis_delegator.users(1)
            sr = self.sr
            friends_list = [{'uid': 1, 'isStar': 5}, {'uid': 2, 'isStar': 0}, {'uid': 3, 'isStar': 1}, {'uid': 4, 'isStar': 0}]
            doc = {'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])}
            yield self.c.users.insert({'uid': 1, 'haslog': 1, 'test': 'xyz', 'friends': sorted(friends_list, key = lambda x: x['isStar'])})
            #doc = yield self.c.users.find_one({'uid': 1})
            res = yield users.find(1)
            self.assertEqual(res, doc)
            self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users._key))
            self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is not None)

            update_doc = {'test': '123', 'abc': 'aaa'}
            yield users.update(1, update_doc)
            doc.update(update_doc)
            self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users._key))
            self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is not None)

            time.sleep(LOCK_TIMEOUT+1)
            res = yield self.redis_delegator.try_write_back(self.ar, 'users:1')

            self.assertTrue(res)
            self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users._key))
            self.assertTrue(sr.zrank(LRU_QUEUE, users._key) is None)
            doc1 = yield self.c.users.find_one({'uid': 1}, {'uid': 0, '_id': 0})
            self.assertEqual(doc, doc1)

            update_doc = {'haslog': 3, 'friends': [{'uid': 2, 'isStar': 11}]}
            yield users.update(1, update_doc)
            doc.update(update_doc)
            self.assertTrue(sr.sismember(KEYS_MODIFIED_SET, users.friends.key_name))
            self.assertTrue(sr.zrank(LRU_QUEUE, users.friends.key_name) is not None)

            time.sleep(LOCK_TIMEOUT+1)
            res = yield self.redis_delegator.try_write_back(self.ar, 'users:1.friends')
            self.assertTrue(res)
            res = yield self.redis_delegator.try_write_back(self.ar, 'users:1')
            self.assertFalse(sr.sismember(KEYS_MODIFIED_SET, users.friends.key_name))
            self.assertTrue(sr.zrank(LRU_QUEUE, users.friends.key_name) is None)
            doc1 = yield self.c.users.find_one({'uid': 1}, {'uid': 0, '_id': 0})
            self.assertEqual(doc, doc1)
            self.stop()

if __name__ == '__main__':
    import unittest
    unittest.main()
