# -*- coding: utf-8 -*-

import sys
import redis
import mock
from tornado import gen, ioloop
from tornado.testing import gen_test, AsyncTestCase
from motor import MotorClient
from pymongo import MongoClient
from random import uniform, randint, choice
from string import letters
from itertools import permutations
from collections import defaultdict

mock_redis = redis.StrictRedis()
#sync_db = MongoClient()
#db = MotorClient()
sys.path.append('..')
import mongoclient
import motorclient

mongoclient.set_mode('test')
motorclient.set_mode('test')
from async_redis.asyncRedis import AsyncStrictRedis
from fileNameSearcher import FileNameSearcher, make_key_for_keyword
from constant import USER_IP_CACHE_SET_KEY

__author__ = 'spark'

test_mtime = [randint(1, 10000) for _ in range(20)]
test_main_type = [randint(0, 9) for _ in range(20)]
test_download_num = [randint(1, 10000) for _ in range(20)]
pk = permutations(letters, 2)
test_keyword = [''.join(pk.next()) for _ in range(6)]
pf = permutations(test_keyword, 2)
test_filename = [' '.join(pf.next()) for _ in range(20)]
test_resources = list()

class FileNameSearcherTest(AsyncTestCase):
    def setUp(self):
        super(FileNameSearcherTest, self).setUp()
        self.sr = redis.StrictRedis()
        self.ar = AsyncStrictRedis()
        self.m = MotorClient()
        self.c = self.m.fbt
        self.patcher1 = mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis)
        self.patcher1.start()
        '''
        self.patcher2 = mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db)
        self.patcher3 = mock.patch("motor.MotorReplicaSetClient", return_value=db)
        #self.patcher4 = mock.patch("async_redis.asyncRedis.AsyncStrictRedis", spec=AsyncStrictRedis, return_value=AsyncStrictRedis())
        self.patcher2.start()
        self.patcher3.start()
        #self.patcher4.start()
        '''
        self.io_loop.run_sync(self.setup_coro)

    def tearDown(self):
        self.patcher1.stop()
        '''
        self.patcher2.stop()
        self.patcher3.stop()
        #self.patcher4.stop()
        '''

    @gen.coroutine
    def setup_coro(self):
        yield self.ar.flushdb()
        yield self.m.drop_database('fbt')
        yield self.ar.sadd(USER_IP_CACHE_SET_KEY, *[1, 2, 3, 4])
        yield self.c.users.insert({'uid': 1, 'friends': [{'uid': 2, 'isStar': 1}, {'uid': 3, 'isStar': 1}]})
        yield self.c.resources_of_user.insert({'uid': 2, 'file_ids': [str(_) for _ in range(10)]})
        yield self.c.resources_of_user.insert({'uid': 3, 'file_ids': [str(_) for _ in range(5, 15)]})
        yield self.c.resources_of_user.insert({'uid': 4, 'file_ids': [str(_) for _ in range(15, 20)]})
        for i, file_name in enumerate(test_filename):
            file_id = str(i)
            resource = {'file_id': file_id, 'mtime': test_mtime[i], 'download_num': test_download_num[i],
                                 'public': 1, 'main_type': test_main_type[i], 'file_name': file_name}
            test_resources.append(resource)
            yield self.c.all_resources.insert(resource)
            yield FileNameSearcher().file_id_add_title(file_id, file_name)
            #yield [self.c.all_resources.insert(resource), FileNameSearcher().file_id_add_title(file_id, file_name)]

    @gen_test(timeout=3)
    def test_all(self):
        search_key = test_keyword[3]
        res = yield FileNameSearcher().query_file_ids_by_file_name(search_key, 1, 4)
        res_list = list()
        for i, v in enumerate(test_filename):
            if search_key in v:
                test_resources[i].pop('_id')
                res_list.append(test_resources[i])

        res_list = sorted(res_list, key=lambda x: x["mtime"], reverse=True)
        res = yield FileNameSearcher().query_file_ids_by_file_name(search_key, 1, 4, sort="mtime")
        #print res_list[0:3], len(res_list)
        #print res, search_key
        self.assertEqual(res, (len(res_list), res_list[0:4]))

        #print res
        res_list = sorted(res_list, key=lambda x: x["download_num"], reverse=True)
        res = yield FileNameSearcher().query_file_ids_by_file_name(search_key, 1, 4, sort="download_num")
        self.assertEqual(res, (len(res_list), res_list[0:4]))

        res = yield FileNameSearcher().query_file_ids_by_file_name('a b', 1, 4, sort="download_num")
        self.assertEqual(res, (0, []))

        res = yield FileNameSearcher().query_file_ids_by_file_name('xxxxxxxx', 1, 4, sort="download_num")
        self.assertEqual(res, (0, []))

        # test for query_file_ids_by_file_name_private

        search_key = test_keyword[1]
        print 'search_key', search_key
        res_list = list()
        for i, v in enumerate(test_filename[:15]):
            if search_key in v:
                if '_id' in test_resources[i]:
                    test_resources[i].pop('_id')
                res_list.append(test_resources[i])
        res = yield FileNameSearcher().query_file_ids_by_file_name_private(1, search_key, 1, 4, sort="mtime")
        res_list = sorted(res_list, key=lambda x: x["mtime"], reverse=True)
        self.assertEqual(res, (len(res_list), res_list[0:4]))

        # test for query_file_ids_by_file_name_private
        res_list = list()
        for i, v in enumerate(test_filename[:15]):
            if '_id' in test_resources[i]:
                test_resources[i].pop('_id')
            res_list.append(test_resources[i])
        res = yield FileNameSearcher().get_private_resources(1, 1, 4, sort="mtime")
        res_list = sorted(res_list, key=lambda x: x["mtime"], reverse=True)
        self.assertEqual(res, (15, res_list[0:4]))
        
        # test for query_file_ids_by_file_name_private
        print test_main_type
        main_type = test_main_type[0]
        res_list = list()
        for i, v in enumerate(test_filename[:15]):
            if main_type == test_resources[i]['main_type']:
                if '_id' in test_resources[i]:
                    test_resources[i].pop('_id')
                res_list.append(test_resources[i])
        res_list = sorted(res_list, key=lambda x: x["download_num"], reverse=True)
        res = yield FileNameSearcher().get_private_resources_by_type(1, main_type, 1, 4, sort="download_num")
        print len(res_list)
        self.assertEqual(res, (len(res_list), res_list[0:4]))

        ##################### test_basic ###################
        # sync
        test_filename1 = ' '.join(test_keyword[:3])
        test_file_id = '21'
        filename_searcher = FileNameSearcher()
        rdb = filename_searcher.db
        mongo = filename_searcher.mongoDB
        filename_searcher.file_id_add_title_sync(test_file_id, test_filename1)
        for k in test_keyword[:3]:
            key_name = make_key_for_keyword(k)
            self.assertTrue(rdb.sismember(key_name, test_file_id))

        for res in mongo.key_fileids.find({'key': {"$in": test_keyword[:3]}}):
            self.assertTrue(test_file_id in res['file_ids'])

        filename_searcher.remove_file_id_sync(test_file_id, test_filename1)
        for k in test_keyword[:3]:
            key_name = make_key_for_keyword(k)
            self.assertFalse(rdb.sismember(key_name, test_file_id))

        for res in mongo.key_fileids.find({'key': {"$in": test_keyword[:3]}}):
            self.assertFalse(test_file_id in res['file_ids'])

        # async
        yield filename_searcher.file_id_add_title(test_file_id, test_filename1)
        for k in test_keyword[:3]:
            key_name = make_key_for_keyword(k)
            self.assertTrue(rdb.sismember(key_name, test_file_id))

        for res in mongo.key_fileids.find({'key': {"$in": test_keyword[:3]}}):
            self.assertTrue(test_file_id in res['file_ids'])

        yield filename_searcher.remove_file_id(test_file_id, test_filename1)
        for k in test_keyword[:3]:
            key_name = make_key_for_keyword(k)
            self.assertFalse(rdb.sismember(key_name, test_file_id))

        for res in mongo.key_fileids.find({'key': {"$in": test_keyword[:3]}}):
            self.assertFalse(test_file_id in res['file_ids'])

        # test init
        filename_searcher.drop()
        filename_searcher.init_from_mongo()
        key_fileids_dict = defaultdict(list)
        for i, f in enumerate(test_filename):
            i = str(i)
            for k in f.split():
                key_fileids_dict[k].append(i)
        for k in test_keyword:
            key_name = make_key_for_keyword(k)
            self.assertEqual(sorted(rdb.smembers(key_name)), sorted(key_fileids_dict[k]))

        for res in mongo.key_fileids.find():
            self.assertEqual(sorted(res['file_ids']), sorted(key_fileids_dict[res['key']]))
        # test add
        filename_searcher.scan_from_mongo(0)
        for k in test_keyword:
            key_name = make_key_for_keyword(k)
            self.assertEqual(sorted(rdb.smembers(key_name)), sorted(key_fileids_dict[k]))

        for res in mongo.key_fileids.find():
            self.assertEqual(sorted(res['file_ids']), sorted(key_fileids_dict[res['key']]))

        print 'add test'
        last_mtime = max(test_mtime)
        t_mtime = last_mtime + 1
        resource = {'file_id': '21', 'mtime': t_mtime, 'download_num': 11,
                            'public': 1, 'main_type': 1, 'file_name': 'test'}
        yield self.c.all_resources.insert(resource)
        res = filename_searcher.scan_from_mongo(last_mtime)
        self.assertEqual(t_mtime, res)
        self.stop()

if __name__ == '__main__':
    #ioloop.IOLoop.instance().run_sync(setup_coro)
    import unittest
    unittest.main()
