# -*- coding: utf-8 -*-
__author__ = 'bone'

import os
import sys
fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from user_upload_log_manager import UserUploadLogManager

from random import randint
import tornado.testing
import tornado.gen
import motor

def mock_uid(user):
    return abs(hash(user))


class UserUploadLogManagerTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=5)
    def test_user_save_log(self):
        db = motor.MotorClient().fbt_test
        user_res_man = UserUploadLogManager(db)

        yield user_res_man.clear_db_just_for_test()
        yield user_res_man.save({"key":"value"}, "test@test.com")
        log_list = yield user_res_man.get_log_list()
        self.assertEqual(len(log_list), 1)

        yield user_res_man.save({"key":"value"}, "test2@test.com")
        log_list = yield user_res_man.get_log_list()
        self.assertEqual(len(log_list), 2)

        log_list = yield user_res_man.get_log_list("test@test.com")
        self.assertEqual(len(log_list), 1)

        log_list = yield user_res_man.get_log_list("test2@test.com")
        self.assertEqual(len(log_list), 1)
        print "test user upload log save over."

if __name__ == '__main__':
    import unittest
    unittest.main()
