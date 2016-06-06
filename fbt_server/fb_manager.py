#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'bone-lee'

from redis_cache_client import RedisCacheClient
from coin_manager import CoinManager
import logging
from tornado import gen
from datetime import datetime
import motorclient
from redis_lru_scheduler import RedisDelegate, Fblog
from constant import CHANNEL_STUDY_COIN_VARY,FB_WEEKLY_CACHE, FB_MONTHLY_CACHE, STUDY_FB_WEEKLY_CACHE, STUDY_FB_MONTHLY_CACHE


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
    DOWNLOAD_SIZE_PER_FB = 200 * 1024 * 1024  # 200MB
    _ASCENDING = 1
    _DESCENDING = -1
    _sns_share_cache_update_time = datetime.now()
    ONE_DAY = 24 * 3600
    _MAX_NO_FB_DOWNLOAD_NUM = 1000
    # _update_fb_callback = staticmethod(lambda x, y: stdout.write("uid:" + str(x) + " updated coin:" + str(y) + "\n"))
    # _user_coin_vary = {}
    # _user_study_coin_vary = {}
    _FREE_DOWNLOAD_NUM_BASE_LINE = 10
    _MAX_DOWNLOAD_FB = 20
    MAX_VARY_CNT = 10

    _redis_cache = RedisCacheClient().get_instance()
    _FB_WEEKLY_CACHE = FB_WEEKLY_CACHE
    _FB_MONTHLY_CACHE = FB_MONTHLY_CACHE
    _STUDY_FB_WEEKLY_CACHE = STUDY_FB_WEEKLY_CACHE
    _STUDY_FB_MONTHLY_CACHE = STUDY_FB_MONTHLY_CACHE

    _coin_rules = {"register": 200,
                   "online_an_hour": 10,
                   "invite_a_user": 300,
                   "hot100_resource": 200,
                   "hot500_resource": 500,
                   "pass_audit_for_study_res": 100,
                   "online_plus_fb_line": 200,
                   "resource_download_by_other": 1,
                   "resource_download_by_before_10": 0,
                   "sns_share": 50,
                   "max_invite_user_cnt": 50000,
                   "tip_off": 5,
                   "focus_us": 100}

    _db = motorclient.fbt
    redis_delegator = None

    @classmethod
    def set_db(cls, db):
        cls._db = db
        cls.redis_delegator = RedisDelegate()
        cls.redis_delegator.add_collection(Fblog())

    @classmethod
    def is_free_day(cls):
        FREE_DAY_DEAD_LINE = datetime(year=2015,month=7,day=1)
        return datetime.now() < FREE_DAY_DEAD_LINE


    # @classmethod
    # def is_function(cls, f):
    #     return hasattr(f, '__call__')


    @classmethod
    @gen.coroutine
    def clear_db(cls):
        yield cls._db.coins_of_user.remove()
        yield cls._db.users.remove()

    @classmethod
    @gen.coroutine
    def register_ok(cls, uid):
        uid = long(uid)
        assert (uid > 0)
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if not coin:
            # fblog
            #yield cls._db.fblog.insert({'uid': uid, 'online_time': 0, 'log': [
             #   {'date': datetime.now(), 'coin': cls._coin_rules["register"], 'info': 'register'}]})
            uid_fblog = cls.redis_delegator.fblog(uid)
            uid_fblog.online_time = 0
            uid_fblog.log.rpush({'date': datetime.now(), 'coin': cls._coin_rules["register"], 'info': 'register'})

            yield cls._db.coins_of_user.insert({'uid': uid, 'total_coins': cls._coin_rules["register"]})

    @classmethod
    @gen.coroutine
    def user_online_ok(cls, uid, online_at, offline_at):
        assert online_at > 0 and offline_at > 0 and offline_at > online_at
        uid = long(uid)
        assert uid > 0
        online_hour = (offline_at - online_at) / 3600.0  # long(time()) return seconds
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            if "total_coins" in coin and coin["total_coins"] >= cls._coin_rules["online_plus_fb_line"]:
                cls.update_coin(coin, uid, online_hour * cls._coin_rules["online_an_hour"])
                # fblog
                '''
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": online_hour * cls._coin_rules["online_an_hour"],
                        "info": "online:" + str(online_at) + "-" + str(offline_at) + " coin:" + str(
                            coin["total_coins"])}},
                                                          "$inc": {"online_time": online_hour}})
                '''
                uid_fblog = cls.redis_delegator.fblog(uid)
                uid_fblog.log.rpush({"date": datetime.now(), "coin": online_hour * cls._coin_rules["online_an_hour"],
                                                    "info": "online:" + str(online_at) + "-" + str(offline_at) + " coin:" + str(coin["total_coins"])})
                uid_fblog.log.ltrim(-201, -1)
                uid_fblog.online_time += online_hour

                coin["online_at"] = online_at
                coin["offline_at"] = offline_at
                yield cls._db.coins_of_user.save(coin)
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
                    '''
                    yield cls._db.fblog.update({'uid': uid}, {"$push": {
                    "log": {"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                            "info": "focus_us coin:" + str(coin["total_coins"])}}})
                    '''
                    uid_fblog = cls.redis_delegator.fblog(uid)
                    uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                                                        "info": "focus_us coin:" + str(coin["total_coins"])})
                    uid_fblog.log.ltrim(-201, -1)
                    # coin["total_coins"]+=cls._coin_rules["focus_us"]
                else:
                    logging.info("duplicated focus us uid:" + str(uid))
            else:
                coin["focus_us"] = True
                cls.update_coin(coin, uid, cls._coin_rules["focus_us"])
                # fblog
                '''
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                        "info": "focus_us coin:" + str(coin["total_coins"])}}})
                '''
                uid_fblog = cls.redis_delegator.fblog(uid)
                uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["focus_us"],
                                                    "info": "focus_us coin:" + str(coin["total_coins"])})
                uid_fblog.log.ltrim(-201, -1)
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
                if download_num > cls._FREE_DOWNLOAD_NUM_BASE_LINE and not cls.is_free_day():
                    if '+' in fid:
                        minus_fb = - cls.public_resource_download_coin(long(fid.split('+')[1].split('_')[1]))
                    else:
                        minus_fb = - cls.public_resource_download_coin(long(fid.split('_')[1]))
                    uid_fblog = cls.redis_delegator.fblog(uid)
                    uid_fblog.log.rpush({"date": datetime.now(), "coin":  minus_fb,
                                                        "info": "download_a_public_resource:" + fid + " coin:" + str(coin["total_coins"])})
                    uid_fblog.log.ltrim(-201, -1)

                    cls.update_coin(coin, uid, minus_fb)
                yield cls._db.coins_of_user.save(coin)
                if cls._FREE_DOWNLOAD_NUM_BASE_LINE < download_num <= cls._MAX_NO_FB_DOWNLOAD_NUM:
                    for user in users_downloaded_from:
                        yield cls.plus_fb(user, cls._coin_rules["resource_download_by_other"])
                        coin = yield cls._db.coins_of_user.find_one({'uid': user},{'total_coins':1})
                        '''
                        yield cls._db.fblog.update({'uid': user}, {"$push": {
                            "log": {"date": datetime.now(), "coin": cls._coin_rules["resource_download_by_other"],
                                    "info": "resource_download_by_other:" + fid + " coin:" + str(
                                        coin["total_coins"])}}})
                        '''
                        uid_fblog = cls.redis_delegator.fblog(user)
                        uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["resource_download_by_other"],
                                                            "info": "resource_download_by_other:" + fid + " coin:" + str(coin["total_coins"])})
                        uid_fblog.log.ltrim(-201, -1)
        else:
            logging.info("Warning: logic err. uid or public_download_queue not in coin db.")

    @classmethod
    @gen.coroutine
    def sns_share_ok(cls, uid_of_shared_person, remote_ip):
        assert remote_ip
        uid_of_shared_person = long(uid_of_shared_person)
        assert uid_of_shared_person > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid_of_shared_person})
        if coin:
            if "sns_clicked_ip" not in coin:
                coin["sns_clicked_ip"]=[]
            if remote_ip not in coin["sns_clicked_ip"]:
                coin["sns_clicked_ip"].append(remote_ip)
                if "sns_share_times" in coin:
                    coin["sns_share_times"] += 1
                else:
                    coin["sns_share_times"] = 1
                if coin["sns_share_times"] > 1000:
                    logging.info("user is a hacker. his share times exceed 1000. check him:"+str(uid_of_shared_person))
                    return
                '''
                yield cls._db.fblog.update({'uid': uid_of_shared_person}, {"$push": {
                "log": {"date": datetime.now(), "coin": cls._coin_rules["sns_share"],
                        "info": "sns_share coin:" + str(coin["total_coins"])}}})
                '''
                uid_fblog = cls.redis_delegator.fblog(uid_of_shared_person)
                uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["sns_share"],
                                                    "info": "sns_share coin:" + str(coin["total_coins"])})
                uid_fblog.log.ltrim(-201, -1)

                cls.update_coin(coin, uid_of_shared_person, cls._coin_rules["sns_share"])
                yield cls._db.coins_of_user.save(coin)
        else:
            logging.info("Warning: logic err. uid not in coin db.")


    @classmethod
    @gen.coroutine
    def get_user_total_fb_coin(cls, uid, need_study_coin=False):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid}, {"total_coins":1,"coins_by_study":1})
        if coin and "total_coins" in coin:
            if need_study_coin:
                if "coins_by_study" in coin:
                    raise gen.Return([int(round(coin["total_coins"])), int(coin["coins_by_study"])])
                else:
                    raise gen.Return([int(round(coin["total_coins"])), 0])
            else:
                raise gen.Return(int(round(coin["total_coins"])))
        else:
            if need_study_coin:
                raise gen.Return([0, 0])
            else:
                raise gen.Return(0)

    @classmethod
    @gen.coroutine
    def plus_study_fb(cls, uid, how_many):
        uid = long(uid)
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            cls.update_study_coin(coin, uid, how_many)
            yield cls._db.coins_of_user.save(coin)

    @classmethod
    def update_study_coin(cls, coin, uid, delta_fb):
        uid = long(uid)
        if "coins_by_study" not in coin:
            coin["coins_by_study"] = 0
        coin["coins_by_study"] += delta_fb
        if coin["coins_by_study"] < 0:
            coin["coins_by_study"] = 0
        # if uid not in cls._user_study_coin_vary:
        #     cls._user_study_coin_vary[uid] = 0
        # cls._user_study_coin_vary[uid] += delta_fb

        pipe = cls._redis_cache.pipeline()
        pipe.hincrbyfloat(cls._STUDY_FB_WEEKLY_CACHE, uid, int(delta_fb))
        pipe.hincrbyfloat(cls._STUDY_FB_MONTHLY_CACHE, uid, int(delta_fb))
        pipe.execute()

        # if len(cls._user_study_coin_vary) >= cls.MAX_VARY_CNT:
        #     RedisPubClient().publish(json.dumps(cls._user_study_coin_vary), CHANNEL_STUDY_COIN_VARY)
        #     cls.reset_study_coin_vary()

    @classmethod
    @gen.coroutine
    def plus_fb(cls, uid, how_many):
        uid = long(uid)
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin and "total_coins" in coin:
            cls.update_coin(coin, uid, how_many)
            yield cls._db.coins_of_user.save(coin)

    @classmethod
    @gen.coroutine
    def get_total_rank_helper(cls, sort_item):
        cursor = cls._db.coins_of_user.find({},{"uid":1,sort_item:1}).sort([(sort_item, cls._DESCENDING), ]).limit(200)
        ans = []
        while (yield cursor.fetch_next):
            coin = cursor.next_object()
            ans.append((coin['uid'], int(coin[sort_item])))
        raise gen.Return(ans)

    @classmethod
    @gen.coroutine
    def get_total_rank(cls):
        ans = yield cls.get_total_rank_helper("total_coins")
        raise gen.Return(ans)

    @classmethod
    @gen.coroutine
    def get_total_rank2(cls):
        ans = yield cls.get_total_rank_helper("coins_by_study")
        raise gen.Return(ans)

    @classmethod
    @gen.coroutine
    def invite_a_user(cls, uid):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            if "invite_user_cnt" not in coin:
                coin["invite_user_cnt"] = 0
            if coin["invite_user_cnt"] < cls._coin_rules["max_invite_user_cnt"]:
                coin["invite_user_cnt"] += 1
                yield cls._db.coins_of_user.save(coin)
                # fblog
                '''
                yield cls._db.fblog.update({'uid': uid}, {"$push": {
                "log": {"date": datetime.now(), "coin": cls._coin_rules["invite_a_user"],
                        "info": "invite_a_user coin:" + str(coin["total_coins"])}}})
                '''
                uid_fblog = cls.redis_delegator.fblog(uid)
                uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["invite_a_user"],
                                                    "info": "invite_a_user coin:" + str(coin["total_coins"])})
                uid_fblog.log.ltrim(-201, -1)

                yield cls.plus_fb(uid, cls._coin_rules["invite_a_user"])

    @classmethod
    @gen.coroutine
    def hot100_resource(cls, uid, file_id):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            yield cls.plus_fb(uid, cls._coin_rules["hot100_resource"])
            '''
            yield cls._db.fblog.update({'uid': uid}, {"$push": {
            "log": {"date": datetime.now(), "coin": cls._coin_rules["hot100_resource"],
                    "info": "hot100_resource:" + file_id + " coin:" + str(coin["total_coins"])}}})
            '''
            uid_fblog = cls.redis_delegator.fblog(uid)
            uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["hot100_resource"],
                                                "info": "hot100_resource:" + file_id + " coin:" + str(coin["total_coins"])})
            uid_fblog.log.ltrim(-201, -1)

    @classmethod
    @gen.coroutine
    def hot500_resource(cls, uid, file_id):
        uid = long(uid)
        assert uid > 0
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            yield cls.plus_fb(uid, cls._coin_rules["hot500_resource"])
            '''
            yield cls._db.fblog.update({'uid': uid}, {"$push": {
            "log": {"date": datetime.now(), "coin": cls._coin_rules["hot500_resource"],
                    "info": "hot500_resource:" + file_id + " coin:" + str(coin["total_coins"])}}})
            '''
            uid_fblog = cls.redis_delegator.fblog(uid)
            uid_fblog.log.rpush({"date": datetime.now(), "coin": cls._coin_rules["hot500_resource"],
                                                "info": "hot500_resource:" + file_id + " coin:" + str(coin["total_coins"])})
            uid_fblog.log.ltrim(-201, -1)

    @classmethod
    @gen.coroutine
    def issue_a_reward(cls, uid, reward_id, how_many):
        reason = "issue an reward:" + reward_id
        # yield cls.plus_study_fb_helper(uid, how_many, reason)
        yield CoinManager.instance().issue_a_reward(uid, reward_id, how_many)


    @classmethod
    @gen.coroutine
    def pass_audit_a_study_res(cls, uid, file_id, how_many):
        reason = "pass_audit_for_study_res:" + file_id
        yield CoinManager.instance().pass_audit_a_study_res(uid, file_id, how_many)
        # yield cls.plus_study_fb_helper(uid, how_many, reason)
        # yield CoinManager.instance().register_ok(uid)

    @classmethod
    @gen.coroutine
    def reward_accepted(cls, uid, file_id, how_many):
        reason = "reward_accepted:" + file_id
        yield CoinManager.instance().reward_accepted(uid, file_id, how_many)
        # yield cls.plus_study_fb_helper(uid, how_many, reason)

    @classmethod
    @gen.coroutine
    def plus_study_fb_helper(cls, uid, how_many, reason):
        uid = long(uid)
        coin = yield cls._db.coins_of_user.find_one({'uid': uid})
        if coin:
            # yield cls.plus_fb(uid, how_many)
            yield cls.plus_study_fb(uid, how_many)
            uid_fblog = cls.redis_delegator.fblog(uid)
            uid_fblog.log.rpush({"date": datetime.now(), "coin": how_many,
                    "info": reason + " coin:" + str(coin["total_coins"])})
            uid_fblog.log.ltrim(-201, -1)

    @classmethod
    def update_coin(cls, coin, uid, delta_fb):
        uid = long(uid)
        assert "total_coins" in coin
        origin_coin = coin["total_coins"]
        coin["total_coins"] += delta_fb
        if coin["total_coins"] < 0:
            coin["total_coins"] = 0
            delta_fb = -origin_coin

        # if uid not in cls._user_coin_vary:
        #     cls._user_coin_vary[uid] = 0
        # cls._user_coin_vary[uid] += delta_fb

        # print "send coin update...",cls._user_coin_vary
        pipe = cls._redis_cache.pipeline()
        pipe.hincrbyfloat(cls._FB_WEEKLY_CACHE, uid, int(delta_fb))
        pipe.hincrbyfloat(cls._FB_MONTHLY_CACHE, uid, int(delta_fb))
        pipe.execute()

        # MAX_VARY_CNT = 10
        # if len(cls._user_coin_vary) >= MAX_VARY_CNT:
        #     RedisPubClient().publish(json.dumps(cls._user_coin_vary))
        #     cls.reset_coin_vary()

    # @classmethod
    # def reset_coin_vary(cls):
    #     cls._user_coin_vary = {}
    #
    # @classmethod
    # def reset_study_coin_vary(cls):
    #     cls._user_study_coin_vary = {}

    @classmethod
    def public_resource_download_coin(cls, file_size):
        return (file_size + cls.DOWNLOAD_SIZE_PER_FB - 1) / cls.DOWNLOAD_SIZE_PER_FB

