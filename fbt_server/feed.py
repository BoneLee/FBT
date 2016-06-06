#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import gen
import simplejson as json
from time import time
from datetime import datetime
from redis_handler import RedisHandler
from util import generate_ukey, getFriendsById, get_next_sequence, set_next_sequence, getUserInfoById

class FeedManager(object):
    #struct: {fid, rid, rname, uid, type, content, ctime}
    #{uid, fid, seq}
    _max_feed = 200
    _redis = RedisHandler()
    _db = None
    _db_realtime = None
    _key = "feed"
    TYPE_UPLOAD = 0
    TYPE_DOWNLOAD = 1
    TYPE_COMMENT = 2
    TYPE_GRADE = 3
    _type = {0: "上传", 1: "下载", 2: "评论", 3: "评分"}

    @classmethod
    def set_db(cls, db, db_realtime):
        cls._db = db
        cls._db_realtime = db_realtime

    @classmethod
    @gen.coroutine
    def add_feed(cls, rid, rname, uid, t, content, link = "", desc = ""):
        assert t >= 0 and t < 4
        assert uid > 0
        #seq = yield get_next_sequence(cls._db_realtime, cls._key)
        cur_time = long(time()*1000)
        fid = generate_ukey(uid, cur_time)
        feed = {"fid": fid, "rid": rid, "rname": rname, "uid": uid, "type": t, "content": content,
        "ctime": cur_time, "link": link, "desc": desc}
        tmp_feed = {"fid": fid, "rid": rid, "rname": rname, "uid": uid, "type": t, "content": content,
        "ctime": cur_time, "link": link, "desc": desc}
        yield cls._db.all_feeds.insert(feed)
        friends = yield getFriendsById(uid)
        for item in friends:
            user_feed = {"uid": item["uid"], "fid": fid, "ctime": cur_time}
            yield cls._db.all_user_feeds.insert(user_feed)
            uid_tmp = "feed:"+str(item["uid"])
            size = cls._redis.llen(uid_tmp)
            if size >= 200:
                cls._redis.rpop(uid_tmp)
            cls._redis.lpush(uid_tmp, json.dumps(tmp_feed))
            #seq += 1
        #yield set_next_sequence(cls._db_realtime, cls._key, seq)

    @classmethod
    @gen.coroutine
    def get_feed(cls, uid, time = 1, page = 1, max_feeds_cnt_in_page = 20, t = None):
        assert time > 0
        assert uid > 0
        assert page > 0
        feed_list = []
        (start_index, end_index) = ((page - 1) * max_feeds_cnt_in_page, page * max_feeds_cnt_in_page)
        if end_index <= 200:
            uid_tmp = "feed:"+str(uid)
            tmp_feed_list = cls._redis.lrange(uid_tmp, start_index, end_index-1)
            for feed in tmp_feed_list:
                feed = json.loads(feed)
                friendId = feed["fid"].split("_")[0]
                info = yield getUserInfoById(friendId)
                feed["icon"] = info["icon"]
                feed["nick_name"] = info["nick_name"]
                feed["type"] = cls._type[feed["type"]]
                feed_list.append(feed) 
        else:
            if time == 1:
                cursor = cls._db.all_user_feeds.find({"uid":uid}, {"_id":0}).sort([("ctime", -1),]).limit(max_feeds_cnt_in_page)
            else:
                cursor = cls._db.all_user_feeds.find({"ctime":{"$lt":time}, "uid":uid}, {"_id":0}).sort([("ctime", -1),]).limit(max_feeds_cnt_in_page)        
            while (yield cursor.fetch_next):
                user_feed = cursor.next_object()
                feed = yield cls._db.all_feeds.find_one({"fid": user_feed["fid"]}, {"_id": 0})
                friendId = user_feed["fid"].split("_")[0]
                info = yield getUserInfoById(friendId)
                feed["icon"] = info["icon"]
                feed["nick_name"] = info["nick_name"]
                feed["type"] = cls._type[feed["type"]]
                feed_list.append(feed)
        raise gen.Return(feed_list)
