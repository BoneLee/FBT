# -*- coding: utf-8 -*-
__author__ = 'bone'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from pymongo import MongoClient
import tornado.testing

_db = MongoClient().fbt_test

SNS_SHARE_COIN = 50

def update_coin(coin, uid, delta_fb):
        assert "total_coins" in coin
        coin["total_coins"] += delta_fb
        if coin["total_coins"] < 0:
            coin["total_coins"] = 0

def sns_share_ok(uid_of_shared_person, remote_ip):
        assert remote_ip
        uid_of_shared_person = long(uid_of_shared_person)
        assert uid_of_shared_person > 0
        coin = _db.coins_of_user.find_one({'uid': uid_of_shared_person})
        if coin:
            if "sns_clicked_ip" not in coin:
                coin["sns_clicked_ip"]=[]
            if remote_ip not in coin["sns_clicked_ip"]:
                coin["sns_clicked_ip"].append(remote_ip)
                if "sns_share_times" in coin:
                    coin["sns_share_times"] += 1
                else:
                    coin["sns_share_times"] = 1
                update_coin(coin, uid_of_shared_person, SNS_SHARE_COIN)
                _db.coins_of_user.save(coin)

class UserResourceManagerTestCase(tornado.testing.AsyncTestCase):
    def test_download_and_overview(self):
        _db.coins_of_user.remove({})
        uid = 123
        _db.coins_of_user.insert({"uid": uid, "total_coins": 0})

        coin = _db.coins_of_user.find_one({"uid": uid}, {"total_coins":1})
        self.assertEqual(coin["total_coins"], 0)

        sns_share_ok(uid, "1.1.1.1")
        coin = _db.coins_of_user.find_one({"uid": uid}, {"total_coins":1})
        self.assertEqual(coin["total_coins"], SNS_SHARE_COIN)

        sns_share_ok(uid, "1.1.1.2")
        coin = _db.coins_of_user.find_one({"uid": uid}, {"total_coins":1})
        self.assertEqual(coin["total_coins"], SNS_SHARE_COIN*2)

        sns_share_ok(uid, "1.1.1.2")
        coin = _db.coins_of_user.find_one({"uid": uid}, {"total_coins":1})
        self.assertEqual(coin["total_coins"], SNS_SHARE_COIN*2)
        print "test over."

if __name__ == '__main__':
    import unittest
    unittest.main()
