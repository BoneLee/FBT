# -*- coding: utf-8 -*-
__author__ = 'bone'

import motorclient
from tornado import gen

from datetime import datetime
from time import time
from tornado.escape import utf8
import logging

DOWNLOAD_COIN_OF_FILE_TAGS = {
  '作业和答案': 20,
  '课堂笔记': 20,
  '往届考题': 20,
  '学习心得': 20,
  '电子书或文献': 5,
  '课程课件': 5,
  'TED': 5,
  '软件教学': 5,
  '其他': 5
}

class CoinManager(object):
    """
    Now just for study coin manager.
    """

    REFER_COIN = 500
    REFEREE_COIN = 500
    REGISTER_COIN = 200
    COIN_REASON = {"register_ok": 0,
                   "refer_ok": 1,
                   "be_referred_ok": 2,
                   "pass_audit_a_study_res": 3,
                   "pass_audit_a_study_res_referee": 4,
                   "issue_a_reward": 5,
                   "reward_accepted": 6,
                   "download_a_resource": 7,
                   "resource_download_by_other": 8,
                   "thanks_post_experience": 9,
                   "post_experience_thanked": 10,
                   "invite_user_answer_question": 11,
                   "user_answer_question_by_invitation": 11,
                   "transfer_coin": 12
                   }
    REFEREE_COIN_PERCENTAGE = 0.95
    STATUS = {"ok": 0, "err": 1}

    _single_instance = None

    def __init__(self, db=None, redis_cache=None):
        if db:
            self._db = db
        else:
            self._db = motorclient.fbt

    @gen.coroutine
    def refer_ok(self, uid, user, referee_uid, referee_user):
        yield self._db.coins_of_user.update({'uid': uid},
                                            {"$set": {"referee_uid": referee_uid,
                                                      "referee": referee_user}},
                                            upsert=True)
        total_coin, status = yield self.add_study_coin(uid, self.REFER_COIN)
        if status == self.STATUS["ok"]:
            yield self._log(uid, self.REFER_COIN,
                            self.COIN_REASON["refer_ok"],
                            "refer_ok",
                            total_coin,
                            {"referee_user": referee_user,
                             "referee_uid": referee_uid})
        else:
            raise gen.Return(False)
        total_coin, status = yield self.add_study_coin(referee_uid, self.REFEREE_COIN)
        if status == self.STATUS["ok"]:
            yield self._log(referee_uid, self.REFEREE_COIN,
                            self.COIN_REASON["be_referred_ok"],
                            "be_referred_ok",
                            total_coin,
                            {"refer_uid": uid,
                             "refer_user": user})
        else:
            raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    def add_study_coin(self, uid, how_many):
        how_many = int(round(how_many))
        if how_many != 0:
            # TODO(bonelee) remove upsert = True
            coin = yield self._db.coins_of_user.find_and_modify(
                                                {'uid': uid},
                                                {"$inc": {"total_coins": how_many,
                                                          "coins_by_study": how_many,}},
                                                upsert=True)
            # assert coin is not None
            if coin is None:
                raise gen.Return([0, self.STATUS["err"]])
            if "total_coins" in coin:
                raise gen.Return([coin["total_coins"], self.STATUS["ok"]])
            else:
                raise gen.Return([0, self.STATUS["err"]])
        else:
            raise gen.Return([0, self.STATUS["err"]])

    @gen.coroutine
    def register_ok(self, uid, user_email):
        uid = long(uid)
        yield self._db.coins_of_user.update({'uid': uid},
                                            {"$set": {"user": user_email,
                                                      "total_coins": self.REGISTER_COIN,
                                                      "coins_by_study": self.REGISTER_COIN}},
                                            upsert=True)
        yield self._log(uid, self.REGISTER_COIN,
                        self.COIN_REASON["register_ok"],
                        "register_ok",
                        0,
                        None)

    @gen.coroutine
    def get_coin(self, uid):
        coin = yield self._db.coins_of_user.find_one({'uid': uid}, {"total_coins":1,"coins_by_study":1})
        if coin and "total_coins" in coin:
            if "coins_by_study" in coin:
                raise gen.Return([int(round(coin["total_coins"])), int(coin["coins_by_study"])])
            else:
                raise gen.Return([int(round(coin["total_coins"])), 0])
        else:
            raise gen.Return([0, 0])

    @gen.coroutine
    def pass_audit_a_study_res(self, uid, file_id, how_many):
        coin = yield self._db.coins_of_user.find_one({'uid': uid}, {"referee_uid": 1, "referee": 1})
        if coin and "referee_uid" in coin and coin["referee_uid"]:
            total_coin, status = yield self.add_study_coin(uid, how_many * self.REFEREE_COIN_PERCENTAGE)
            if status == self.STATUS["ok"]:
                yield self._log(uid, how_many * self.REFEREE_COIN_PERCENTAGE,
                                self.COIN_REASON["pass_audit_a_study_res"],
                                "pass_audit_a_study_res",
                                total_coin,
                                {"file_id": file_id})
            referee_uid = coin["referee_uid"]
            reward = how_many * (1-self.REFEREE_COIN_PERCENTAGE)
            total_coin, status = yield self.add_study_coin(referee_uid, reward)
            if status == self.STATUS["ok"]:
                yield self._log(referee_uid, reward,
                                self.COIN_REASON["pass_audit_a_study_res_referee"],
                                "pass_audit_a_study_res_referee",
                                total_coin,
                                {"file_id": file_id})
                # self.user_msg_handler.add_msg(coin["referee"], u"您推荐的好友 %s 成功上传了一个资源，系统奖励了您 %d F" % (user, reward)
        else:
            total_coin, status = yield self.add_study_coin(uid, how_many)
            if status == self.STATUS["ok"]:
                yield self._log(uid, how_many,
                                self.COIN_REASON["pass_audit_a_study_res"],
                                "pass_audit_a_study_res",
                                total_coin,
                                {"file_id": file_id})

    @gen.coroutine
    def _log(self, uid, how_many, reason_id, detail_reason, total_coin, extra_info=None):
        yield self._db.coin_log.insert({"uid": uid,
                                        "how_many": how_many,
                                        "reason_id": reason_id,
                                        "reason": detail_reason,
                                        "extra_info": extra_info,
                                        "index_ctime": long(time()*1000),
                                        "last_total_coin": total_coin,
                                        "ctime": datetime.now().strftime('%Y-%m-%d %H:%M')})

    @gen.coroutine
    def reward_accepted(self, uid, file_id, how_many):
        assert how_many > 0
        total_coin, status = yield self.add_study_coin(uid, how_many)
        if status == self.STATUS["ok"]:
            yield self._log(uid, how_many,
                            self.COIN_REASON["reward_accepted"],
                            "reward_accepted",
                            total_coin,
                            {"file_id": file_id})

    @gen.coroutine
    def issue_a_reward(self, uid, reward_id, how_many):
        assert how_many < 0
        total_coin, status = yield self.add_study_coin(uid, how_many)
        if status == self.STATUS["ok"]:
            yield self._log(uid, how_many,
                            self.COIN_REASON["issue_a_reward"],
                            "issue_a_reward",
                            total_coin,
                            {"reward_id": reward_id})

    @gen.coroutine
    def get_user_coin_log(self, uid):
        cursor = self._db.coin_log.find({"uid": uid}).sort([('index_ctime', -1),])
        log_list = yield cursor.to_list(None)
        raise gen.Return(log_list)

    @gen.coroutine
    def clear_db(self):
        yield self._db.coin_log.remove({})

    @classmethod
    def instance(cls):
        if cls._single_instance is None:
            cls._single_instance = CoinManager()
        return cls._single_instance

    def set_db_cache(self, db, cache):
        self._db = db

    def get_download_coin(self, file_tag):
        file_tag = utf8(file_tag)
        if file_tag in DOWNLOAD_COIN_OF_FILE_TAGS:
            return DOWNLOAD_COIN_OF_FILE_TAGS[file_tag]
        else:
            logging.error("found invalid download coin:" + file_tag)
            return 1

    @gen.coroutine
    def download_ok(self, uid, file_id, uploader, file_tag):
        download_coin = self.get_download_coin(file_tag)
        total_coin, status = yield self.add_study_coin(uid, -download_coin)
        if status == self.STATUS["ok"]:
            yield self._log(uid, -download_coin,
                            self.COIN_REASON["download_a_resource"],
                            "download_a_resource",
                            total_coin,
                            {"file_id": file_id})
        else:
            raise gen.Return(False)

        total_coin, status = yield self.add_study_coin(uploader, download_coin)
        if status == self.STATUS["ok"]:
            yield self._log(uploader, download_coin,
                            self.COIN_REASON["resource_download_by_other"],
                            "resource_download_by_other",
                            total_coin,
                            {"file_id": file_id})
        else:
            raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    def thanks_user_post_experience(self, uid, publisher_uid, how_much, exp_id, is_answer=False):
        total_coin, status = yield self.add_study_coin(uid, -how_much)
        if status == self.STATUS["ok"]:
            yield self._log(uid, -how_much,
                            self.COIN_REASON["thanks_post_experience"],
                            "thanks_post_experience",
                            total_coin,
                            {"exp_id": exp_id, "is_answer": is_answer})
        else:
            raise gen.Return(False)

        total_coin, status = yield self.add_study_coin(publisher_uid, how_much)
        if status == self.STATUS["ok"]:
            yield self._log(publisher_uid, how_much,
                            self.COIN_REASON["post_experience_thanked"],
                            "post_experience_thanked",
                            total_coin,
                            {"exp_id": exp_id, "is_answer": is_answer})
        else:
            raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    def invite_user_answer_question(self, answerer_uid, question_id, pubisher, how_much):
        total_coin, status = yield self.add_study_coin(answerer_uid, how_much)
        if status == self.STATUS["ok"]:
            yield self._log(answerer_uid, how_much,
                            self.COIN_REASON["user_answer_question_by_invitation"],
                            "user_answer_question_by_invitation",
                            total_coin,
                            {"question_id": question_id})
        else:
            raise gen.Return(False)

        total_coin, status = yield self.add_study_coin(pubisher, -how_much)
        if status == self.STATUS["ok"]:
            yield self._log(pubisher, -how_much,
                            self.COIN_REASON["invite_user_answer_question"],
                            "invite_user_answer_question",
                            total_coin,
                            {"question_id": question_id})
        else:
            raise gen.Return(False)
        raise gen.Return(True)

    @gen.coroutine
    def get_transfer_list(self, uid, page=1):
        # TODO(bonelee) support page and add unit test for it
        cursor = self._db.coin_log.find({"uid": uid, "reason_id": self.COIN_REASON["transfer_coin"]},
                                        {"_id": 0, "ctime": 1, "how_many": 1, "extra_info":1}).sort([('index_ctime', -1),]).limit(100)
        transfer_list = yield cursor.to_list(None)
        raise gen.Return(transfer_list)

    @gen.coroutine
    def transfer_coin_ok(self, how_much, uid, user_from, real_name, university,
                         uid2, user_to, real_name2, university2):
        total_coin, status = yield self.add_study_coin(uid, -how_much)
        if status == self.STATUS["ok"]:
            yield self._log(uid, -how_much,
                            self.COIN_REASON["transfer_coin"],
                            "F币转出",
                            total_coin,
                            {"from": {"user": user_from, "real_name": real_name, "university": university},
                             "to": {"user": user_to, "real_name": real_name2, "university": university2}})
        else:
            raise gen.Return(False)

        total_coin, status = yield self.add_study_coin(uid2, how_much)
        if status == self.STATUS["ok"]:
            yield self._log(uid2, how_much,
                            self.COIN_REASON["transfer_coin"],
                            "F币转入",
                            total_coin,
                            {"from": {"user": user_from, "real_name": real_name, "university": university},
                             "to": {"user": user_to, "real_name": real_name2, "university": university2}})
        else:
            raise gen.Return(False)
        raise gen.Return(True)
