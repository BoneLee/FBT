# coding: utf8
__author__ = 'bone'

import mongoclient
from users_manager import UserManager
from QA_manager import UserAnswerThumbUpRecorder
from qiniu_utils import get_file_qetag_from_download_link, get_key_from_download_link
from qiniu_utils import office_to_pdf
from university_db import UniversityDB
from es_mapping import course_analyze_fields, course_index_mapping, course_none_analyze_fields
from es_mapping import resource_analyze_fields, resource_none_analyze_fields, resource_index_mapping

from tornado import gen, ioloop
import json
import os
import time
from tornado.escape import utf8
from es_search import ESSearch
from constant import *
from es_mapping import *

def main():
    db = mongoclient.fbt
    cnt = 0
    for item in db.questions.find({}):
        if "best_answer" in item and item["best_answer"]:
            user_info = db.users.find_one({"user": item["publisher"]}, {"desc": 1})
            item["user_description"] = user_info["desc"]
            print "user desc:", user_info["desc"]
            db.questions.save(item)
            cnt += 1
    print "fix cnt:", cnt


def fix_search():
    db = mongoclient.fbt
    cnt = 0
    man = UserManager()
    for item in db.users.find({}):
        if "university" in item and "college" in item and item["university"] and item["college"]:
            man.add_to_statistic(item["university"], item["college"], item["user"])
            print "user OK:", item["user"]
            cnt += 1
    print "all cnt:", cnt


def fix_top_recommend_users():
    thumb_up_recorder = UserAnswerThumbUpRecorder()
    db = mongoclient.fbt
    for exp in db.answers.find({}):
        tags_with_class = [utf8(exp["class2"]) + ":" + utf8(tag) for tag in exp["tags"]]
        if exp["thumb_up_num"] > 0:
            thumb_up_recorder.thumb_up_for_user(exp["publisher"], tags_with_class, exp["thumb_up_num"])


def random_num():
    while True:
        r = random.normalvariate(0, 5)
        ret = int(r)
        if 0 <= r <= 10:
            return ret


def fake_download_cnt():
    db = mongoclient.fbt
    cnt = 0
    for item in db.study_resources.find({}):
        if "download_num" in item:
            if item["download_num"] > 0:
                item["download_num"] *= 2
            else:
                item["download_num"] = random_num()
            cnt += 1
        db.study_resources.save(item)
    print "all cnt:", cnt

def fix_university():
    db = mongoclient.fbt
    cnt = 0
    for item in db.users.find({}):
        if "university" not in item or not item["university"]:
            if item["school"]:
                print item["user"]
                item["university"] = item["school"]
                db.users.save(item)
                cnt += 1
    print "all cnt:", cnt


@gen.coroutine
def fix_file_id():
    db = mongoclient.fbt
    cnt = 0
    for resource in db.study_resources.find({"file_hash": {"$exists": False}}).batch_size(30):
        if "download_link" not in resource:
            continue
        old_fid = resource["file_id"]
        download_link = utf8(resource["download_link"])
        data = json.loads(get_file_qetag_from_download_link(download_link))
        resource["file_hash"] = data["hash"]
        resource["file_key"] = get_key_from_download_link(download_link)
        # print item["file_id"]
        # print item["key"]
        res = db.study_resources.find_one({"file_hash": resource["file_hash"]}, {"_id": 1})
        if res:
            print resource["filename"], resource["university"], resource["college"], resource["course"]
            db.study_resources.remove({"file_id": old_fid})
            cnt += 1
        else:
            db.study_resources.save(resource)
        _, file_extension = os.path.splitext(resource["filename"])
        file_extension = file_extension.lower()[1:]
        preview_extensions = {"WORD": {"doc", "docx", "odt", "rtf", "wps"},
                              "PPT": {"ppt", "pptx", "odp", "dps"},
                              "EXCEL": {"xls", "xlsx", "ods", "csv", "et"},
                              "PDF": {"pdf"}}
        if file_extension in preview_extensions["WORD"] or \
                        file_extension in preview_extensions["PPT"] or \
                        file_extension in preview_extensions["EXCEL"] or \
                        file_extension in preview_extensions["PDF"]:
            if resource["file_size"] <= MAX_PREVIEW_SIZE:
                yield office_to_pdf(resource["file_key"], file_extension)
    print "cnt:", cnt
    for resource in db.auditing_study_resources.find({"file_hash": {"$exists": False}}).batch_size(30):
        if "download_link" not in resource:
            continue
        old_fid = resource["file_id"]
        download_link = utf8(resource["download_link"])
        data = json.loads(get_file_qetag_from_download_link(download_link))
        resource["file_hash"] = data["hash"]
        resource["file_key"] = get_key_from_download_link(download_link)
        # print item["file_id"]
        # print item["key"]
        res = db.auditing_study_resources.find_one({"file_hash": resource["file_hash"]}, {"_id": 1})
        if res:
            print resource["filename"], resource["university"], resource["college"], resource["course"]
            db.auditing_study_resources.remove({"file_id": old_fid}) 
            cnt += 1
        else:
            db.auditing_study_resources.save(resource)
    print "all cnt:", cnt 


@gen.coroutine
def fix_reward_preview_key():
    db = mongoclient.fbt
    cnt = 0
    for reward in db.study_reward.find().batch_size(30):
        if not reward["resource_list"]:
            continue
        for _ in reward["resource_list"]:
            for resource in _["uploaded_resources"]:
                if "file_hash" not in resource:
                    if "download_link" not in resource:
                        continue
                    download_link = utf8(resource["download_link"])
                    data = json.loads(get_file_qetag_from_download_link(download_link))
                    resource["file_hash"] = data["hash"]
                    resource["file_key"] = get_key_from_download_link(download_link)
                    db.study_reward.save(reward)
                    time.sleep(2)
                print "resource:", resource, " reward id:", reward["id"]
                _, file_extension = os.path.splitext(resource["filename"])
                file_extension = file_extension.lower()[1:]
                preview_extensions = {"WORD": {"doc", "docx", "odt", "rtf", "wps"},
                                      "PPT": {"ppt", "pptx", "odp", "dps"},
                                      "EXCEL": {"xls", "xlsx", "ods", "csv", "et"},
                                      "PDF": {"pdf"}}
                if file_extension in preview_extensions["WORD"] or \
                                file_extension in preview_extensions["PPT"] or \
                                file_extension in preview_extensions["EXCEL"]:
                    if resource["file_size"] <= MAX_PREVIEW_SIZE:
                        yield office_to_pdf(resource["file_key"], file_extension,
                                            callback_url=OUR_WEB_URL + "/preview_key_upload/" + reward["id"] + "/" + resource["file_hash"])
                        cnt += 1

    print "cnt:", cnt


@gen.coroutine
def fix_QA_search():
    db = mongoclient.fbt
    cnt = 0
    question_searcher = ESSearch(host=ES_HOST, port=ES_PORT,
                               index_name="question_index",
                               type_name="question",
                               analyze_fields=question_analyze_fields,
                               none_analyze_fields=question_none_analyze_fields,
                               index_mapping=question_index_mapping)
    for question in db.questions.find().batch_size(30):
        print question["title"], " is indexing...."
        yield question_searcher.insert(question["id"], question)
        cnt += 1
    print "all cnt:", cnt


@gen.coroutine
def fix_course_search():
    db = mongoclient.fbt
    cnt = 0
    course_searcher = ESSearch(host=ES_HOST, port=ES_PORT,
                               index_name="course_index",
                               type_name="course",
                               analyze_fields=course_analyze_fields,
                               none_analyze_fields=course_none_analyze_fields,
                               index_mapping=course_index_mapping)
    udb = UniversityDB()
    for course in db.courses.find().batch_size(30):
        print course["course"], " is indexing...."
        course["university_short_names"] = udb.get_short_name(course["university"])
        yield course_searcher.insert(course["course_id"], course)
        cnt += 1
    print "all cnt:", cnt


@gen.coroutine
def fix_resource_search():
    db = mongoclient.fbt
    cnt = 0
    resource_searcher = ESSearch(ES_HOST, port=ES_PORT,
                                 index_name="resource_index",
                                 type_name="resource",
                                 analyze_fields=resource_analyze_fields,
                                 none_analyze_fields=resource_none_analyze_fields,
                                 index_mapping=resource_index_mapping)
    udb = UniversityDB()
    for resourse in db.study_resources.find().batch_size(30):
        print resourse["filename"], " is indexing...."
        resourse["university_short_names"] = udb.get_short_name(resourse["university"])
        yield resource_searcher.insert(resourse["file_id"], resourse)
        cnt += 1
    print "all cnt:", cnt


@gen.coroutine
def fix_user_search():
    db = mongoclient.fbt
    cnt = 0
    user_searcher = ESSearch(host=ES_HOST, port=ES_PORT,
                             index_name="user_index",
                             type_name="user",
                             none_analyze_fields=user_none_analyze_fields,
                             analyze_fields=user_analyze_fields,
                             index_mapping=user_index_mapping)
    udb = UniversityDB()
    for user in db.users.find().batch_size(30):
        if "university" in user and "college" in user and user["university"] and user["college"]:
            user["university_short_name"] = udb.get_short_name(user["university"])
            print user["university"], user["real_name"], " is indexing...."
            yield user_searcher.insert(user["uid"], user)
            cnt += 1
    print "all cnt:", cnt


if __name__ == '__main__':
    ioloop.IOLoop.instance().run_sync(fix_QA_search)
    ioloop.IOLoop.instance().run_sync(fix_user_search)
    ioloop.IOLoop.instance().run_sync(fix_course_search)
    ioloop.IOLoop.instance().run_sync(fix_resource_search)
