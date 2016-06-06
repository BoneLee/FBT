#-*- coding:utf-8 -*-
from time import time
from tornado import gen

class LogForUser:
    _db = None

    @staticmethod
    def set_db(db):
        LogForUser._db = db

    @staticmethod
    @gen.coroutine
    def log_user_delete(uid, time, file_id):
        yield LogForUser._db.user_delete.update({"uid":uid},{"$push":{"list":{"time":time, "file_id":file_id}}},True)

    @staticmethod
    @gen.coroutine
    def log_user_search(uid, time, keyword, count):
        yield LogForUser._db.user_search.update({"uid":uid},{"$push":{"list":{"time":time, "keyword":keyword, "count":count}}},True)

    @staticmethod
    @gen.coroutine
    def log_user_upload(uid, time, file_id):
        yield LogForUser._db.user_upload.update({"uid":uid},{"$push":{"list":{"time":time, "file_id":file_id}}},True)

    @staticmethod
    @gen.coroutine
    def log_user_download(uid, time, file_id):
        tmp = {"time":time, "file_id":file_id, "is_over":0, "finish_time":0}
        yield LogForUser._db.user_download.update({"uid":uid},{"$push":{"list":tmp}},True)

    @staticmethod
    @gen.coroutine
    def log_user_download_over(uid, file_id):
        yield LogForUser._db.user_download.update({"uid":uid,"list.file_id":file_id},
            { "$set": { "list.$.is_over" : 1, "list.$.finish_time": long(time())} })