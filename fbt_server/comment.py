#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tornado import gen
from time import time
from datetime import datetime
from cipher import WaveCipher as Cipher
from util import get_next_sequence

class CommentManager(object):
    #struct: {rid, rname, uid, uname, uicon, comment, ctime, seq}
    _db = None
    _db_realtime = None
    _key = "comment"

    @classmethod
    def set_db(cls, db, db_realtime):
        cls._db = db
        cls._db_realtime = db_realtime

    @classmethod
    @gen.coroutine
    def getComment(cls, rid, time=1, max_comments_cnt_in_page = 20):
        assert time > 0
        assert len(rid) > 0
        #(start_index, end_index) = ((page - 1) * max_comments_cnt_in_page, page * max_comments_cnt_in_page)
        if time == 1:
            cursor = cls._db.all_comments.find({"rid":rid}, {"_id":0}).sort([("ctime", -1),]).limit(max_comments_cnt_in_page)
        else:
            cursor = cls._db.all_comments.find({"ctime":{"$lt":time}, "rid":rid}, {"_id":0}).sort([("ctime", -1),]).limit(max_comments_cnt_in_page)
        comment_list = []
        while (yield cursor.fetch_next):
            one_comment = cursor.next_object()
            one_comment["comment"] = Cipher.encrypt(one_comment["comment"])
            comment_list.append(one_comment)
        raise gen.Return(comment_list)

    @classmethod
    @gen.coroutine
    def addComment(cls, rid, rname, uid, nick_name, icon, comment):
        assert len(rid) > 0
        assert uid > 0
        #seq = yield get_next_sequence(cls._db_realtime, cls._key, rid)
        one_comment = {"rid": rid, "rname":rname, "uid": uid, "uname":nick_name, "uicon":icon, "comment": comment,
        "ctime": long(time()*1000)}
        yield cls._db.all_comments.insert(one_comment)