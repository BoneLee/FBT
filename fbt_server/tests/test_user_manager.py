# -*- coding: utf-8 -*-
__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(fbt_path)

#################################################################
######  mock redis locally ##########
# import constant
# constant.REDIS_MASTER_HOST = "127.0.0.1"
# constant.REDIS_PORT = (6379, 6379, 6379, 6379, 6379, 6379)
# constant.REDIS_PWD = (None, None, None, None, None, None)
#################################################################

from es_mapping import user_none_analyze_fields, user_analyze_fields
from university_course_manager import RedisDBManager
from university_db import UniversityDB
import constant
from tornado.escape import utf8
from tornado.gen import coroutine

from tornado import testing
from time import sleep
import motor
import redis
import mock


class MockHotBorad(object):
    def __init__(self, db, ioloop):
        pass

    def __getattr__(self, attr_name):
        return self.mock_any_method

    def mock_any_method(self, *args, **kwargs):
        # such as folows
        pass


class UserManagerTestCase(testing.AsyncTestCase):
    def setUp(self):
        super(UserManagerTestCase, self).setUp()
        from users_manager import UserManager
        db = motor.MotorClient().fbt_test  # motorclient.fbt_test
        redis_db = redis.StrictRedis()
        redis_cache = redis.StrictRedis()
        redis_db.flushdb()
        redis_cache.flushdb()
        redis_db_man = RedisDBManager(redis_db, redis_cache)
        self.user_manager = UserManager(db, redis_cache, redis_db_man, es_host="localhost", es_port=9200)
        self.io_loop.run_sync(self.fixture_setup)

    @coroutine
    def fixture_setup(self):
        yield self.user_manager.clear_search_db()

    def test_generate_user_icon(self):
            from users_manager import UserManager
            for i in range(100):
                random_num = UserManager.generate_user_icon()
                assert 1 <= int(random_num) <= 36

    def test_generate_uid(self):
            from users_manager import UserManager
            uid_set = set()
            for i in range(3):
                sleep(1)
                uid = UserManager.generate_uid("bone@test.com")
                assert uid not in uid_set
                uid_set.add(uid)

    def test_salt_passwd(self):
            from users_manager import UserManager
            salt_passwd = UserManager.generate_salt_passwd("bone@test.com", "123")
            for i in range(100):
                sleep(0.0001 * i)
                salt_passwd2 = UserManager.generate_salt_passwd("bone@test.com", "123")
                assert salt_passwd == salt_passwd2

    # def test_gen_session_id(self):
    #     uid_set = set()
    #     for i in range(100):
    #         sid = UserManager.generate_session_id()
    #         assert sid not in uid_set
    #         uid_set.add(sid)

    @testing.gen_test
    def test_user_change_password(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager

            yield db.users.remove({})
            user = "test@test.com"
            passwd, user_icon_url, real_name, school, college, nick, gender = "123", "NOT SET", "bone", "NOT SET", "NOT SET", "bonelee", "MALE"
            yield user_manager.register_user(user, passwd, user_icon_url, real_name, school, college, nick, gender)
            user_db = yield user_manager.find_user(user)
            self.assertEqual(user_db["user"], user)
            self.assertEqual(user_db["password"], user_manager.generate_salt_passwd(user, passwd))

            new_passwd = "bone"
            yield user_manager.user_chg_password(user, new_passwd)
            user_db = yield user_manager.find_user(user)
            self.assertEqual(user_db["user"], user)
            self.assertEqual(user_db["password"], user_manager.generate_salt_passwd(user, new_passwd))
            self.stop()

    @testing.gen_test
    def test_user_change_college(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager

            yield db.users.remove({})
            user = "test@test.com"
            passwd, user_icon_url, real_name, school, college, nick, gender = "123", "NOT SET", "bone", "NOT SET", "NOT SET", "bonelee", "MALE"
            yield user_manager.register_user(user, passwd, user_icon_url, real_name, school, college, nick, gender)
            user_db = yield user_manager.find_user(user)
            self.assertEqual(user_db["university"], "NOT SET")
            self.assertEqual(user_db["college"], "NOT SET")

            university = u"测试的学校"
            college = u"测试的学苑"
            ok = yield user_manager.change_college(user, university, college)
            self.assertTrue(ok)
            user_db = yield user_manager.find_user(user)
            self.assertEqual(user_db["university"], university)
            self.assertEqual(user_db["college"], college)

    @testing.gen_test(timeout=10)
    def test_user_change_info(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager

            yield db.users.remove({})
            user = "test@test.com"
            passwd, user_icon_url, real_name, school, college, nick, gender = "123", "NOT SET", "bone", "NOT SET", "NOT SET", "bonelee", "MALE"
            yield user_manager.register_user(user, passwd, user_icon_url, real_name, school, college, nick, gender)

            ret = yield user_manager.get_user_info(user)
            self.assertEqual(ret["university"], school)
            self.assertEqual(ret["college"], college)
            self.assertEqual(ret["gender"], gender)
            self.assertEqual(ret["real_name"], real_name)

            university = u"测试的学校2"
            college = u"测试的学苑2"
            gender = u"男"
            real_name = u"甲壳虫"
            nick_name = u"kaka"
            yield user_manager.change_user_info(user, university, college, gender, real_name, nick_name)
            ret = yield user_manager.get_user_info(user)
            self.assertEqual(ret["university"], university)
            self.assertEqual(ret["college"], college)
            self.assertEqual(ret["gender"], gender)
            self.assertEqual(ret["real_name"], real_name)
            self.assertEqual(ret["nick_name"], nick_name)

            # TODO fix me @先斌
            import time
            time.sleep(8)
            total_page, cur_page, users_list = yield user_manager.search_user(u"测试学校", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["user"], user)

    @testing.gen_test
    def test_user_tag(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager

            yield db.users.remove({})
            user = "test@test.com"
            # passwd, user_icon_url, real_name, school, college, nick, gender = "123", "NOT SET", "bone", "NOT SET", "NOT SET", "bonelee", "MALE"
            # yield user_manager.register_user(user, passwd, user_icon_url, real_name, school, college, nick, gender)
            # tags = ["我","你","他","他"]
            tags = ["考研:我", "考研:你", "考研:我", "考研:他"]
            uid = 12124
            yield user_manager.insert_my_tags(user, uid, tags)

            cnt = yield user_manager.get_post_num_by_tag(user, "考研")
            self.assertEqual(cnt, len(tags) - 1)
            cnt = yield user_manager.get_post_num_by_tag(user, u"考研")
            self.assertEqual(cnt, len(tags) - 1)

            tags = yield user_manager.get_my_tags(user)
            self.assertEqual(len(tags), 3)
            user_info = yield user_manager.get_user_info(user)
            self.assertTrue(u"考研:我" in user_info["tags"])
            self.assertTrue(u"考研:你" in user_info["tags"])
            self.assertTrue(u"考研:他" in user_info["tags"])

    @testing.gen_test
    def test_user_interested_tag(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager

            yield db.users.remove({})
            user = "test@test.com"
            tags = yield user_manager.get_my_interested_tags(user)
            self.assertSetEqual(tags, set())

            my_tags = ["考研:我", "考研:你", "考研:我", "考研:他"]
            for tag in my_tags:
                yield user_manager.insert_my_interested_tags(user, tag)
            tags = yield user_manager.get_my_interested_tags(user)
            tags2 = yield user_manager.get_my_interested_tags(user, True)
            self.assertSetEqual(tags, tags2)
            self.assertTrue("考研:我" in tags)
            self.assertTrue("考研:你" in tags)
            self.assertTrue("考研:他" in tags)
            for tag in my_tags:
                yield user_manager.remove_my_interested_tags(user, tag)
            tags = yield user_manager.get_my_interested_tags(user)
            tags2 = yield user_manager.get_my_interested_tags(user, True)
            self.assertSetEqual(tags, tags2)
            self.assertSetEqual(tags, set())

    @testing.gen_test(timeout=20)
    def test_inc_thanks_coin(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            yield user_manager.inc_thanks_coin(user, 100)
            user_info = yield user_manager.find_user(user, True)
            self.assertEqual(user_info["thanks_coin"], 100)

    @testing.gen_test(timeout=200)
    def test_user_follow(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            follower = "test2@test.com"
            yield user_manager.register_user(user, "password", "user_icon", "王大锤", "school", "college", "nick",
                                             "M")
            follower1 = yield user_manager.get_followers(user)
            follower2 = yield user_manager.get_followers(follower)
            self.assertSetEqual(follower1, set())
            self.assertSetEqual(follower2, set())
            follower1 = yield user_manager.get_followers(user, False)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set())
            self.assertSetEqual(follower2, set())
            yield user_manager.follow(user, follower)
            follower1 = yield user_manager.get_followers(user)
            follower2 = yield user_manager.get_followers(follower)
            self.assertSetEqual(follower1, set([follower]))
            self.assertSetEqual(follower2, set())
            follower1 = yield user_manager.get_followers(user, False)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set([follower]))
            self.assertSetEqual(follower2, set())

            another_follower = "tet@tet.com"
            yield user_manager.follow(user, another_follower)
            user2 = "test333@test.com"
            yield user_manager.register_user(user2, "password", "user_icon", "李二毛", "school", "college", "nick",
                                             "M")
            yield user_manager.follow(user2, another_follower)

            following_users = yield user_manager.get_following_users(another_follower)
            self.assertEqual(following_users[0]["user"], user2)
            self.assertEqual(following_users[1]["user"], user)

            follower1 = yield user_manager.get_followers(user)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set([follower, another_follower]))
            self.assertSetEqual(follower2, set())
            follower1 = yield user_manager.get_followers(user, False)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set([follower, another_follower]))
            self.assertSetEqual(follower2, set())

            yield user_manager.unfollow(user, another_follower)
            follower1 = yield user_manager.get_followers(user)
            follower2 = yield user_manager.get_followers(follower)
            self.assertSetEqual(follower1, set([follower]))
            self.assertSetEqual(follower2, set())
            follower1 = yield user_manager.get_followers(user, False)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set([follower]))
            self.assertSetEqual(follower2, set())

            yield user_manager.unfollow(user, follower)
            follower1 = yield user_manager.get_followers(user)
            follower2 = yield user_manager.get_followers(follower)
            self.assertSetEqual(follower1, set())
            self.assertSetEqual(follower2, set())
            follower1 = yield user_manager.get_followers(user, False)
            follower2 = yield user_manager.get_followers(follower, False)
            self.assertSetEqual(follower1, set())
            self.assertSetEqual(follower2, set())

    @testing.gen_test(timeout=200)
    def test_search_user(self):
        # clean index

            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            uid = yield user_manager.register_user(user, "password", "user_icon", "李智华", "good中国科学院大学", "研究生院", "nick", "M")
            yield user_manager.insert_my_tags(user, uid, ["考研:计算机", "留学:美国"])
            total_page, cur_page, users_list = yield user_manager.search_user("研究生院", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            total_page, cur_page, users_list = yield user_manager.search_user("李智华", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            total_page, cur_page, users_list = yield user_manager.search_user("美国研究生", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            total_page, cur_page, users_list = yield user_manager.search_user("留学研究生", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            total_page, cur_page, users_list = yield user_manager.search_user("good", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            total_page, cur_page, users_list = yield user_manager.search_user("good留学研究生", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)

            user2 = "test2@test.com"
            uid2 = yield user_manager.register_user(user2, "password", "user_icon", "real_name", "北京大学", "研究生院", "nick", "M")
            # ik不能把北京大学拆成北大，用这个语句可知
            # ik curl -XPOST http://localhost:9200/index/_analyze?analyzer=ik  -d'北京大学'
            total_page, cur_page, users_list = yield user_manager.search_user("北大", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid2)

            total_page, cur_page, users_list = yield user_manager.search_user("美国研究生", 1)
            self.assertEqual(total_page, 1)
            self.assertEqual(cur_page, 1)
            self.assertEqual(users_list[0]["uid"], uid)
            print "test search by university short name passed"

    @testing.gen_test(timeout=2)
    def test_auth_user(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            tag_class = u"考研"
            yield user_manager.register_user(user, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick", "M")
            user_info = yield user_manager.find_user(user)
            self.assertTrue(constant.STAR_CLASS[tag_class] not in user_info)
            yield user_manager.set_star_user(user, tag_class)
            user_info = yield user_manager.find_user(user)
            self.assertEqual(user_info[constant.STAR_CLASS[tag_class]], 1)
            self.assertEqual(user_info["university"], u"中国科学院大学")
            self.assertEqual(user_info["nick_name"], "nick")
            user_info = yield user_manager.get_user_info(user)
            self.assertEqual(user_info[constant.STAR_CLASS[tag_class]], 1)
            self.assertEqual(user_info["university"], u"中国科学院大学")
            self.assertEqual(user_info["nick_name"], "nick")

            yield user_manager.unset_star_user(user, tag_class)
            user_info = yield user_manager.find_user(user)
            self.assertTrue(constant.STAR_CLASS[tag_class] not in user_info)

    @testing.gen_test(timeout=2)
    def test_set_star_user_info(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            yield user_manager.register_user(user, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick", "M")
            user_info = yield user_manager.find_user(user)
            university, college = UniversityDB().random_choose_college_of_university()
            degree = "doctor"
            entrance_year = 2012
            self.assertTrue("degree" not in user_info)
            self.assertTrue("entrance_year" not in user_info)
            yield user_manager.set_star_user_info(user, university, college, degree, entrance_year)
            user_info = yield user_manager.find_user(user)
            self.assertEqual(utf8(user_info["university"]), university)
            self.assertEqual(utf8(user_info["college"]), college)
            self.assertEqual(user_info["degree"], degree)
            self.assertEqual(user_info["entrance_year"], entrance_year)
            user_info = yield user_manager.get_user_info(user)
            self.assertEqual(utf8(user_info["university"]), university)
            self.assertEqual(utf8(user_info["college"]), college)
            self.assertEqual(user_info["degree"], degree)
            self.assertEqual(user_info["entrance_year"], entrance_year)

    @testing.gen_test(timeout=2)
    def test_get_top_star_users(self):
            db = motor.MotorClient().fbt_test  # motorclient.fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            user = "test@test.com"
            tag_class = u"考研"
            yield user_manager.register_user(user, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick", "M")
            top_users = yield user_manager.get_top_star_users()
            self.assertEqual(len(top_users), 6)
            self.assertEqual(len(top_users[tag_class]), 0)

            yield user_manager.set_star_user(user, tag_class)
            top_users = yield user_manager.get_top_star_users()
            self.assertEqual(len(top_users), 6)
            self.assertEqual(len(top_users[tag_class]), 1)
            self.assertEqual(top_users[tag_class][0]["user"], user)
            user2 = "test2@test.com"
            tag_class = u"考研"
            yield user_manager.register_user(user2, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick",
                                             "M")
            yield user_manager.set_star_user(user2, tag_class)
            yield user_manager.inc_thumb_num(user2)
            top_users = yield user_manager.get_top_star_users(False)
            self.assertEqual(len(top_users), 6)
            self.assertEqual(len(top_users[tag_class]), 2)
            self.assertEqual(top_users[tag_class][0]["user"], user2)

            user3 = "test3@test.com"
            tag_class = u"留学"
            yield user_manager.register_user(user3, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick",
                                             "M")
            yield user_manager.set_star_user(user3, tag_class)
            top_users = yield user_manager.get_top_star_users(False)
            self.assertEqual(len(top_users), 6)
            self.assertEqual(len(top_users[tag_class]), 1)
            self.assertEqual(top_users[tag_class][0]["user"], user3)

    @testing.gen_test(timeout=2)
    def test_get_today_registered_users(self):
            db = motor.MotorClient().fbt_test
            user_manager = self.user_manager
            yield db.users.remove({})
            yield db.followers.remove({})
            top_users = yield user_manager.get_today_users()
            self.assertEqual(len(top_users), 0)
            user = "test@test.com"
            tag_class = u"考研"
            yield user_manager.register_user(user, "password", "user_icon", "real_name", "中国科学院大学", "研究生院", "nick", "M")
            top_users = yield user_manager.get_today_users()
            self.assertEqual(len(top_users), 1)
            print "get today user passed test"


if __name__ == '__main__':
    import unittest

    unittest.main()
