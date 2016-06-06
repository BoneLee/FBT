#!/usr/bin/env python
from tornado.test.util import unittest
import tornado.testing
import psutil
import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

def is_process_on(process_name):
    for proc in psutil.process_iter():
        if process_name in str(proc.name): # == process_name:
            return True
    return False

# check that redis-server and mongodb is open
redis_server_process = "redis-server"
mongodb_server_process = "mongod"

assert is_process_on(redis_server_process), "redis-server not on"
assert is_process_on(mongodb_server_process), "mongodb is not on"

TEST_MODULES = [
    'test_async',  # teach you how to write tornado unit test
    'test_mock',  # teach you how to mock constant

    # fbt
    'test_util',
    'test_fb_manager',
    'test_fb_rank',
    'test_fb_rank_timer',
    'test_download',
    'test_redis_pub_sub_client',
    # 'test_search_resources',
    # 'test_async_lru',

    ############## xiaoyuanxingkong ################
    'test_redis_db_manager',
    'test_study_resource_manager',
    'test_user_resource_manager',
    'test_comment_manager',
    'test_rating_manager',
    'test_university_db',
    'test_reward_study',
    'test_user_msg_center',
    'test_address',
    'test_session_manager',
    'test_user_upload_log_manager',
    'test_user_ip_cache',
    'test_redis_proxy',
    'test_user_res_cache',
    'test_coin_manager',
    'test_coin_collector',
    # 'test_question_manager',
    'test_experience_tag_manager',
    'test_mail_manager',
    # can not put together
    'test_user_manager',
    'test_experience_manager',
    'test_chat',
    'test_es_search',
]

def all():
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)

if __name__ == '__main__':
    tornado.testing.main()
