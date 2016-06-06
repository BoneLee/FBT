__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(fbt_path)

from test_user_res_cache import FBTUserResourceManager
from coin_manager import CoinManager
from motor import MotorClient
from pymongo import MongoClient
import tornado.gen
import tornado.testing
from time import time, sleep
import simplejson as json
from random import randint, uniform
import tornado.gen
import tornado.testing
import tornado.ioloop
import mock
import redis


def my_cmp(x, y):
    if x[1] == y[1]:
        return cmp(y[0], x[0])
    else:
        return cmp(y[1], x[1])


def mock_file_hash(file_name):
    return str(abs(hash(file_name)))


def gen_file_id(file_hash, file_size):
    return str(file_hash) + "_" + str(file_size)


class FbManagerTestCase(tornado.testing.AsyncTestCase):
    def setUp(self):
        super(FbManagerTestCase, self).setUp()
        db = MotorClient().fbt_test
        mock_redis = redis.StrictRedis()
        CoinManager.instance().set_db_cache(db, mock_redis)

    @tornado.testing.gen_test(timeout=3)
    def test_download(self):
        db = MotorClient().fbt_test  # motorclient.fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    from fb_manager import FBCoinManager
                    print "Mock Ok"
                    FBCoinManager.set_db(db)
                    yield db.users.remove()
                    yield db.coins_of_user.remove()
                    uid_list = range(1, 21)
                    for u in uid_list:
                        yield FBCoinManager.register_ok(u)
                    (his_uid, her_uid) = (1, 2)
                    his_fb = yield FBCoinManager.get_user_total_fb_coin(his_uid)
                    her_fb = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(his_fb, FBCoinManager._coin_rules["register"])
                    self.assertEqual(her_fb, FBCoinManager._coin_rules["register"])

                    users_downloaded_from = [his_uid, her_uid]
                    uid = 3
                    owners_cnt = FBCoinManager._FREE_DOWNLOAD_NUM_BASE_LINE - 1
                    file_size = FBCoinManager.DOWNLOAD_SIZE_PER_FB - 1
                    for download_num in range(FBCoinManager._FREE_DOWNLOAD_NUM_BASE_LINE + 1):
                        yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                          file_size))
                        yield FBCoinManager.public_resource_download_ok(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                         file_size),
                                                                        users_downloaded_from, download_num, owners_cnt)
                        ret2 = yield FBCoinManager.get_user_total_fb_coin(uid)
                        self.assertEqual(ret2, FBCoinManager._coin_rules["register"])

                    download_num = FBCoinManager._FREE_DOWNLOAD_NUM_BASE_LINE + 1
                    yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                      file_size))
                    yield FBCoinManager.public_resource_download_ok(uid,
                                                                    gen_file_id(mock_file_hash("test2.txt"), file_size),
                                                                    users_downloaded_from, download_num, owners_cnt)
                    ret2 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret2, FBCoinManager._coin_rules["register"] - (
                    file_size + FBCoinManager.DOWNLOAD_SIZE_PER_FB - 1) / FBCoinManager.DOWNLOAD_SIZE_PER_FB)

                    his_fb2 = yield FBCoinManager.get_user_total_fb_coin(his_uid)
                    self.assertEqual(his_fb2, his_fb + FBCoinManager._coin_rules["resource_download_by_other"])
                    her_fb2 = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb2, her_fb + FBCoinManager._coin_rules["resource_download_by_other"])

                    download_num = FBCoinManager._MAX_NO_FB_DOWNLOAD_NUM
                    owners_cnt = 2000
                    yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                      file_size))
                    yield FBCoinManager.public_resource_download_ok(uid,
                                                                    gen_file_id(mock_file_hash("test2.txt"), file_size),
                                                                    users_downloaded_from, download_num, owners_cnt)
                    ret3 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret3, ret2 - (
                    file_size + FBCoinManager.DOWNLOAD_SIZE_PER_FB - 1) / FBCoinManager.DOWNLOAD_SIZE_PER_FB)

                    his_fb3 = yield FBCoinManager.get_user_total_fb_coin(his_uid)
                    self.assertEqual(his_fb3, his_fb2 + FBCoinManager._coin_rules["resource_download_by_other"])
                    her_fb3 = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb3, her_fb2 + FBCoinManager._coin_rules["resource_download_by_other"])

                    download_num = FBCoinManager._MAX_NO_FB_DOWNLOAD_NUM + 1
                    owners_cnt = 2000
                    yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                      file_size))
                    yield FBCoinManager.public_resource_download_ok(uid,
                                                                    gen_file_id(mock_file_hash("test2.txt"), file_size),
                                                                    users_downloaded_from, download_num, owners_cnt)
                    ret4 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret4, ret3 - (
                    file_size + FBCoinManager.DOWNLOAD_SIZE_PER_FB - 1) / FBCoinManager.DOWNLOAD_SIZE_PER_FB)

                    his_fb4 = yield FBCoinManager.get_user_total_fb_coin(his_uid)
                    self.assertEqual(his_fb4, his_fb3)
                    her_fb4 = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb4, her_fb3)

                    # test private download
                    yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                      file_size))
                    yield FBCoinManager.public_resource_download_ok(uid, gen_file_id(
                        mock_file_hash("not-exist-or-private-resource.txt"), file_size), users_downloaded_from,
                                                                    download_num, owners_cnt)
                    ret5 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret5, ret4)
                    his_fb5 = yield FBCoinManager.get_user_total_fb_coin(his_uid)
                    self.assertEqual(his_fb5, his_fb4)
                    her_fb5 = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb5, her_fb4)

                    # test fb is zero
                    file_size = FBCoinManager.DOWNLOAD_SIZE_PER_FB * 200
                    for i in range(10):
                        yield FBCoinManager.add_to_public_download_queue(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                          file_size))
                        yield FBCoinManager.public_resource_download_ok(uid, gen_file_id(mock_file_hash("test2.txt"),
                                                                                         file_size),
                                                                        users_downloaded_from, download_num, owners_cnt)
                    ret5 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret5, 0)

    @tornado.testing.gen_test(timeout=3)
    def test_hot_resource(self):
        db = MotorClient().fbt_test  # motorclient.fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    from fb_manager import FBCoinManager
                    from resource_manager import ResourceStoreManager
                    print "mock Ok"
                    FBCoinManager.set_db(db)
                    # test hot resource download 100 times
                    file_name = "test_file.txt"
                    her_uid = 12345
                    yield FBCoinManager.register_ok(her_uid)
                    her_fb = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb, FBCoinManager._coin_rules["register"])
                    ResourceStoreManager.set_db(db)
                    yield ResourceStoreManager.clear_db()
                    file_hash = mock_file_hash(file_name)
                    file_size = 123

                    # mock db and redis
                    FBTUserResourceManager.instance().set_db_cache(db, redis.StrictRedis())

                    yield ResourceStoreManager.user_upload_resource(False, False, her_uid, "her", file_hash, file_name,
                                                                    file_size, True,
                                                                    ["test"], 0, 0, 2, "comments", None)
                    for i in range(100):
                        yield ResourceStoreManager.increase_download_num(file_hash + "_" + str(file_size))
                    her_fb = yield FBCoinManager.get_user_total_fb_coin(her_uid)
                    self.assertEqual(her_fb, FBCoinManager._coin_rules["register"] + FBCoinManager._coin_rules[
                        "hot100_resource"])
                    print "test over."

    @tornado.testing.gen_test(timeout=10)
    def test_fb_vary(self):
        db = MotorClient().fbt_test  # motorclient.fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    from fb_manager import FBCoinManager
                    uid = 1234
                    print "Mock Ok"
                    FBCoinManager.set_db(db)
                    # prepare db
                    yield FBCoinManager.clear_db()
                    for u in [123, 321, 9876, 4321, 1234]:
                        yield db.users.insert({"love_state": "", "uid": u, "phone": "",
                                               "user": "dc0651@163.com", "address": "",
                                               "password": "89fae5422739667c4094399f7c162dbe3120",
                                               "friends": [], "desc": "nothing", "qq": "", "school": "",
                                               "nick_name": "Robin",
                                               "gender": "", "real_name": "", "time": "2014-09-12 19:26",
                                               "icon": "/static/images/user_icon/icon_4.jpg?v=0c7748df3fc91549eeadd0ab36b6fd6c"})
                    ret0 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret0, 0)

                    yield FBCoinManager.register_ok(uid)
                    ret1 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret1, FBCoinManager._coin_rules["register"])

                    FBCoinManager._coin_rules["max_invite_user_cnt"] = 3
                    for i in range(0, FBCoinManager._coin_rules["max_invite_user_cnt"] + 1):
                        yield FBCoinManager.invite_a_user(uid)
                    ret222 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret222,
                                     ret1 + FBCoinManager._coin_rules["max_invite_user_cnt"] *
                                     FBCoinManager._coin_rules[
                                         "invite_a_user"])

                    now = long(time())
                    yield FBCoinManager.user_online_ok(uid, now, now + 3600)
                    ret3 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret3, ret222 + FBCoinManager._coin_rules["online_an_hour"] * 1)

                    yield FBCoinManager.plus_fb(uid, 170)
                    ret4 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret4, ret3 + 170)

                    yield FBCoinManager.user_online_ok(uid, now, now + 3600)
                    ret5 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret5, ret4 + FBCoinManager._coin_rules["online_an_hour"])

                    yield FBCoinManager.user_online_ok(uid, now + 3600, now + 7200)
                    ret6 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret6, ret5 + (1 * FBCoinManager._coin_rules["online_an_hour"]))

                    yield FBCoinManager.focus_us_ok(uid)
                    ret7 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret7, ret6 + FBCoinManager._coin_rules["focus_us"])

                    yield FBCoinManager.focus_us_ok(uid)
                    ret8 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret8, ret7)

                    remote_ip = "1.1.1.1"
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret9 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret9, ret8 + FBCoinManager._coin_rules["sns_share"])

                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret10 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret10, ret9)

                    remote_ip = '2.2.2.2'
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret2 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret2, ret10 + FBCoinManager._coin_rules["sns_share"])

                    # this share is invalid
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret22 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret22, ret2)

                    # share second day
                    sleep(1)
                    FBCoinManager.ONE_DAY = 0.5
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret23 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret23, ret22)

                    remote_ip = '3.3.3.3'
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    ret23 = yield FBCoinManager.get_user_total_fb_coin(uid)
                    self.assertEqual(ret23, ret22 + FBCoinManager._coin_rules["sns_share"])
                    print "test over"

    @tornado.testing.gen_test(timeout=10)
    def test_pass_audit_study_resource(self):
        db = MotorClient().fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    from fb_manager import FBCoinManager
                    FBCoinManager.set_db(db)
                    yield FBCoinManager.clear_db()
                    uid = 1234
                    file_id = "1234_1234"
                    how_many = randint(0, 999)
                    yield FBCoinManager.register_ok(uid)
                    yield FBCoinManager.pass_audit_a_study_res(uid, file_id, how_many)
                    fb = yield FBCoinManager.get_user_total_fb_coin(uid, True)
                    self.assertEqual(fb[0], FBCoinManager._coin_rules["register"]+int(round(how_many)))
                    self.assertEqual(fb[1], int(round(how_many)))

    @tornado.testing.gen_test(timeout=10)
    def test_study_fb_rank(self):
        db = MotorClient().fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    # with mock.patch('redis.StrictRedis.publish') as what_ever3:
                    from fb_manager import FBCoinManager
                    FBCoinManager.set_db(db)
                    yield FBCoinManager.clear_db()
                    ans = []
                    for uid in range(1, 50):
                        file_id = "1234_1234"
                        how_many = uid * 30 + randint(1000, 9999)
                        ans.append((uid, int(round(how_many))))
                        yield FBCoinManager.register_ok(uid)
                        yield FBCoinManager.pass_audit_a_study_res(uid, file_id, how_many)
                    res = yield FBCoinManager.get_total_rank2()
                    ans = sorted(ans, key=lambda x: x[1], reverse=True)
                    for i, fb in enumerate(res):
                        self.assertEqual(res[i][1], ans[i][1])

    @tornado.testing.gen_test(timeout=10)
    def test_study_fb_rank_manager(self):
        db = MotorClient().fbt_test
        sync_db = MongoClient()
        mock_redis = redis.StrictRedis()
        with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever:
            with mock.patch('redis_lru_scheduler.RedisDelegate', mock.MagicMock()) as what_ever2:
                with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
                    from fb_manager import FBCoinManager
                    FBCoinManager.set_db(db)
                    yield FBCoinManager.clear_db()

                    mock_redis.flushdb()
                    from fb_rank_manager import FBRankManager
                    gold_ans = []
                    self.assertListEqual(FBRankManager.get_weekly_top(), gold_ans)
                    self.assertListEqual(FBRankManager.get_monthly_top(), gold_ans)

                    fb_vary = {}
                    for i in range(1, 50):
                        uid = randint(1, 5)
                        delta_fb = uniform(-10, 100)  # a float in range -100,3000

                        found = False
                        delta_fb = int(delta_fb)
                        for i, data in enumerate(gold_ans):
                            if data[0] == uid:
                                gold_ans[i] = (uid, data[1] + delta_fb)
                                found = True
                                break
                        if not found:
                            gold_ans.append((uid, delta_fb))
                        if uid not in fb_vary:
                            fb_vary[uid] = 0
                        fb_vary[uid] += delta_fb

                    for uid, delta_fb in fb_vary.iteritems():
                        yield FBCoinManager.register_ok(uid)
                        yield FBCoinManager.plus_fb(uid, delta_fb)
                    # RedisPubClient().publish(json.dumps(fb_vary))
                    # FBRankManager.fb_vary_processor(json.dumps(fb_vary))
                    self.assertListEqual(FBRankManager.get_weekly_top(), FBRankManager.get_monthly_top())

                    gold_ans.sort(my_cmp)
                    ans2 = list(FBRankManager.get_weekly_top())
                    ans2.sort(my_cmp)
                    self.assertListEqual(ans2, gold_ans[:100])

                    FBRankManager.reset_weekly_fb()
                    ans = list(FBRankManager.get_weekly_top())
                    self.assertListEqual(ans, [])

                    for uid, delta_fb in fb_vary.iteritems():
                        yield FBCoinManager.plus_study_fb(uid, delta_fb)
                    # FBRankManager.study_fb_vary_processor(json.dumps(fb_vary))
                    self.assertListEqual(FBRankManager.get_weekly_top2(), FBRankManager.get_monthly_top2())
                    gold_ans.sort(my_cmp)
                    ans2 = list(FBRankManager.get_weekly_top2())
                    ans2.sort(my_cmp)
                    self.assertListEqual(ans2, gold_ans[:100])
                    print "test fb_rank ok"


if __name__ == '__main__':
    import unittest

    unittest.main()
