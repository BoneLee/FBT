#!/usr/bin/env python
from tornado.test.util import unittest
import tornado.testing
import psutil

def is_process_on(process_name):
    for proc in psutil.process_iter():
        if proc.name == process_name:
            return True
    return False

# check that redis-server and mongodb is open
redis_server_process = "redis-server"
mongodb_server_process = "mongod"

assert is_process_on(redis_server_process), "redis-server not on"
assert is_process_on(mongodb_server_process), "mongodb is not on"

TEST_MODULES = [
    #'test_fb_rank',
    #'test_rank_manager',
    # 'test_redis_pub_sub_client',

    ############## FBT web ################
    'test_redis_db_manager',
    'test_study_resource_manager',
    'test_user_manager',
    'test_comment_manager',
    'test_rating_manager',
]

def all():
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)

if __name__ == '__main__':
    tornado.testing.main()
