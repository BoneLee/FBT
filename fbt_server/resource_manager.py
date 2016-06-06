#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'bone-lee'

from time import time
from datetime import datetime
import operator
from tornado import gen
import simplejson as json

# import copy
from fbt_user_res_manager import FBTUserResourceManager
from resource_info import ResourceInfo
from fb_manager import FBCoinManager
from fileNameSearcher import FileNameSearcher
from util import gen_file_id
from redis_pub_sub_client import RedisPubClient
from constant import CHANNEL_RES_UPLOAD
from download_medium import DownloadMedium
import motorclient
import logging


class ResourceStoreManager(object):
    '''
    memory resources
    # a resource in all_resources DB such as
    #   {
    #   file_hash: file_hash1,
    #   file_name: xxx,
    #   main_type: 0~5, #see ResourceType
    #   sub_type: 0~3,
    #   file_size: 1234,
    #   mtime: 2014-3-4,
    #   tags: [tag1,tag2,...]
    #   owners: [{uid:uid1, is_public: 1},...]
    #   grades: [{uid:uid1, score: grade1},...]
    #   comments: [{who: user_name1, uid: uid1, content: the content of comment, ctime: 2014-4-3},...]
    #   download_num: 123
    #   public: 1 or 0
    #   },
    #
    # 这里做如下假设：(1)　all_resources　中个资源都有file_id字段；(2)　所有新客户端之后的调用都会传size
    #
    # 关于(2)(3)点问题：老版本的客户端会有问题，看怎么协调
    #
    # 做如下实现：(1)文件夹中的文件的file_hash一般为正常file_hash，当文件夹中的文件不能方便地与文件夹标识共存时，其file_hash代表为[directory file_hash]+"_"+
    # [file numbers of the directory] + "+" + [file file_hash]，由服务器负责拆装和合并等相关维护，而客户端请求子文件信息时，需要传所属文件夹的file_id（作为原来函数的最后一个
    # 默认参数）；(2)文件夹信息放在all_resources中，与基本文件信息相似，有所拥有文件的file_id列表，即file_ids；
    # (3)get_my_resource, get_private_resources除返回文件夹所有file_id列表外，还会返回个人拥有的文件夹的子文件列表'file_ids_downloaded'
    #
    # 注：resources_of_user，coins_of_user中的资源，会出现子文件file_id、普通文件file_id 2种形式。
    #
    # 这里有两点问题：(1)下载次数应该计在文件夹还是子文件--all concerned；(2)加扣积分机制还须完善。
    # 
    # a directory resource in all_resources DB such as
    #   {
    #   file_hash: file_hash1,
    #   file_name: xxx,
    #   main_type: 0~5, #see ResourceType
    #   sub_type: 0~3,
    #   file_size: 1234,
    #   mtime: 2014-3-4,
    #   tags: [tag1,tag2,...]
    #   owners: [{uid:uid1, is_public: 1},...]  (deprecated) to needed
    #   grades: [{uid:uid1, score: grade1},...]
    #   comments: [{who: user_name1, uid: uid1, content: the content of comment, ctime: 2014-4-3},...]
    #   download_num: 123 (the total download numbers of files in this directory), when return to client, divided by size
    #   file_ids: [file_id1, file_id2...]  (new added)
    #   public: 1 or 0
    #   },

    # a resource  representing a file under a directory in dir_resources DB such as
    # {
    #   file_hash: file_hash1,
    #   file_name: xxx,
    #   file_id: xxx,
    #   file_size: 1234,
    #   public: 1 or 0
    #   owners: [{uid:uid1, is_public: 1},...], 
    #   download_num: 123,
    #   dir_id: xxx     (the file_id of the directory to which this file belong)
    # }

    # a resource in resources_of_user DB such as
    # items in file_hashes should be file_id
    # such as {uid : uid1, file_hashes : [file_hash1,file_hash2], file_ids : [file_id1, file_2, ...}

    # a tag in tags DB such as
    # items in file_hashes should be file_id
    # {tag : tag1, file_hashes : [file_hash1,file_hash2,...]} , file_ids : [file_id1, file_2, ...] ...}

    # user_of_dir_id
    # {user_dir_id: user_dir_id1, dir_id: dir_id1}

    For is_reward:
    all_resources: None or owners = [] => reward = 1
    all_resources: reward = 1, and is_reward = 1 => do nothing
                                                   but  is_reward = 0 => rm reward, tobeaudit = 1
    all_resources: reward not exists, and is_reward = 1 or 0 => do nothing

    resource_tobeaudit():
    if reward exists, unset reward, tobeaudit = 1
    else do nothing
    '''
    _db = motorclient.fbt
    res_sort_by = {"time": 0, "download_num": 1, "online_num": 2}
    _ASCENDING = 1
    _DESCENDING = -1
    _nav_info_cache = None
    _nav_info_update_time = None

    @classmethod
    def set_db(cls, db):
        cls._db = db

    @classmethod
    def get_sort_item(cls, sort):
        if sort is None:
            return None
        if sort == 0:
            return "mtime"
        for k, v in cls.res_sort_by.iteritems():
            if sort == v:
                return k
        return None

    @classmethod
    @gen.coroutine
    def get_one_resource(cls, file_id, version = "2.0"):
        res = yield cls._db.all_resources.find_one({"file_id": file_id})
        if res:
            one_resource = cls.extract_resource_from_db(res, version)
            raise gen.Return(one_resource)
        else:
            raise gen.Return(None)

    @classmethod
    @gen.coroutine
    def get_summary(cls, file_id, version = "2.0"):
        res = yield cls._db.all_resources.find_one({"file_id": file_id}, {"exp_info": 1})
        if res and "exp_info" in res:
            summary = res["exp_info"]["summary"]
            raise gen.Return(summary)
        else:
            raise gen.Return(None)

    @classmethod
    @gen.coroutine
    def get_resources_count(cls, res_type):
        # cursor = cls._db.all_resources.find({"hidden": {"$ne": 1}, "public": 1, "main_type": res_type},{"file_hash":1})
        #cursor = yield cursor.to_list(None)
        #size = len(cursor)
        #raise gen.Return(size)
        # the following is better
        size = yield cls._db.all_resources.find({"hidden": {"$ne": 1}, "public": 1, "main_type": res_type}).count()
        #size = 10000
        raise gen.Return(size)

    # @classmethod
    # @gen.coroutine
    # def get_one_resources_count(cls, uid):
    #     cursor = yield cls._db.resources_of_user.find_one({'uid': uid}, {"file_ids": 1})
    #     size = 0
    #     file_in_dir = set()
    #     if cursor and "file_ids" in cursor:
    #         for f in cursor["file_ids"]:
    #             if '+' in f:
    #                 dir_id, file_id = f.split('+')
    #                 if dir_id not in file_in_dir:
    #                     file_in_dir.add(dir_id)
    #                     size += 1
    #             else:
    #                 size += 1
    #     raise gen.Return(size)

    @classmethod
    @gen.coroutine
    def get_one_resources_count(cls, uid):
        size = 0
        file_in_dir = set()
        res_list = yield FBTUserResourceManager.instance().get_resource_of_user(uid)
        for f in res_list:
            if '+' in f:
                dir_id, file_id = f.split('+')
                if dir_id not in file_in_dir:
                    file_in_dir.add(dir_id)
                    size += 1
            else:
                size += 1
        raise gen.Return(size)

    @classmethod
    @gen.coroutine
    def get_file_name(cls, file_id):
        cursor = yield cls._db.all_resources.find_one({'file_id': file_id}, {"file_name": 1})
        name = None
        if cursor and "file_name" in cursor:
            name = cursor["file_name"]
        raise gen.Return(name)

    @classmethod
    @gen.coroutine
    def get_file_size(cls, file_hash):
        assert file_hash >= 0
        size = yield cls._db.all_resources.find({"file_hash": file_hash}, {"_id": 0, "file_size": 1}).count()
        if size == 1:
            resource = yield cls._db.all_resources.find_one({"file_hash": file_hash}, {"_id": 0, "file_size": 1})
            raise gen.Return(resource['file_size'])
        else:
            raise gen.Return(None)

    @classmethod
    @gen.coroutine
    def get_one_friend_resources_count(cls, friend_uid_list):
        # TODO FIXME too complex
        size = 0
        for uid in friend_uid_list:
            size += yield cls.get_one_resources_count(uid)
        raise gen.Return(size)

    @classmethod
    @gen.coroutine
    def clear_db(cls):
        # just for test. DO NOT use.
        yield cls._db.all_resources.remove()
        yield cls._db.dir_resources.remove()
        yield cls._db.resources_of_user.remove()
        yield cls._db.tags.remove()

    @classmethod
    @gen.coroutine
    def get_resources_list(cls):
        cursor = cls._db.all_resources.find({}, {"_id": 0})
        all_resources = yield cursor.to_list(None)
        res_list = [res for res in all_resources]
        raise gen.Return(res_list)

    @classmethod
    def filter_file_ids(cls, file_ids):
        file_in_dir = {}
        my_resource_list = list()
        for f in file_ids: #reversed(file_ids):
            if '+' in f:
                dir_id, file_id = f.split('+')
                if dir_id in file_in_dir:
                    file_in_dir[dir_id].append(file_id)
                else:
                    file_in_dir[dir_id] = [file_id]
                    my_resource_list.append(dir_id)
            else:
                my_resource_list.append(f)
        return my_resource_list

    # sort_by to be remove. sort by mtime by default.
    # @classmethod
    # @gen.coroutine
    # def get_my_resource(cls, version, uid, page, sort_by, max_resources_cnt_in_page):
    #     assert uid > 0
    #     assert page >= 1
    #     assert sort_by == cls.res_sort_by["time"] or sort_by == cls.res_sort_by["download_num"]
    #     assert max_resources_cnt_in_page > 0
    #     my_resource = yield cls._db.resources_of_user.find_one({'uid': uid})
    #     ret = list()
    #     if my_resource:
    #         my_resource_list = list()
    #         if "file_ids" in my_resource:
    #             my_resource_list =  cls.filter_file_ids(my_resource["file_ids"])
    #
    #         for file_id in my_resource_list[(page - 1) * max_resources_cnt_in_page:page * max_resources_cnt_in_page]:
    #             res = yield cls._db.all_resources.find_one({'file_id': file_id})
    #             if res:
    #                 one_resource = cls.extract_resource_from_db(res, version, True)
    #                 '''
    #                 # All files in dir which I have downloaded
    #                 if file_id in file_in_dir :
    #                     one_resource['file_ids'] = file_in_dir[file_id]
    #                 '''
    #                 ret.append(one_resource)
    #     raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_my_resource(cls, version, uid, page, sort_by, max_resources_cnt_in_page):
        assert uid > 0
        assert page >= 1
        assert sort_by == cls.res_sort_by["time"] or sort_by == cls.res_sort_by["download_num"]
        assert max_resources_cnt_in_page > 0
        ret = list()
        res_list = yield FBTUserResourceManager.instance().get_resource_of_user(uid)
        my_resource_list = cls.filter_file_ids(res_list)
        for file_id in my_resource_list[(page - 1) * max_resources_cnt_in_page:page * max_resources_cnt_in_page]:
            res = yield cls._db.all_resources.find_one({'file_id': file_id})
            if res:
                one_resource = cls.extract_resource_from_db(res, version, True)
                '''
                # All files in dir which I have downloaded
                if file_id in file_in_dir :
                    one_resource['file_ids'] = file_in_dir[file_id]
                '''
                ret.append(one_resource)
        raise gen.Return(ret)

    @classmethod
    def extract_resource_from_db(cls, res, version='1.8', need_private_owner=False, file_in_dir=None):
        one_resource = dict()
        one_resource['file_hash'] = res['file_hash']
        one_resource['file_id'] = res['file_id']
        one_resource['file_name'] = res['file_name']
        one_resource['main_type'] = res['main_type']
        one_resource['sub_type'] = res['sub_type']
        one_resource['file_size'] = res['file_size']
        one_resource['mtime'] = res['mtime']
        if 'is_v4' in res:
            one_resource['is_v4'] = res['is_v4']
        else:
            one_resource['is_v4'] = '0'

        if 'exp_info' in res and res['exp_info']:
            one_resource['ext_info'] = res['exp_info']
            if 'summary' in res['exp_info']:
                one_resource['ext_info']['summary'] = 'removed'
        if 'sticky' in res:
            one_resource['sticky'] = res['sticky']
        one_resource['tags'] = " ".join(tag for tag in res['tags'])
        one_resource['grades'] = dict()
        # TODO FIXME calculate the score when add score to DB
        map(lambda score1: operator.setitem(one_resource['grades'], score1['uid'], score1["score"]), res['scores'])
        total_score = \
            reduce(lambda score1, score2: {"score": score1['score'] + score2['score'], "uid": 0}, res['scores'])[
                "score"]
        one_resource['avg_grade'] = (total_score + 0.0) / len(res['scores'])
        if version < '2.0':
            one_resource['comments'] = res['comments']  # copy.deepcopy(res['comments']) #need deep copy #make a copy is safe to prevent change the value externally
        else:
            one_resource['grades'] = dict()
        if "download_num" not in res:
            res["download_num"] = 0
        one_resource['download_num'] = res['download_num']
        if 'file_ids' in res:
            dn = one_resource['download_num']
            file_num = res['file_size']
            
            one_resource['download_num'] = (dn + file_num - 1) / file_num
            file_hashes_list = list()
            file_sizes_list = list()
            '''
            if  file_in_dir :
                assert need_private_owner == True and isinstance(file_in_dir, list)
                for file_id in file_in_dir :
                    file_hash, file_size = file_id.split('_')
                    file_hashes_list.append(file_hash)
                    file_sizes_list.append(file_size)
            else :
            '''
            for file_id in res['file_ids']:
                file_hash, file_size = file_id.split('_')
                file_hashes_list.append(file_hash)
                file_sizes_list.append(file_size)
            one_resource['file_hashes'] = ','.join(file_hashes_list)
            one_resource['file_sizes'] = ','.join(file_sizes_list)

        if need_private_owner:
            owners = [owner['uid'] for owner in res['owners']]  # yield cls.get_resource_owners(k)
        else:
            owners = [owner['uid'] for owner in res['owners'] if owner['is_public']]  # yield cls.get_resource_owners(k)
        one_resource['total_owners_num'] = len(owners)
        if len(res["comments"]) > 0:
            one_resource['owner'] = res["comments"][0]["who"]
        else:
            one_resource['owner'] = '你猜'
        return one_resource

    @classmethod
    @gen.coroutine
    def get_resources_by_tag(cls, version, tag, page, max_resources_cnt_in_page):
        assert len(tag) > 0
        assert page > 0
        assert max_resources_cnt_in_page > 0
        ret = list()
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        index = start_index
        resources_with_tag = yield cls._db.tags.find_one({"tag": tag})
        size = 0
        if resources_with_tag and "file_ids" in resources_with_tag:
            to_remove = []
            size = len(resources_with_tag["file_ids"])
            for file_id in resources_with_tag["file_ids"][start_index:]:
                # can't see the private resource and tip_off resource
                res = yield cls._db.all_resources.find_one({"hidden": {"$ne": 1}, "public": 1, 'file_id': file_id})
                if res:
                    one_resource = cls.extract_resource_from_db(res, version)
                    ret.append(one_resource)
                    index += 1
                    if index == end_index:
                        break
                else:
                    to_remove.append(file_id)
            if len(to_remove):
                # print "to_remove:",to_remove
                for file_id in to_remove:
                    resources_with_tag["file_ids"].remove(file_id)
                yield cls._db.tags.save(resources_with_tag)
        result = {}
        result["size"] = size
        result["res"] = ret
        raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def search_resources(cls, version, key_word, page, sort_by, max_resources_cnt_in_page):
        assert len(key_word) > 0
        assert page >= 1
        assert max_resources_cnt_in_page > 0
        if ResourceInfo.is_valid_tag(key_word):
            ret = yield cls.get_resources_by_tag(version, key_word, page, max_resources_cnt_in_page)
            raise gen.Return(ret)
        else:
            size, found_resources = yield FileNameSearcher().query_file_ids_by_file_name(key_word, page, max_resources_cnt_in_page, sort_by)
            ret = [cls.extract_resource_from_db(res, version) for res in found_resources]
            result = {}
            result["size"] = size
            result["res"] = ret
            raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def search_resources_private(cls, uid, version, key_word, page, sort_by, max_resources_cnt_in_page):
        assert len(key_word) > 0
        assert page >= 1
        assert max_resources_cnt_in_page > 0
        size, found_resources = yield FileNameSearcher().query_file_ids_by_file_name_private(uid, key_word, page, max_resources_cnt_in_page, sort_by)
        ret = [cls.extract_resource_from_db(res, version) for res in found_resources]
        result = {}
        result["size"] = size
        result["res"] = ret
        raise gen.Return(result)

    @classmethod
    @gen.coroutine
    def navigate_resources(cls, version, main_type, page, sort_by, max_resources_cnt_in_page,
                           tag=None, year=None, country=None):
        main_type = int(main_type)
        assert main_type >= 0
        assert page >= 1
        assert sort_by == cls.res_sort_by["time"] or sort_by == cls.res_sort_by["download_num"]
        assert max_resources_cnt_in_page > 0
        ret = list()
        search_key = {"hidden": {"$ne": 1}, "public": 1, "main_type": main_type}
        if tag and ResourceInfo.is_valid_tag(tag):
            search_key["tags"] = tag
        if year and ResourceInfo.is_valid_year(year):
            # TODO year is not a number FIX it in DB
            search_key["exp_info.year"] = year
        if country and ResourceInfo.is_valid_country(country):
            search_key["exp_info.countries"] = country
        cursor = None
        if sort_by == cls.res_sort_by["download_num"]:
            cursor = cls._db.all_resources.find(search_key).sort(
                [('hot.0.hot_day', cls._DESCENDING), ('mtime', cls._DESCENDING)])
        else:
            cursor = cls._db.all_resources.find(search_key).sort(
                [('mtime', cls._DESCENDING), ('hot.0.hot_day', cls._DESCENDING)])
        # size = yield cursor.count()
        cursor = cursor.limit(max_resources_cnt_in_page).skip((page - 1) * max_resources_cnt_in_page)  # skip page-1
        while (yield cursor.fetch_next):
            res = cursor.next_object()
            one_resource = cls.extract_resource_from_db(res, version)
            ret.append(one_resource)
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_private_resources(cls, version, friend_uid_list, page, max_resources_cnt_in_page):
        assert page >= 1
        # TODO FIXME
        # assert sort_by==cls.res_sort_by["time"] or sort_by==cls.res_sort_by["download_num"]
        assert max_resources_cnt_in_page > 0
        ret = list()
        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        index = 0
        for uid in friend_uid_list:
            assert uid > 0
            # It seems that 'reward' shouldn't be here  
            friend_resource = yield cls._db.resources_of_user.find_one({'uid': uid, 'reward':  {"$exists": False}})
            if friend_resource:
                if "file_ids" in friend_resource:
                    my_resource_list = list()
                    file_in_dir = {}
                    for f in friend_resource["file_ids"]:
                        if '+' in f:
                            dir_id, file_id = f.split('+')
                            if dir_id in file_in_dir:
                                file_in_dir[dir_id].append(file_id)
                            else:
                                file_in_dir[dir_id] = [file_id]
                        else:
                            my_resource_list.append(f)
                    if file_in_dir:
                        my_resource_list.extend(file_in_dir.keys())

                    for file_id in my_resource_list:
                        if index >= start_index and index < end_index:
                            res = yield cls._db.all_resources.find_one({'file_id': file_id})
                            if res:
                                '''
                                if file_id in file_in_dir :
                                    one_resource = cls.extract_resource_from_db(res, True, file_in_dir[file_id])
                                else :
                                '''
                                one_resource = cls.extract_resource_from_db(res, version, True)
                                ret.append(one_resource)
                        index += 1
                        if index == end_index:
                            break
            if index == end_index:
                break
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_resources_overview(cls, version, res_type, page, sort_by, max_resources_cnt_in_page):
        assert ResourceInfo.is_valid_main_type(res_type)
        assert page >= 1
        assert sort_by == cls.res_sort_by["time"] or sort_by == cls.res_sort_by["download_num"] or sort_by == \
                                                                                                   cls.res_sort_by[
                                                                                                       "online_num"]
        assert max_resources_cnt_in_page > 0

        (start_index, end_index) = ((page - 1) * max_resources_cnt_in_page, page * max_resources_cnt_in_page)
        if sort_by == cls.res_sort_by["download_num"]:
            cursor = cls._db.all_resources.find({"hidden": {"$ne": 1}, "public": 1, "main_type": res_type}).sort(
                [('sticky', cls._DESCENDING), ('hot.0.hot_day', cls._DESCENDING), ])
        else:
            cursor = cls._db.all_resources.find({"hidden": {"$ne": 1}, "public": 1, "main_type": res_type}).sort(
                [('mtime', cls._DESCENDING), ])
        cursor = cursor.limit(max_resources_cnt_in_page).skip(start_index)

        ret = list()
        while (yield cursor.fetch_next):
            res = cursor.next_object()
            one_resource = cls.extract_resource_from_db(res, version)
            ret.append(one_resource)
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_resources_by_file_ids(cls, version, hashes_list, file_size_list=None):
        assert len(hashes_list) > 0
        if file_size_list:
            assert len(file_size_list) == len(hashes_list)
        ret = list()
        for i, file_hash in enumerate(hashes_list):
            if file_size_list:
                size = long(file_size_list[i])
                if size != 0:
                    file_id = gen_file_id(file_hash, size)
                    res = yield cls._db.all_resources.find_one({'file_id': file_id})
                else:
                    res = yield cls._db.all_resources.find_one({'file_hash': file_hash})
            else:
                res = yield cls._db.all_resources.find_one({'file_hash': file_hash})
            if res:
                one_resource = cls.extract_resource_from_db(res, version)
                ret.append(one_resource)
        raise gen.Return(ret)

    @classmethod
    @gen.coroutine
    def get_resource_owners(cls, file_id, is_dir_file=False):
        # owners: {uid1: is_public,uid2: is_private,...}
        #res=yield motor.Op(cls.db.all_resources.find_one, {'file_hash': file_hash})
        if is_dir_file:
            res = yield cls._db.dir_resources.find_one({'file_id': file_id})
        else:
            res = yield cls._db.all_resources.find_one({'file_id': file_id})

        if res and "owners" in res:
            owners = [owner['uid'] for owner in res['owners']]  # if owner['is_public']] #
            raise gen.Return(owners)
        else:
            raise gen.Return([])

    @classmethod
    @gen.coroutine
    def get_resource_header(cls, file_id, dir_id=None):
        if dir_id:
            res = yield cls._db.dir_resources.find_one({'file_id': file_id})
        else:
            res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res:
            header_info = dict()
            header_info['file_size'] = res['file_size']
            header_info['file_name'] = res['file_name']
            header_info['file_hash'] = res['file_hash']
            # TODO: may be faster, when dir_names are stored with file informations
            if dir_id:
                res = yield cls._db.all_resources.find_one({'file_id': dir_id})
                header_info['dir_name'] = res['file_name']
            elif "file_ids" in res:
                header_info["isDir"] = True
            header_info['file_id'] = file_id
            raise gen.Return(header_info)
        else:
            raise gen.Return({})

    @classmethod
    @gen.coroutine
    def user_upload_dir(cls, is_reward, is_v4,
                        fileInfo, uid,
                        user_name,
                        file_hash,
                        file_name,
                        file_size,
                        is_public,
                        tags,
                        main_type,
                        sub_type,
                        res_grade,
                        comment, exp_info=None, userDirId=None):
        """
        Input:   fileInfo [{'hash': 567868, 'name': "test", "size": 1234}, {}]
                     uid: unique user id
                     user_name: user name registered
                     file_hash: file hash
                     file_name: file name
                     file_size: file size
                     is_public: is public share
                     tags: tags for resources
                     main_type: resource main type
                     sub_type: resource sub type
                     res_grade: resource grade by user
                     comment: user's comment

        """
        assert file_hash > 0
        assert len(file_name) > 0
        assert len(fileInfo) > 0
        assert uid > 0
        assert main_type >= 0
        assert sub_type >= 0
        assert file_size > 0
        assert len(user_name) > 0
        assert is_public == 0 or is_public == 1
        assert res_grade >= 0 and res_grade <= 10
        assert len(comment) > 0
        assert len(tags) > 0

        file_name = file_name.strip()
        comment = comment.strip()
        tags = [tag.strip() for tag in tags if len(tag.strip()) > 0]

        file_id = gen_file_id(file_hash, file_size)
        file_ids = [gen_file_id(i['hash'], i['size']) for i in fileInfo]
        resource_header = {'file_hash': file_hash, 'file_name': file_name, 'file_id': file_id, 'file_ids': file_ids,
                           'main_type': main_type, 'sub_type': sub_type,
                           'file_size': file_size, 'mtime': long(time())}
        # TODO: too expensive
        if exp_info:
            resource_header["exp_info"] = exp_info
        else:
            resource_header["exp_info"] = {}

        # userDirId_info = None
        # if userDirId:
        #     userDirId_info = yield cls._db.user_of_dir_id.find_one({'user_dir_id': userDirId})
        #     if userDirId_info:
        #         file_id = userDirId_info['dir_id']
        #         yield cls._db.all_resources.update({'file_id': file_id}, {"$inc":{'file_size': file_size},"$push": {"file_ids": {"$each": file_ids}}}, True)

        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        need_pub_res=False
        if not res:  # resource not in DB
            res_to_save = resource_header
            owner_doc = {"uid": uid, "is_public": is_public}
            if is_public:  # private resource will not be audited
                if not is_reward:
                    res_to_save["tobeaudit"] = 1
                res_to_save["hidden"] = 1
                need_pub_res=False
            else:
                need_pub_res=True

            if is_reward:
                res_to_save["reward"] = 1

            res_to_save['owners'] = [owner_doc]
            resource_comment = {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())}
            res_to_save["comments"] = [resource_comment]

            score_doc = {"uid": uid, "score": res_grade}
            res_to_save['scores'] = [score_doc]
            res_to_save['hot'] = [{"download_num_day": 0, "hot_day": 0}]
            res_to_save['public'] = is_public
            res_to_save['is_v4'] = is_v4
            res_to_save["tags"] = []
            for tag in tags:
                if len(tag) and (tag not in res_to_save["tags"]):
                    res_to_save["tags"].append(tag)
            yield cls._db.all_resources.insert(res_to_save)
        else:
            # yield cls._update_resource_header(file_hash, resource_header, file_size)
            if not res["owners"]:
                if is_reward:
                    yield cls._db.all_resources.update({"file_id": file_id}, {"$set": {"reward": 1}}, True)
            else:
                if 'reward' in res and not is_reward:
                    yield cls._db.all_resources.update({"file_id": file_id}, {"$unset": {"reward": 1}, "$set": {"tobeaudit": 1}}, True)

            resource_comment = {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())}
            yield cls._add_resource_comment(file_id, resource_comment)
            yield cls._add_resource_score(file_id, uid, res_grade)
            yield cls._add_tags_for_resource(file_id, tags)

            yield cls._add_resource_owner(file_id, uid, is_public, res)
            need_pub_res=True
        if need_pub_res:
            RedisPubClient().publish(json.dumps({"file_id": file_id, "file_name": file_name, "uid": uid, "is_subfile": False}), CHANNEL_RES_UPLOAD)

        yield cls._add_resource_for_tag(file_id, tags)
        yield cls._add_file_in_dir_to_my_resource_list(uid, [file_id + '+' + i for i in file_ids])

        for f in fileInfo:
            fileHash = f['hash']  # '+'.join([file_id, str(f['hash'])])
            fileSize = f['size']
            fileName = f['name']
            yield cls.user_upload_fileInDir_resource(uid, fileHash, fileName, fileSize, is_public, file_id)

        # if not userDirId_info:
        #     yield cls._db.user_of_dir_id.insert({'user_dir_id': userDirId, 'dir_id': file_id})

    @classmethod
    @gen.coroutine
    def user_upload_fileInDir_resource(cls, uid,
                                       file_hash,
                                       file_name,
                                       file_size,
                                       is_public,
                                       dir_id):
        assert file_hash > 0
        file_name = file_name.strip()
        assert len(file_name) > 0
        assert uid > 0
        assert file_size > 0
        assert is_public == 0 or is_public == 1

        file_id = gen_file_id(file_hash, file_size)
        resource_header = {'file_hash': file_hash, 'file_name': file_name, 'file_id': file_id, 'file_size': file_size}
        res = yield cls._db.dir_resources.find_one({'file_id': file_id})
        owner_doc = {"uid": uid, "is_public": is_public}
        if not res:  # resource not in DB
            res_to_save = resource_header
            res_to_save['owners'] = [owner_doc]
            res_to_save['public'] = is_public
            res_to_save['dir_id'] = dir_id
            yield cls._db.dir_resources.insert(res_to_save)
        else:
            # yield cls._db.dir_resources.update({"file_id": file_id}, {"$set": resource_header}, True)
            yield cls._add_fileInDIr_resource_owner(file_id, uid, is_public, dir_id, res)
        RedisPubClient().publish(json.dumps({"file_id": file_id, "file_name": file_name, "uid": uid, "is_subfile": True}), CHANNEL_RES_UPLOAD)

    @classmethod
    @gen.coroutine
    def user_upload_resource(cls, is_reward, is_v4,  # user download type
                             uid,  # unique user id
                             user_name,  #user name registered
                             file_hash,  #file hash
                             #blocks_hash,#file blocks(4KB for each block) hash
                             file_name,  #file name
                             file_size,  #file size
                             is_public,  #is public share
                             tags,  #tags for resources
                             main_type,  #resource main type
                             sub_type,  #resource sub type
                             res_grade,  #resource grade by user
                             comment, exp_info=None):  # user's comment
        file_hash = long(file_hash)
        assert file_hash > 0
        file_name = file_name.strip()
        assert len(file_name) > 0
        uid = long(uid)
        assert uid > 0
        main_type = int(main_type)
        sub_type = int(sub_type)
        assert main_type >= 0
        assert sub_type >= 0
        assert file_size > 0
        assert len(user_name) > 0
        assert is_public == 0 or is_public == 1
        assert res_grade >= 0 and res_grade <= 10
        comment = comment.strip()
        assert len(comment) > 0

        tags = [tag.strip() for tag in tags if len(tag.strip()) > 0]
        assert len(tags) > 0

        file_id = gen_file_id(file_hash, file_size)
        resource_header = {'file_hash': file_hash, 'file_name': file_name, 'file_id': file_id,
                           'main_type': main_type, 'sub_type': sub_type,
                           'file_size': file_size, 'mtime': long(time())}
        if exp_info:
            resource_header["exp_info"] = exp_info
        else:
            resource_header["exp_info"] = {}
        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        need_pub_res = False
        if not res:  #resource not in DB
            res_to_save = resource_header
            if is_public:  # private resource will not be audited
                if not is_reward:
                    res_to_save["tobeaudit"] = 1
                res_to_save["hidden"] = 1
                need_pub_res = False
            else:
                need_pub_res = True

            if is_reward:
                res_to_save["reward"] = 1

            resource_comment = {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())}
            res_to_save["comments"] = [resource_comment]

            score_doc = {"uid": uid, "score": res_grade}
            res_to_save['scores'] = [score_doc]
            res_to_save['hot'] = [{"download_num_day": 0, "hot_day": 0}]
            res_to_save['is_v4'] = is_v4

            owner_doc = {"uid": uid, "is_public": is_public}
            res_to_save['owners'] = [owner_doc]
            res_to_save['public'] = is_public

            res_to_save["tags"] = []
            for tag in tags:
                if len(tag) and (tag not in res_to_save["tags"]):
                    res_to_save["tags"].append(tag)
            yield cls._db.all_resources.insert(res_to_save)
            # if is_public:
            #     yield FileNameSearcher().file_id_add_title(file_id, file_name)
        else:
            #yield cls._update_resource_header(file_hash, resource_header)
            if not res["owners"]:
                if is_reward:
                    yield cls._db.all_resources.update({"file_id": file_id}, {"$set": {"reward": 1}}, True)
            else:
                if 'reward' in res and not is_reward:
                    yield cls._db.all_resources.update({"file_id": file_id}, {"$unset": {"reward": 1}, "$set": {"tobeaudit": 1}}, True)

            resource_comment = {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())}
            yield cls._add_resource_comment(file_id, resource_comment)
            yield cls._add_resource_score(file_id, uid, res_grade)
            yield cls._add_resource_owner(file_id, uid, is_public)
            yield cls._add_tags_for_resource(file_id, tags)
            need_pub_res = True
        if need_pub_res:
            RedisPubClient().publish(json.dumps({"file_id": file_id, "file_name": file_name, "uid": uid, "is_dir": False}),
                                     CHANNEL_RES_UPLOAD)

        yield cls._add_resource_for_tag(file_id, tags)
        yield cls._add_to_my_resource_list(uid, file_id)

    @classmethod
    @gen.coroutine
    def add_owner_when_download_over(cls, file_id, uid, dir_id=None):
        assert (uid >= 0)
        if dir_id:
            store_file_id = '+'.join([dir_id, file_id])
            yield cls._add_file_in_dir_to_my_resource_list(uid, [store_file_id])
            yield cls._add_fileInDIr_resource_owner(file_id, uid, None, dir_id)
            owners_cnt = yield cls._add_resource_owner(dir_id, uid, None)
        else:
            yield cls._add_to_my_resource_list(uid, file_id)
            owners_cnt = yield cls._add_resource_owner(file_id, uid, None)
        raise gen.Return(owners_cnt)

    @classmethod
    @gen.coroutine
    def remove_owner(cls, file_id, uid, isDir=False):
        assert (uid >= 0)
        if isDir:
            res = yield cls._db.dir_resources.find_one({'file_id': file_id})
            if res is None:
                logging.info("res file id not found:%s uid=%d is_dir:%s" % (file_id, uid, str(isDir)))
                return
            dir_id = res['dir_id']
            store_file_id = '+'.join([dir_id, file_id])
            modified_doc = yield cls._remove_from_my_resource_list(uid, store_file_id)
            if modified_doc is None:
                logging.info("modified_doc is None:%s uid=%d is_dir=%s dir_id=%s" % (file_id, uid, str(isDir), str(dir_id)))
                return
            need_del = not any((_.startswith(dir_id) for _ in modified_doc['file_ids']))
            if need_del:
                yield cls._remove_resource_owner(dir_id, uid)
            yield cls._remove_fileInDir_resource_owner(file_id, uid, dir_id)
        else:
            yield cls._remove_from_my_resource_list(uid, file_id)
            yield cls._remove_resource_owner(file_id, uid)

    @classmethod
    @gen.coroutine
    def add_comment(cls, file_id, uid, user_name, comment):
        uid = long(uid)
        assert uid >= 0
        assert len(user_name) > 0
        comment = comment.strip()
        assert len(comment) > 0
        resource_comment = {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())}
        yield cls._add_resource_comment(file_id, resource_comment)

    @classmethod
    @gen.coroutine
    def tip_off(cls, file_id, uid):
        assert uid > 0
        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res:
            if 'tip_off_users' not in res:
                res['tip_off_users'] = [uid]
            else:
                am_i_in = filter(lambda id: uid == id, res["tip_off_users"])
                if len(am_i_in) > 0:
                    assert len(am_i_in) == 1
                else:
                    res['tip_off_users'].append(uid)
                MAX_TIP_OFF_CNT = 100
                if len(res['tip_off_users']) == MAX_TIP_OFF_CNT:
                    assert "owners" in res
                    '''
                    for owner in res["owners"]:
                        if owner["is_public"]:
                            yield FBCoinManager.tip_off_sub(owner["uid"],file_hash)
                    for owner in res["tip_off_users"]:
                        yield FBCoinManager.tip_off_add(owner["uid"],file_hash)
                    '''
                    res["hidden"] = 1
                    # yield FileNameSearcher().remove_file_id(file_id, res['file_name'])
            yield cls._db.all_resources.save(res)

    @classmethod
    @gen.coroutine
    def add_score(cls, file_id, uid, score):
        assert uid >= 0
        assert score >= 0 and score <= 10
        yield cls._add_resource_score(file_id, uid, score)

    @classmethod
    @gen.coroutine
    def increase_download_num(cls, file_id, dir_id=None):
        # yield cls._db.all_resources.update({'file_hash': file_hash}, {'$inc': {"hot.0.download_num_day":1,'download_num': 1}}, True)
        if dir_id:
            res = yield cls._db.all_resources.find_one({'file_id': dir_id})
            yield cls._db.dir_resources.update({'file_id': file_id}, {'$inc': {'download_num': 1}}, True)
        else:
            res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res:
            if "hot" not in res:
                res["hot"] = [{"download_num_day": 0, "hot_day": 0}]
            if "download_num" not in res:
                res["download_num"] = 0
            res["hot"][0]["download_num_day"] += 1
            res["download_num"] += 1
            if res["download_num"] == 100:
                yield FBCoinManager.hot100_resource(res["owners"][0]["uid"], file_id)
            elif res["download_num"] == 500:
                yield FBCoinManager.hot500_resource(res["owners"][0]["uid"], file_id)
            yield cls._db.all_resources.save(res)
            if dir_id:
                raise gen.Return(res["download_num"]/res["file_size"])
            else:
                raise gen.Return(res["download_num"])
        else:
            raise gen.Return(0)

    @classmethod
    @gen.coroutine
    def _add_to_my_resource_list(cls, uid, file_id):
        yield FBTUserResourceManager.instance().add_to_my_resource_list(uid, file_id)

    # @classmethod
    # @gen.coroutine
    # def _add_to_my_resource_list(cls, uid, file_id):
    #     assert (uid >= 0)
    #     yield cls._db.resources_of_user.update({"uid": uid}, {"$push": {"file_ids": file_id}}, True)

    @classmethod
    @gen.coroutine
    def _add_file_in_dir_to_my_resource_list(cls, uid, file_ids):  # file_ids is a list of file_id
        yield FBTUserResourceManager.instance().add_file_in_dir_to_my_resource_list(uid, file_ids)

    # @classmethod
    # @gen.coroutine
    # def _add_file_in_dir_to_my_resource_list(cls, uid, file_ids):  # file_ids is a list of file_id
    #     assert (uid >= 0)
    #     assert (isinstance(file_ids, list))
    #     yield cls._db.resources_of_user.update({"uid": uid}, {"$push": {"file_ids": {"$each": file_ids}}}, True)

    @classmethod
    @gen.coroutine
    def _remove_from_my_resource_list(cls, uid, file_id):
        modified_doc = yield FBTUserResourceManager.instance().remove_from_my_resource_list(uid, file_id)
        raise gen.Return(modified_doc)

    # @classmethod
    # @gen.coroutine
    # def _remove_from_my_resource_list(cls, uid, file_id):
    #     assert (uid >= 0)
    #     modified_doc = yield cls._db.resources_of_user.find_and_modify({"uid": uid}, {"$pull": {"file_ids": file_id}},
    #                                                                    new=True)
    #     raise gen.Return(modified_doc)

    @classmethod
    @gen.coroutine
    def _add_resource_owner(cls, file_id, uid, is_public, res=None):
        '''
        resource owners in all_resources db is like, owners: [{"uid":uid1, "is_public":1}, {"uid": uid2, is_public: 0},...]
        '''
        assert (uid >= 0)
        unknown = None
        assert (is_public == 0 or is_public == 1 or is_public == unknown)

        if not res:
            res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res:
            if is_public == unknown:  # check history public attr and inherit it
                if "public" in res:
                    is_public = res["public"]
                else:
                    is_public = 1
            owner_doc = {"uid": uid, "is_public": is_public}
            if 'owners' not in res:
                res['owners'] = [owner_doc]
                # res['public'] = is_public
            else:
                am_i_in = filter(lambda owner: uid == owner['uid'], res["owners"])
                if len(am_i_in) > 0:
                    assert len(am_i_in) == 1
                    am_i_in[0]["is_public"] = is_public
                else:
                    res['owners'].append(owner_doc)
            yield cls._db.all_resources.save(res)
            raise gen.Return(len(res['owners']))
        else:
            # print "warning: file not found. but the user want to use it! He is a hacker..."
            raise gen.Return(0)

    @classmethod
    @gen.coroutine
    def _add_fileInDIr_resource_owner(cls, file_id, uid, is_public, dir_id, res=None):
        '''
        resource owners in all_resources db is like, owners: [{"uid":uid1, "is_public":1}, {"uid": uid2, is_public: 0},...]
        '''
        assert (uid >= 0)
        unknown = None
        assert (is_public == 0 or is_public == 1 or is_public == unknown)

        if not res:
            res = yield cls._db.dir_resources.find_one({'file_id': file_id})
        if res:
            if is_public == unknown:  # check history public attr and inherit it
                if "public" in res:
                    is_public = res["public"]
                else:
                    is_public = 1
            owner_doc = {"uid": uid, "is_public": is_public}
            am_i_in = filter(lambda owner: uid == owner['uid'], res["owners"])
            if len(am_i_in) > 0:
                assert len(am_i_in) == 1
                am_i_in[0]["is_public"] = is_public
            else:
                res['owners'].append(owner_doc)
            yield cls._db.dir_resources.save(res)

    @classmethod
    @gen.coroutine
    def _remove_resource_owner(cls, file_id, uid):
        '''
        resource owners in all_resources db is like, owners: [{"uid":uid1, "is_public":1}, {"uid": uid2, is_public: 0},...]
        '''
        assert (uid >= 0)
        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res and 'owners' in res:
            am_i_in = filter(lambda owner: uid == owner['uid'], res["owners"])
            if len(am_i_in) > 0:
                assert len(am_i_in) == 1
                res["owners"].remove(am_i_in[0])
                if len(res["owners"]) == 0:
                    res["hidden"] = 1
                    yield FileNameSearcher().remove_file_id(file_id, res['file_name'])
                    #res["tobeaudit"] = 0
            yield cls._db.all_resources.save(res)

    @classmethod
    @gen.coroutine
    def _remove_fileInDir_resource_owner(cls, file_id, uid, dir_id):
        '''
        resource owners in dir_resources db is like, owners: [{"uid":uid1, "is_public":1}, {"uid": uid2, is_public: 0},...]
        '''
        assert (uid >= 0)
        res = yield cls._db.dir_resources.find_one({'file_id': file_id})
        if res and 'owners' in res:
            am_i_in = filter(lambda owner: uid == owner['uid'], res["owners"])
            if len(am_i_in) > 0:
                assert len(am_i_in) == 1
                res["owners"].remove(am_i_in[0])
                if len(res["owners"]) == 0:
                    #res["hidden"] = 1 # seems unnecessary
                    modified_doc = yield cls._db.all_resources.find_and_modify({"file_id": dir_id},
                                                                               {"$pull": {"file_ids": file_id}},
                                                                               new=True)
                    if modified_doc and not modified_doc['file_ids']:
                        yield cls._db.all_resources.update({"file_id": dir_id}, {"$set": {"hidden": 1}}, True)
                        yield FileNameSearcher().remove_file_id(dir_id, modified_doc['file_name'])
            yield cls._db.dir_resources.save(res)

    @classmethod
    @gen.coroutine
    def _add_resource_comment(cls, file_id, resource_comment):
        '''
        comments in all_resources db is like, comments: [{who: user_name1, uid: uid1, content: the content of comment, ctime: 2014-4-3},...]
        '''
        yield cls._db.all_resources.update({"file_id": file_id}, {"$push": {"comments": resource_comment}}, True)

    @classmethod
    @gen.coroutine
    def _add_resource_score(cls, file_id, uid, resource_score):
        '''
        grades in all_resources db is like, scores: [{uid: uid1, "score": grade1}, {uid: uid2, score:grade2},...]
        '''
        assert uid > 0
        assert resource_score >= 0 and resource_score <= 10
        score_doc = {"uid": uid, "score": resource_score}
        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res:
            if 'scores' not in res:
                res['scores'] = [score_doc]
            else:
                am_i_in = filter(lambda owner: uid == owner['uid'], res["scores"])
                if len(am_i_in) > 0:
                    assert len(am_i_in) == 1
                    am_i_in[0]["score"] = resource_score
                else:
                    res['scores'].append(score_doc)
            yield cls._db.all_resources.save(res)
        else:
            # print "warning: file not found. but the user want to score it! He is a hacker..."
            pass

    @classmethod
    @gen.coroutine
    def _add_resource_for_tag(cls, file_id, tags_list):
        '''
        tags db is like doc1 {tag: tag1, file_hashes: [file_hash1,file_hash2,...]}, ....
        '''
        assert (len(tags_list) > 0)
        for tag in tags_list:
            assert len(tag) > 0
            yield cls._db.tags.update({"tag": tag}, {"$addToSet": {"file_ids": file_id}}, True)

    @classmethod
    @gen.coroutine
    def _add_tags_for_resource(cls, file_id, tags_list):
        '''
        tags for all_resources is like {tags: [tag1,tag2,...]}
        '''
        assert len(tags_list) > 0
        yield cls._db.all_resources.update({"file_id": file_id}, {"$addToSet": {"tags": {"$each": tags_list}}},
                                           True)


    # TODO: check wither the files are inserted!
    @classmethod
    @gen.coroutine
    def get_files_from_dir(cls, dir_id, uid=None):
        '''
        Input:
                    uid : None for all public dir, otherwise my friend uid's download dirs
        return [{file_hash, file_size, file_name, download_num, online_owner_num, all_owner_num}]
        '''

        ret = list()
        if uid:
            # friend_resource = yield cls._db.resources_of_user.find_one({'uid': uid})
            res_list = yield FBTUserResourceManager.instance().get_resource_of_user(uid)
            if res_list:
                for f in res_list:
                    if '+' in f:
                        dirId, file_id = f.split('+')
                        if dirId == dir_id:
                            dres = yield cls._db.dir_resources.find_one({'file_id': file_id})
                            if dres:
                                one_resource = dict()
                                one_resource['file_hash'] = dres['file_hash']
                                one_resource['file_name'] = dres['file_name']
                                one_resource['file_size'] = dres['file_size']
                                if "download_num" not in dres:
                                    one_resource['download_num'] = 0
                                else:
                                    one_resource['download_num'] = dres['download_num']
                                one_resource['all_owner_num'] = len(dres['owners'])
                                one_resource["online_owners_num"] =min(int(DownloadMedium.get_online_owners_num_of_res(file_id)),one_resource['all_owner_num'])
                                ret.append(one_resource)
        else:
            res = yield cls._db.all_resources.find_one({'file_id': dir_id})
            if res and 'file_ids' in res:
                for file_id in res['file_ids']:
                    dres = yield cls._db.dir_resources.find_one({'file_id': file_id})
                    if dres:
                        one_resource = dict()
                        one_resource['file_hash'] = dres['file_hash']
                        one_resource['file_name'] = dres['file_name']
                        one_resource['file_size'] = dres['file_size']
                        if "download_num" not in dres:
                            one_resource['download_num'] = 0
                        else:
                            one_resource['download_num'] = dres['download_num']
                        one_resource['all_owner_num'] = len(dres['owners'])
                        one_resource["online_owners_num"] = DownloadMedium.get_online_owners_num_of_res(file_id)
                        ret.append(one_resource)
        raise gen.Return(ret)

    # TODO: check wither the files are inserted! 
    # @classmethod
    # @gen.coroutine
    # def get_files_from_dir(cls, dir_id, uid=None):
    #     '''
    #     Input:
    #                 uid : None for all public dir, otherwise my friend uid's download dirs
    #     return [{file_hash, file_size, file_name, download_num, online_owner_num, all_owner_num}]
    #     '''
    #
    #     ret = list()
    #     if uid:
    #         friend_resource = yield cls._db.resources_of_user.find_one({'uid': uid})
    #         if friend_resource and "file_ids" in friend_resource:
    #             for f in friend_resource["file_ids"]:
    #                 if '+' in f:
    #                     dirId, file_id = f.split('+')
    #                     if dirId == dir_id:
    #                         dres = yield cls._db.dir_resources.find_one({'file_id': file_id})
    #                         if dres:
    #                             one_resource = dict()
    #                             one_resource['file_hash'] = dres['file_hash']
    #                             one_resource['file_name'] = dres['file_name']
    #                             one_resource['file_size'] = dres['file_size']
    #                             if "download_num" not in dres:
    #                                 one_resource['download_num'] = 0
    #                             else:
    #                                 one_resource['download_num'] = dres['download_num']
    #                             one_resource['all_owner_num'] = len(dres['owners'])
    #                             one_resource["online_owners_num"] =min(int(DownloadMedium.get_online_owners_num_of_res(file_id)),one_resource['all_owner_num'])
    #                             ret.append(one_resource)
    #     else:
    #         res = yield cls._db.all_resources.find_one({'file_id': dir_id})
    #         if res and 'file_ids' in res:
    #             for file_id in res['file_ids']:
    #                 dres = yield cls._db.dir_resources.find_one({'file_id': file_id})
    #                 if dres:
    #                     one_resource = dict()
    #                     one_resource['file_hash'] = dres['file_hash']
    #                     one_resource['file_name'] = dres['file_name']
    #                     one_resource['file_size'] = dres['file_size']
    #                     if "download_num" not in dres:
    #                         one_resource['download_num'] = 0
    #                     else:
    #                         one_resource['download_num'] = dres['download_num']
    #                     one_resource['all_owner_num'] = len(dres['owners'])
    #                     one_resource["online_owners_num"] = DownloadMedium.get_online_owners_num_of_res(file_id)
    #                     ret.append(one_resource)
    #     raise gen.Return(ret)


    @classmethod
    @gen.coroutine
    def get_nav_info(cls):
        ONE_DAY = 24 * 3600
        if cls._nav_info_cache is None or cls._nav_info_update_time is None or \
                        (datetime.now() - cls._nav_info_update_time).seconds > ONE_DAY:
            cls._nav_info_cache = yield cls._generate_nav_info()
            cls._nav_info_update_time = datetime.now()
        raise gen.Return(cls._nav_info_cache)

    @classmethod
    @gen.coroutine
    def _generate_nav_info(cls):
        MAX_CNT = 20
        DESCENDING = -1
        types_with_exp_info = ResourceInfo.get_types_with_exp_info()
        ans = []
        for type in ResourceInfo.get_sorted_main_types():
            info = {"main_type": type, "what": ResourceInfo.get_main_type_by_index(type)}
            if type in types_with_exp_info:
                years = yield cls._db.all_resources.aggregate(
                    [{"$match": {"main_type": type, "exp_info.year": {"$exists": True}}},
                     {"$group": {"_id": "$exp_info.year", "count": {"$sum": 1}}},
                     {"$sort": {"count": DESCENDING}},
                     {"$limit": MAX_CNT}])
                countries = yield cls._db.all_resources.aggregate(
                    [{"$match": {"main_type": type, "exp_info.countries": {"$exists": True}}},
                     {"$unwind": "$exp_info.countries"},
                     {"$group": {"_id": "$exp_info.countries", "count": {"$sum": 1}}},
                     {"$sort": {"count": DESCENDING}},
                     {"$limit": MAX_CNT}])
                # TODO FIXME maybe there are bugs
                years["result"] = filter(lambda x: len(x['_id'].strip()) > 0, years["result"])
                info["year"] = sorted(years["result"], lambda x, y: cmp(int(y['_id']), int(x['_id'])))
                info["country"] = countries["result"]
            else:
                info["year"] = []
                info["country"] = []
            info["tag"] = ResourceInfo.get_tags_by_type(type)
            ans.append(info)
        raise gen.Return(ans)

    @classmethod
    @gen.coroutine
    def file_hash2file_id(cls, file_hash):
        assert file_hash >= 0
        # so ugly
        size = yield cls._db.all_resources.find({"file_hash": file_hash}, {"_id": 0, "file_id": 1}).count()
        if size == 1:
            resource = yield cls._db.all_resources.find_one({"file_hash": file_hash}, {"_id": 0, "file_id": 1})
            raise gen.Return(resource['file_id'])
        else:
            raise gen.Return(None)
    
    @classmethod
    @gen.coroutine
    def resource_tobeaudit(cls, file_id):
        """
        only for reward resource
        if reward exists, unset reward, tobeaudit = 1
        else do nothing
        """
        res = yield cls._db.all_resources.find_one({'file_id': file_id})
        if res and "reward" in res:
            yield cls._db.all_resources.update({"file_id": file_id}, {"$set": {"tobeaudit": 1}, "$unset": {"reward": 1}}, True)

    @classmethod
    def find_study_resource(cls, sync_db, file_id):
        # "exp_info" : { "resource_school" : "台湾大学", "resource_teacher" : "未知", "resource_course" : "Py教学", "resource_academy" : "信息学院" } }
        #         resource_header = {'file_hash': file_hash, 'file_name': file_name, 'file_id': file_id,
        #                    'main_type': main_type, 'sub_type': sub_type,
        #                    'file_size': file_size, 'mtime': long(time())}
        # ==>
        # for key in ("course", "teacher", "university", "college","filename", "resource_name","download_link","description","tag"):
        res = sync_db.all_resources.find_one({"file_id": file_id},{"_id":0,"file_id":1, "exp_info":1,
                                                                    "main_type":1,"file_name":1,"file_size":1,
                                                                    "tags":1, "comments":1, "owners":1,"scores":1})
        if res and ResourceInfo.is_study_res_type(res["main_type"]):
            return res
        else:
            return None
