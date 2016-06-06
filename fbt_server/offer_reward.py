#-*- coding: utf-8 -*-
#所有悬赏库：res_type, 资源描述，文件名，fb，uid，悬赏记录时间，追加fb，追加uid_list，
#file_info,total_fb,res_year,res_country,is_finish（每个上传者的资源是一条item）
#file_info {file_id:[uids]}
#我的悬赏库：uid, rid_list
from constant import *
from time import time
from datetime import datetime
from tornado import gen
from resource_info import ResourceInfo
import simplejson as json
import math
import msg_handle
import uuid
from resource_manager import ResourceStoreManager
from util import RedisPub, gen_file_hash, generate_ukey, getPages, getUserInfoById, get_prefix

class Reward(object):
    _db = None
    _coin_db = None
    reward_sort_by = {"time": 0, "reward": 1}
    _key = "reward"

    @classmethod
    def set_db(cls, db, coin_db):
        cls._db = db
        cls._coin_db = coin_db

    @classmethod
    @gen.coroutine
    def user_offer_reward(cls, uid, desc, fileName, fb, res_type, res_year, res_country):
        assert fileName is not None and len(fileName) > 0
        assert fb > 0
        assert uid > 0
        assert ResourceInfo.is_valid_main_type(res_type)
        uid = long(uid)
        create_time = long(time()*1000)
        rid = generate_ukey(uid, create_time)
        #seq_type, seq = yield get_next_sequence(cls._db_realtime, cls._key, res_type)
        reward = {"desc":desc, "fileName":fileName, "fb":fb, "uid":uid, "rid":rid, "append_fb":[], "append_uid":[],
            "res_type":res_type, "ctime":create_time, "file_info":{},"append_time":[], 
            "total_fb":fb,"res_year":res_year,"res_country":res_country,"is_finish":0}
        coin_ret = yield cls.user_coin_handle(uid, fb, False)
        if coin_ret:
            #add rid to the user reward
            #yield cls._db.user_reward.update({'uid': uid}, {'$push': {'reward_ids': rid}}, True)
            #add a reward to all reward
            yield cls._db.all_reward.insert(reward)
            #add a reward to my reward
            yield cls._db.my_reward.update({"uid": uid}, {"$addToSet": {"rid_list": rid}}, True)
            yield cls._db.my_reward.update({"uid": uid}, {"$addToSet": {"rid_list"+str(res_type): rid}}, True)

    @classmethod
    @gen.coroutine
    def user_coin_handle(cls, uid, fb, isAdd=True):
        coin = yield cls._coin_db.coins_of_user.find_one({'uid': uid})
        coin_vary = fb
        if isAdd:
            coin["total_coins"] += fb
        else:
            coin["total_coins"] -= fb
            coin_vary = -fb
            if coin["total_coins"] < 0:
                raise gen.Return(False)
        yield cls._coin_db.coins_of_user.save(coin)
        send = json.dumps({str(uid): coin_vary})
        RedisPub.publish(CHANNEL_COIN_VARY, send)
        raise gen.Return(True)
    
    @classmethod
    @gen.coroutine
    def user_inform(cls, uid, content):
        msg = {"type": 7, "sticky": 1, "content": content}
        send = json.dumps({"type": 0, "msg": msg, "uid": uid, "user": ""})
        RedisPub.publish(CHANNEL_INFORM, send)
        msg = {}
        msg["type"] = 0
        #msg["isRead"] = 0
        msg["id"] = str(uuid.uuid1().int)
        msg["sender"] = "0"
        msg["nick"] = "0"
        msg["content"] = content
        msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
        useInfo = yield getUserInfoById(uid)
        msg_handle.addMsg(useInfo["user"], msg, "", "", "")

    @classmethod
    @gen.coroutine
    def user_append_reward(cls, uid, append_fb, rid):
        assert append_fb > 0
        assert uid > 0
        assert len(rid) > 0
        uid = long(uid)
        reward = yield cls._db.all_reward.find_one({'rid': rid})
        coin_ret = yield cls.user_coin_handle(uid, append_fb, False)
        if reward and coin_ret:
            reward["append_fb"].append(append_fb)
            reward["append_time"].append(long(time()*1000))
            reward["append_uid"].append(uid)
            reward["total_fb"] += append_fb
            #add rid to the user reward
            #yield cls._db.user_reward.update({'uid': uid}, {'$push': {'reward_ids': rid}}, True)
            yield cls._db.all_reward.save(reward)
            #add a reward to my reward
            res_type = reward["res_type"]
            yield cls._db.my_reward.update({"uid": uid}, {"$addToSet": {"rid_list": rid}}, True)
            yield cls._db.my_reward.update({"uid": uid}, {"$addToSet": {"rid_list"+str(res_type): rid}}, True)

    @classmethod
    @gen.coroutine
    def extract_more(cls, one_reward, version="2.0", shouldExtractRes=False):
        user = yield getUserInfoById(one_reward["uid"])
        if user:
            one_reward["nick_name"] = user["nick_name"]
            one_reward["icon"] = user["icon"]
            one_reward["append_user"] = [];
            for item in one_reward["append_uid"]:
                append_user = yield getUserInfoById(item)
                one_reward["append_user"].append(append_user)
            file_info = one_reward["file_info"]
            if shouldExtractRes and file_info:
                file_infos = []
                for item in file_info:
                    hash_size = gen_file_hash(item)
                    ret = yield ResourceStoreManager.get_resources_by_file_ids(version, [hash_size[0]], [hash_size[1]])
                    if ret:
                        file_infos.append(ret[0])
                one_reward["file_infos"] = file_infos
            del one_reward["file_info"]
            raise gen.Return(True)
        else:
            raise gen.Return(False)

    @classmethod
    @gen.coroutine
    def get_reward_count_by_type(cls, res_type=None):
        count = 0
        if res_type:
            assert ResourceInfo.is_valid_main_type(res_type)
            cursor = cls._db.all_reward.find({"res_type": res_type})
            count = yield cursor.count()
        else:
            count = yield cls._db.all_reward.count()
        raise gen.Return(count)

    @classmethod
    @gen.coroutine
    def get_all_reward_by_type(cls, version = 1.9, page = 1, time=1, max_rewards_cnt_in_page=20, sort_by=0,res_type=None):
        assert time >= 1
        assert page >= 1
        assert max_rewards_cnt_in_page > 0
        assert sort_by == cls.reward_sort_by["time"] or sort_by == cls.reward_sort_by["reward"]
        (start_index, end_index) = ((page - 1) * max_rewards_cnt_in_page, page * max_rewards_cnt_in_page)
        all_rewards = []
        cursor = None
        if res_type is not None:
            assert ResourceInfo.is_valid_main_type(res_type)
            if sort_by == cls.reward_sort_by["time"]:
                if time == 1:
                    cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}, "res_type":res_type}, {"_id":0}).sort([("ctime", -1),]).limit(max_rewards_cnt_in_page)
                else:
                    cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}, "ctime":{"$lt":time}, "res_type":res_type}, {"_id":0}).sort([("ctime", -1),]).limit(max_rewards_cnt_in_page)
            else:
                cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}, "res_type":res_type}, {"_id": 0}).sort([("total_fb", -1), ("ctime", -1)])
                cursor = cursor.skip(start_index).limit(max_rewards_cnt_in_page) 
        else:
            if sort_by == cls.reward_sort_by["time"]:
                if time == 1:
                    cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}}, {"_id": 0}).sort([("ctime", -1),]).limit(max_rewards_cnt_in_page)
                else:
                    cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}, "ctime":{"$lt":time}}, {"_id": 0}).sort([("ctime", -1),]).limit(max_rewards_cnt_in_page)
            else:
                cursor = cls._db.all_reward.find({"is_finish": {"$ne": 1}}, {"_id": 0}).sort([("total_fb", -1), ("ctime", -1)])
                cursor = cursor.skip(start_index).limit(max_rewards_cnt_in_page)
        while (yield cursor.fetch_next):
            item = cursor.next_object()
            if (yield cls.extract_more(item, version)):
                all_rewards.append(item)
        raise gen.Return(all_rewards)

    @classmethod
    @gen.coroutine
    def get_my_reward_by_type(cls, version, uid, page = 1, max_rewards_cnt_in_page=20, res_type=None):
        assert page > 0
        assert uid > 0
        uid = long(uid)
        (start_index, end_index) = ((page - 1) * max_rewards_cnt_in_page, page * max_rewards_cnt_in_page)
        all_rewards = []
        cursor = None
        rewards = []
        if res_type is not None:
            assert ResourceInfo.is_valid_main_type(res_type)
            cursor = yield cls._db.my_reward.find_one({"uid": uid}, {"_id": 0, "rid_list"+str(res_type): 1})
            if cursor:
                rewards = cursor["rid_list"+str(res_type)]
            else:
                rewards = []
        else:
            cursor = yield cls._db.my_reward.find_one({"uid": uid}, {"_id": 0, "rid_list": 1})
            if cursor:
                rewards = cursor["rid_list"]
            else:
                rewards = []
        size = len(rewards)
        end_index = min(end_index, size)
        for i in xrange(start_index, end_index):
            item = yield cls._db.all_reward.find_one({'rid': rewards[i]}, {"_id": 0})
            if item["is_finish"] == 1:
                ret = yield cls.extract_more(item, version)
            else:
                ret = yield cls.extract_more(item, version, True)
            if ret:
                all_rewards.append(item)
        result = {"total_page": getPages(size), "rewards": all_rewards}
        raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def user_upload_file(cls, uid, file_id, rid):
        uid = long(uid)
        reward = yield cls._db.all_reward.find_one({'rid': rid})
        if reward:
            file_info = reward["file_info"]
            if file_id in file_info and uid not in file_info[file_id]:
                file_info[file_id].append(uid)
            else:
                file_info[file_id] = [uid]
            yield cls._db.all_reward.save(reward)
            all_uid = [reward["uid"]]
            all_uid.extend(reward["append_uid"])
            for mid in all_uid:
                yield cls.user_inform(mid, u"您悬赏的资源"+reward["fileName"]+u"已经有人上传了，请到我的悬赏里查看。")

    @classmethod
    @gen.coroutine
    def user_download_file_over(cls, user_download_from, file_id, rid):
        reward = yield cls._db.all_reward.find_one({'rid': rid})
        if reward:
            coin = reward["total_fb"]
            reward_users = []
            reward["is_finish"] = 1
            yield cls._db.all_reward.save(reward)
            uid_list = reward["file_info"][file_id]
            if uid_list:
                for item in uid_list:
                    if item in user_download_from:
                        reward_users.append(item)
                l = len(reward_users)
                for item in reward_users:
                    yield cls.user_coin_handle(item, long(coin/l))

    @classmethod
    @gen.coroutine
    def user_cancel_reward(cls, uid, rid, res_type):
        if ResourceInfo.is_valid_main_type(res_type):
            yield cls._db.my_reward.update({'uid': uid}, {'$pull': {"rid_list": rid}})
            yield cls._db.my_reward.update({'uid': uid}, {'$pull': {"rid_list"+str(res_type): rid}})
            reward = yield cls._db.all_reward.find_one({'rid': rid})
            if reward:
                if long(uid) == long(reward["uid"]):
                    if len(reward["append_uid"]) == 0:
                        yield cls._db.all_reward.remove({'rid': rid})
                    else:
                        reward["uid"] = reward["append_uid"][0]
                        del reward["append_uid"][0]
                        yield cls._db.all_reward.save(reward)
                else:
                    length = len(reward["append_uid"])
                    for i in xrange(length):
                        item = reward["append_uid"][i]
                        if long(uid) == long(item):
                            del reward["append_uid"][i]
                            yield cls._db.all_reward.save(reward)
                            break
                yield cls.user_coin_handle(uid, reward["fb"])
                raise gen.Return(True)
            else:
                raise gen.Return(False)
        else:
            raise gen.Return(False)

            


