__author__ = 'bone'

import os, sys

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from fbt_user_res_manager import FBTUserResourceManager

import tornado.testing
from time import time
import tornado.gen
import redis
import motor


class UserResManagerTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=3)
    def test_add_resource(self):
        r = redis.StrictRedis()
        r.flushdb()
        db = motor.MotorClient().test_fbt
        cache = FBTUserResourceManager(db=db, cache=r)
        yield cache.get_collection().remove({})
        uid = 1234
        res_list = yield cache.get_resource_of_user(uid)
        self.assertEqual(res_list, [])

        file_id1="1234_4321"
        file_id2="4321_1234"
        file_id3="5678_8765"
        yield cache.add_to_my_resource_list(uid, file_id1)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id1])

        yield cache.add_to_my_resource_list(uid, file_id2)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id2, file_id1])

        yield cache.add_to_my_resource_list(uid, file_id3)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

        # test rebuild resources from db
        r.flushdb()
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

    @tornado.testing.gen_test(timeout=3)
    def test_add_resources(self):
        r = redis.StrictRedis()
        r.flushdb()
        db = motor.MotorClient().test_fbt
        cache = FBTUserResourceManager(db=db, cache=r)
        yield cache.get_collection().remove({})
        uid = 1234
        res_list = yield cache.get_resource_of_user(uid)
        self.assertEqual(res_list, [])

        file_id1="1234_4321"
        file_id2="4321_1234"
        file_id3="5678_8765"
        yield cache.add_file_in_dir_to_my_resource_list(uid, [file_id1, file_id2, file_id3])
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

        # test rebuild resources from db
        r.flushdb()
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

    @tornado.testing.gen_test(timeout=6)
    def test_rm_resources(self):
        r = redis.StrictRedis()
        r.flushdb()
        db = motor.MotorClient().test_fbt
        cache = FBTUserResourceManager(db=db, cache=r)
        yield cache.get_collection().remove({})
        uid = 1234
        file_id1="1234_4321"
        file_id2="4321_1234"
        file_id3="5678_8765"
        yield cache.add_file_in_dir_to_my_resource_list(uid, [file_id1, file_id2, file_id3])
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

        yield cache.remove_from_my_resource_list(uid, file_id2)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id1])

        # test rebuild resources from db
        r.flushdb()
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id1])

        # yield cache.add_file_in_dir_to_my_resource_list(uid, [file_id1, file_id3])
        # res_list = yield cache.get_resource_of_user(uid)
        yield cache.remove_from_my_resource_list(uid, file_id1)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3])

        yield cache.remove_from_my_resource_list(uid, file_id3)
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [])

        yield cache.remove_from_my_resource_list(uid, "file_id3 not exist")
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [])

        # test rebuild resources from db
        r.flushdb()
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [])

    @tornado.testing.gen_test(timeout=6)
    def test_expire(self):
        r = redis.StrictRedis()
        r.flushdb()
        db = motor.MotorClient().test_fbt
        cache = FBTUserResourceManager(db=db, cache=r)
        yield cache.get_collection().remove({})
        uid = 1234
        file_id1="1234_4321"
        file_id2="4321_1234"
        file_id3="5678_8765"
        cache.EXPIRE_TIME = 1
        yield cache.add_file_in_dir_to_my_resource_list(uid, [file_id1, file_id2, file_id3])
        res_list = yield cache.get_resource_of_user(uid)
        self.assertListEqual(res_list, [file_id3, file_id2, file_id1])

        @tornado.gen.coroutine
        def res_list_check2():
            res_list = yield cache.get_resource_of_user(uid)
            self.assertListEqual(res_list, [file_id3, file_id2, file_id1])
            print "test expire Ok"
            self.stop()

        def res_list_check():
            # process.nextTick
            self.io_loop.add_future(res_list_check2(), lambda f: True)

        self.io_loop.add_timeout(time() + 1.1, res_list_check)
        self.wait()



if __name__ == '__main__':
    import unittest
    unittest.main()