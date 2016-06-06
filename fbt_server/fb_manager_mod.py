#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'bone-lee'

from redis_pub_sub_client import RedisPubClient
import logging
from tornado import gen
import motor
from sys import stdout
import simplejson as json
from datetime import datetime, timedelta

class FBCoinManager(object):
    '''
FBT积分规则：
收入：
（1）注册成功，第一次登陆FBT送60个F币
（2）上传和下载私有圈资源（仅好友可见），无需F币
（3）积分大于200的用户，每在线1小时，送10个F币
（4）平台首发优质资源，下载超过100次时，奖励首发用户200F；下载超过500次时，再奖励500F
（5）上传或下载已有资源并保持在线，每被他人成功下载一次，送5F币
（6）举报非法公共资源，被核实后，送50个F币
（7）举报标题和内容不符的公共资源，被核实后，送50个F币
（8）通过社交平台分享fbt链接成功一次送50个F币，每天150封顶
（9）关注我们微博和微信，或加入我们的QQ群，送100个F币
（10）成功推荐身边同学注册FBT(注册时填写推荐人邮箱或姓名)，奖励推荐人100F币，此奖励5000封顶！
支出：
（1）下载一个公共资源扣20个F币
（2）上传的资源标题和内容不符或传错类别，扣除100个F币
（3）上传非法（色情、反动等）公共资源扣除100个F币，情节严重者封号处理!
（4）恶意刷分者，一旦查实，封号处理!
    '''
    public_resource_download_coin = 20
    _ASCENDING = 1
    _DESCENDING = -1
    _sns_share_cache = {}
    _sns_share_cache_update_time = datetime.now()
    ONE_DAY = 24 * 3600
    _MAX_NO_FB_DOWNLOAD_NUM = 1000
    _update_fb_callback = staticmethod(lambda x, y: stdout.write("uid:" + str(x) + " updated coin:" + str(y) + "\n"))
    _user_coin_vary = {}
    _FREE_DOWNLOAD_NUM_BASE_LINE = 10
    _MAX_DOWNLOAD_FB = 50

    _coin_rules = {"register": 200,
                   "online_an_hour": 10,
                   "invite_a_user": 100,
                   "hot100_resource": 200,
                   "hot500_resource": 500,
                   "online_plus_fb_line": 200,
                   "resource_download_by_other": 1,
                   "resource_download_by_before_10": 0,
                   "download_a_public_resource": -public_resource_download_coin,
                   "sns_share": 50,
                   "max_invite_user_cnt": 50,
                   "tip_off": 5,
                   "focus_us": 100}

    _db = motor.MotorClient('localhost', 27017).fbt

    @classmethod
    def set_db(cls, db):
        cls._db = db

    @classmethod
    def is_free_day(cls):
        FREE_DAY_DEAD_LINE = datetime(year=2015,month=4,day=1)
        return datetime.now() < FREE_DAY_DEAD_LINE


    @classmethod
    def is_function(cls, f):
        return hasattr(f, '__call__')

    @classmethod
    def set_update_fb_callback(cls, callback):
        assert cls.is_function(callback)
        cls._update_fb_callback = callback

    @classmethod
    @gen.coroutine
    def clear_db(cls):
        yield cls._db.coins_of_user.remove()

    @classmethod
    @gen.coroutine
    def register_ok(cls, uid):
        uid = long(uid)
        assert (uid > 0)
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if not coin:
            # fblog
            yield cls._db.fblog.insert({'uid': uid, 'online_time': 0, 'log': [
                {'date': datetime.now(), 'coin': cls._coin_rules["register"], 'info': 'register'}]})
            yield cls._db.coins_of_user.insert({'uid': uid, 'total_coins': cls._coin_rules["register"]})

    @classmethod
    @gen.coroutine
    def user_online_ok(cls, uid, online_at, offline_at):
        assert online_at > 0 and offline_at > 0 and offline_at > online_at
        uid = long(uid)
        assert uid > 0
        online_hour = (offline_at - online_at) / 3600.0  # long(time()) return seconds
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"total_coins":1})
        if coin:
            if "total_coins" in coin and coin["total_coins"] >= cls._coin_rules["online_plus_fb_line"]:
                cls.update_coin_db(coin, uid, online_hour * cls._coin_rules["online_an_hour"])
                # coin["total_coins"]+=online_hour*cls._coin_rules["online_an_hour"]
                # fblog
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": online_hour * cls._coin_rules["online_an_hour"],
                        "info": "online:" + str(online_at) + "-" + str(offline_at) + " coin:" + str(
                            coin["total_coins"])}},
                                                          "$inc": {"online_time": online_hour}})
                # yield cls._db.coins_of_user.save(coin)
        else:
            logging.info("Warning: uid not in coin db. uid:" + str(uid))

    @classmethod
    @gen.coroutine
    def focus_us_ok(cls, uid):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            if "focus_us" in coin:
                if not coin["focus_us"]:
                    coin["focus_us"] = True
                    cls.update_coin(coin, uid, cls._coin_rules["focus_us"])
                    # fblog
                    yield cls._db.fblog.update({'uid': uid}, {"$push": {
                    "log": {"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                            "info": "focus_us coin:" + str(coin["total_coins"])}}})
                    # coin["total_coins"]+=cls._coin_rules["focus_us"]
                else:
                    logging.info("duplicated focus us uid:" + str(uid))
            else:
                coin["focus_us"] = True
                cls.update_coin(coin, uid, cls._coin_rules["focus_us"])
                # fblog
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                        "info": "focus_us coin:" + str(coin["total_coins"])}}})
                # coin["total_coins"]+=cls._coin_rules["focus_us"]
            yield cls._db.coins_of_user.save(coin)
        else:
            logging.info("Warning: uid not in coin db. uid:" + str(uid))

    @classmethod
    @gen.coroutine
    def add_to_public_download_queue(cls, uid, file_id, dir_id=None):
        uid = long(uid)
        assert uid > 0
        if dir_id:
            store_file_id = '+'.join([dir_id, file_id])
            yield cls._db.coins_of_user.update({"uid": uid}, {"$addToSet": {"public_download_queue": store_file_id}},
                                               True)
        else:
            yield cls._db.coins_of_user.update({"uid": uid}, {"$addToSet": {"public_download_queue": file_id}}, True)

    @classmethod
    @gen.coroutine
    def public_resource_download_ok(cls, uid, file_id, users_downloaded_from, download_num, owners_cnt, dir_id=None):
        uid = long(uid)
        assert uid > 0
        assert len(users_downloaded_from) > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin and "public_download_queue" in coin:
            if dir_id:
                store_file_id = '+'.join([dir_id, file_id])
                fid = store_file_id
            else:
                fid = file_id
            if fid in coin["public_download_queue"]:
                coin["public_download_queue"].remove(fid)
                if download_num > cls._FREE_DOWNLOAD_NUM_BASE_LINE: # and not cls.is_free_day():
                    minus_fb = -owners_cnt
                    if (-minus_fb) > cls._MAX_DOWNLOAD_FB:
                        minus_fb = -cls._MAX_DOWNLOAD_FB
                    yield cls._db.fblog.update({'uid': uid}, {"$push": {
                    "log": {"date": datetime.now(), "coin":  minus_fb,
                            "info": "download_a_public_resource:" + fid + " coin:" + str(coin["total_coins"])}}})
                    cls.update_coin(coin, uid, minus_fb);
                yield cls._db.coins_of_user.save(coin)
                if cls._FREE_DOWNLOAD_NUM_BASE_LINE < download_num <= cls._MAX_NO_FB_DOWNLOAD_NUM:
                    for user in users_downloaded_from:
                        yield cls.plus_fb(user, cls._coin_rules["resource_download_by_other"])
                        yield cls._db.fblog.update({'uid': user}, {"$push": {
                            "log": {"date": datetime.now(), "coin": cls._coin_rules["resource_download_by_other"],
                                    "info": "resource_download_by_other:" + fid + " coin:" + str(
                                        coin["total_coins"])}}})
        else:
            logging.info("Warning: logic err. uid or public_download_queue not in coin db.")

    @classmethod
    @gen.coroutine
    def sns_share_ok(cls, uid_of_shared_person):
        diff_time = datetime.now() - FBCoinManager._sns_share_cache_update_time
        if diff_time > timedelta(seconds=cls.ONE_DAY):
            FBCoinManager._sns_share_cache_update_time += timedelta(days=1)
            FBCoinManager._sns_share_cache = {}
        uid_of_shared_person = long(uid_of_shared_person)
        assert uid_of_shared_person > 0
        MAX_SHARE_TIME_ONE_DAY = 1
        if uid_of_shared_person in FBCoinManager._sns_share_cache:
            if FBCoinManager._sns_share_cache[uid_of_shared_person] >= MAX_SHARE_TIME_ONE_DAY:
                return
        else:
            FBCoinManager._sns_share_cache[uid_of_shared_person] = 0
        FBCoinManager._sns_share_cache[uid_of_shared_person] += 1
        coin = yield cls._db.coins_of_user.find_one({'uid': uid_of_shared_person},{"total_coins":1})
        if coin:
            # if "sns_share_times" in coin:
            #     coin["sns_share_times"] += 1
            # else:
            #     coin["sns_share_times"] = 1
            yield cls._db.coins_of_user.update({'uid': uid_of_shared_person},{"$inc":{"sns_share_times":1}})
            yield cls._db.fblog.update({'uid': uid_of_shared_person}, {"$push": {
            "log": {"date": datetime.now(), "coin": cls._coin_rules["sns_share"],
                    "info": "sns_share coin:" + str(coin["total_coins"])}}})
            cls.update_coin_db(coin, uid_of_shared_person, cls._coin_rules["sns_share"])
            # yield cls._db.coins_of_user.save(coin)
        else:
            logging.info("Warning: logic err. uid not in coin db.")


    @classmethod
    @gen.coroutine
    def get_user_total_fb_coin(cls, uid):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"total_coins":1})
        if coin and "total_coins" in coin:
            raise gen.Return(int(round(coin["total_coins"])))
        else:
            raise gen.Return(0)

    @classmethod
    @gen.coroutine
    def plus_fb(cls, uid, how_many):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"total_coins":1})
        if coin and "total_coins" in coin:
            # coin["total_coins"]+=how_many
            #if coin["total_coins"]<0:
            #    coin["total_coins"]=0
            cls.update_coin_db(coin, uid, how_many)
            # yield cls._db.coins_of_user.save(coin)

    @classmethod
    @gen.coroutine
    def get_total_rank(cls):
        cursor = cls._db.coins_of_user.find({}).sort([('total_coins', cls._DESCENDING), ]).limit(200)
        ans = []
        while (yield cursor.fetch_next):
            coin = cursor.next_object()
            ans.append((coin['uid'], int(coin['total_coins'])))
        raise gen.Return(ans)


    @classmethod
    @gen.coroutine
    def invite_a_user(cls, uid):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"invite_user_cnt":1})
        if coin:
            if "invite_user_cnt" not in coin:
                coin["invite_user_cnt"] = 0
            if coin["invite_user_cnt"] < cls._coin_rules["max_invite_user_cnt"]:
                # coin["invite_user_cnt"] += 1
                # yield cls._db.coins_of_user.save(coin)
                yield cls._db.coins_of_user.update({"uid":uid},{"$inc":{"max_invite_user_cnt":1}})
                # fblog
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": cls._coin_rules["invite_a_user"],
                        "info": "invite_a_user coin:" + str(coin["total_coins"])}}})
                yield cls.plus_fb(uid, cls._coin_rules["invite_a_user"])

    @classmethod
    @gen.coroutine
    def hot100_resource(cls, uid, file_id):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"total_coins":1})
        if coin:
            yield cls.plus_fb(uid, cls._coin_rules["hot100_resource"])
            yield cls._db.fblog.update({'uid': uid}, {"$push": {
            "log": {"date": datetime.now(), "coin": cls._coin_rules["hot100_resource"],
                    "info": "hot100_resource:" + file_id + " coin:" + str(coin["total_coins"])}}})

    @classmethod
    @gen.coroutine
    def hot500_resource(cls, uid, file_id):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid},{"total_coins":1})
        if coin:
            yield cls.plus_fb(uid, cls._coin_rules["hot500_resource"])
            yield cls._db.fblog.update({'uid': uid}, {"$push": {
            "log": {"date": datetime.now(), "coin": cls._coin_rules["hot500_resource"],
                    "info": "hot500_resource:" + file_id + " coin:" + str(coin["total_coins"])}}})

    @classmethod
    def update_coin_db(cls, coin, uid, delta_fb):
        cls.update_coin(coin, uid, delta_fb)
        yield cls._db.coins_of_user.update({'uid': uid},{"$inc":{"total_coins":delta_fb }})

    @classmethod
    def update_coin(cls, coin, uid, delta_fb):
        uid = long(uid)
        assert "total_coins" in coin
        origin_coin = coin["total_coins"]
        coin["total_coins"] += delta_fb
        if coin["total_coins"] < 0:
            coin["total_coins"] = 0
            delta_fb = -origin_coin
        if uid not in cls._user_coin_vary:
            cls._user_coin_vary[uid] = 0
        cls._user_coin_vary[uid] += delta_fb
        # print "send coin update...",cls._user_coin_vary
        MAX_VARY_CNT = 10
        if len(cls._user_coin_vary) >= MAX_VARY_CNT:
            RedisPubClient().publish(json.dumps(cls._user_coin_vary))
            cls._user_coin_vary = {}

            # if cls.is_function(cls._update_fb_callback):
            #     cls._update_fb_callback(uid,coin["total_coins"])
            # FBRankManager.update_fb(uid,int(delta_fb))

            # @classmethod
            # @gen.coroutine
            # def tip_off_add(cls, uid,file_hash):
            #     assert uid > 0
            #     coin = yield cls._db.coins_of_user.find_one({'uid': uid})
            #     yield cls._db.fblog.update({'uid' : uid},{"$push":{"log":{"date":datetime.now(),"coin":FBCoinManager._coin_rules["tip_off"],"info":"tip_off_add:"+str(file_hash)+" coin:"+str(coin["total_coins"])}}})
            #     cls.plus_fb(uid, FBCoinManager._coin_rules["tip_off"])

            # @classmethod
            # @gen.coroutine
            # def tip_off_sub(cls, uid,file_hash):
            #     assert uid > 0
            #     coin = yield cls._db.coins_of_user.find_one({'uid': uid})
            #     yield cls._db.fblog.update({'uid' : uid},{"$push":{"log":{"date":datetime.now(),"coin":-FBCoinManager._coin_rules["tip_off"],"info":"tip_off_sub:"+str(file_hash)+" coin:"+str(coin["total_coins"])}}})
            #     cls.plus_fb(uid, -FBCoinManager._coin_rules["tip_off"])

