#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import gen

class ResCountManager(object):
    """
    {0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其他"}
    {uid, res_type, count, fcount}
    """
    _db = None
    ALL = -1

    @classmethod
    def set_db(cls, db):
        cls._db = db

    @classmethod
    @gen.coroutine
    def inc_res(cls, uid, res_type):
        yield cls._db.res_count.update({"uid": uid, "res_type": res_type}, { "$inc": { "count": 1 } }, True)
        yield cls._db.res_count.update({"uid": uid, "res_type": cls.ALL}, { "$inc": { "count": 1 } }, True)

    @classmethod
    @gen.coroutine
    def sub_res(cls, uid, res_type):
        yield cls._db.res_count.update({"uid": uid, "res_type": res_type}, { "$inc": { "count": -1 } }, True)
        yield cls._db.res_count.update({"uid": uid, "res_type": cls.ALL}, { "$inc": { "count": -1 } }, True)

    @classmethod
    @gen.coroutine
    def get_count(cls, uid, res_type):
        count = yield cls._db.res_count.find_one({"uid": uid, "res_type": res_type}, {"count": 1})
        raise gen.Return(count["count"])

    @classmethod
    @gen.coroutine
    def inc_friend_res(cls, fuid, res_type):
        yield cls._db.res_count.update({"uid": fuid, "res_type": res_type}, { "$inc": { "fcount": 1 } }, True)
        yield cls._db.res_count.update({"uid": fuid, "res_type": cls.ALL}, { "$inc": { "fcount": 1 } }, True)

    @classmethod
    @gen.coroutine
    def get_friend_count(cls, fuid, res_type):
        count = yield cls._db.res_count.find_one({"uid": fuid, "res_type": res_type}, {"fcount": 1})
        raise gen.Return(count["fcount"])

    @classmethod
    @gen.coroutine
    def sub_friend_res(cls, fuid, res_type):
        yield cls._db.res_count.update({"uid": fuid, "res_type": res_type}, { "$inc": { "fcount": -1 } }, True)
        yield cls._db.res_count.update({"uid": fuid, "res_type": cls.ALL}, { "$inc": { "fcount": -1 } }, True)

