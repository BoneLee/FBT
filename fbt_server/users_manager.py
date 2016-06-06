# -*- coding: utf-8 -*-
__author__ = 'bone-lee'

from redis_cluster_proxy import Redis
from abstract_searcher import AbstractSearcher
from university_db import UniversityDB
# from searcher import RedisFullTextSearcher
from es_search import ESSearch
from constant import ES_HOST, ES_PORT, STAR_CLASS
from es_mapping import user_none_analyze_fields, user_analyze_fields, user_index_mapping

from tornado import gen
import motorclient
import random
from time import time
from datetime import datetime
# from tornado.escape import to_unicode, utf8
import simplejson as json
from tornado.escape import utf8, to_unicode
import mongoclient
from pypinyin import pinyin, TONE2
from util import seconds_of_today_at_wee_hours


class UserManager(AbstractSearcher):
    _primary_db = motorclient.fbt_realtime
    _REDIS_CACHE_KEY_FOR_PASSWD = "user:passwd"
    _REDIS_SESSION_KEY_PREFIX = "session:"
    _REDIS_EXPERIENCE_TAG = "experience:tag:"
    _REDIS_USER_FOLLOWERS = "user:followers:"
    _REDIS_USER_TAG_LIST = "user:experience:tags:"
    _REDIS_USER_INFO = "user_info:"
    _REDIS_EXP_TAG_USERS = "experience:tag:users:"
    _DESCENDING = -1
    TWO_DAY = 2 * 24 * 3600  # TODO maybe this should be more long
    TWO_HOUR = 2 * 3600
    TWO_MINUTES = 120
    MAX_USER_CNT = 200
    TOP_STAR_USER_CNT = 100
    PAGE_NUM = 10

    register_info = {"SAME_PHONE": 3, "SAME_EMAIL": 2, "SAME_NICK": 1, "NOT_REGISTERED": 0}
    _redis_cache = Redis()

    def __init__(self, db=None, redis_cache=None, redis_db_man=None, es_host=None, es_port=None):
        self._db = db or motorclient.fbt
        self._redis_cache = redis_cache or Redis()
        super(UserManager, self).__init__(self._redis_cache)
        self._udb = UniversityDB()
        self.PREVIEW_FIELDS = {"user": 1, "uid": 1, "icon": 1, "password": 1,
            "tags": 1, "thumb_num": 1, "followers_num":1, "state": 1, "state_desc": 1,
            "honor": 1, "thanks_coin": 1, "real_name": 1, "desc": 1, "gender": 1,
            "answers_num":1, "nick_name": 1, 'university': 1, 'college': 1, "_id": 0}
        self._user_searcher = ESSearch(host=es_host or ES_HOST, port=es_port or ES_PORT,
                                       index_name="user_index",
                                       type_name="user",
                                       none_analyze_fields=user_none_analyze_fields,
                                       analyze_fields=user_analyze_fields,
                                       index_mapping=user_index_mapping)
        for _, v in STAR_CLASS.iteritems():
            self.PREVIEW_FIELDS[v] = 1
        # self._hot_board = HotBoard(self._db, ioloop.IOLoop.instance())

    @classmethod
    def set_db(cls, db):
        cls._primary_db = db

    @gen.coroutine
    def is_phone_registered(self, phone):
        db_user = yield self._db.users.find_one({"phone": phone}, {"phone": 1})
        if db_user:
            raise gen.Return(self.register_info["SAME_PHONE"])
        else:
            raise gen.Return(self.register_info["NOT_REGISTERED"])

    @gen.coroutine
    def register_user(self, user, passwd, user_icon_url, real_name, school, college, nick, gender, phone=None):
        uid = UserManager.generate_uid(user)
        new_user = {"uid": uid, 'user': user,'time':datetime.now().strftime('%Y-%m-%d %H:%M'), 'icon': user_icon_url,'desc': "",
            'real_name':real_name, 'phone': phone, 'qq':'', 'gender':gender, 'love_state':'', 'school':school, 'address':'',
            'university': school, 'college': college, 'password':UserManager.generate_salt_passwd(user, passwd), 'nick_name':nick, 'friends':[],
            'university_id': self._udb.get_university_id(school), "university_short_name": self._udb.get_short_name(school), 
            'index_ctime': long(time()),
        }

        yield self._db.users.insert(new_user)
        yield self._user_searcher.insert(uid, new_user)
        self.add_to_statistic(school, college, user)
        raise gen.Return(uid)

    def register_user_sync(self, user, passwd, user_icon_url, real_name, school, college, nick, gender, phone=None):
        uid = UserManager.generate_uid(user)
        new_user = {"uid": uid, 'user': user,'time':datetime.now().strftime('%Y-%m-%d %H:%M'), 'icon': user_icon_url,'desc': "",
            'real_name':real_name, 'phone': phone, 'qq':'', 'gender':gender, 'love_state':'', 'school':school, 'address':'',
            'university': school, 'college': college, 'password':UserManager.generate_salt_passwd(user, passwd), 'nick_name':nick, 'friends':[],
            'university_id': self._udb.get_university_id(school), "mocked": True, "university_short_name": self._udb.get_short_name(school)
        }
        db = mongoclient.fbt
        db.users.insert(new_user)
        self.add_to_statistic(school, college, user)
        return uid

    @gen.coroutine
    def user_chg_password(self, user, passwd):
        salted_passwd = UserManager.generate_salt_passwd(user, passwd)
        yield self._db.users.update({"user": user},{"$set":{"password": salted_passwd}})
        self.update_password_of_user_cache(user, salted_passwd)

    @classmethod
    @gen.coroutine
    def get_friend_list(cls, uid):
        assert uid > 0
        my = yield cls._primary_db.users.find_one({"uid": uid}, {"friends": 1})
        if my and "friends" in my:
            raise gen.Return([friend['uid'] for friend in my["friends"]])
        raise gen.Return([])

    @gen.coroutine
    def is_user_registered(self, email, nick_name):
        db_user = yield self._db.users.find_one({"user": email}, {"user": 1})
        if db_user:
            raise gen.Return(self.register_info["SAME_EMAIL"])
        db_user = yield self._db.users.find_one({"$or": [{"user": email}, {"nick_name": nick_name}]},
                                                       {"user": 1, "nick_name": 1})
        if db_user:
            if db_user["user"] == email:
                raise gen.Return(self.register_info["SAME_EMAIL"])
            else:
                raise gen.Return(self.register_info["SAME_NICK"])
        raise gen.Return(self.register_info["NOT_REGISTERED"])

    @gen.coroutine
    def is_email_registered(self, email):
        db_user = yield self._db.users.find_one({"user": email}, {"user": 1})
        if db_user:
            raise gen.Return(self.register_info["SAME_EMAIL"])
        else:
            raise gen.Return(self.register_info["NOT_REGISTERED"])

    @gen.coroutine
    def find_user_info(self, user, is_mine):
        filter_dict = {"uid": 1, "user": 1, "icon": 1, "real_name": 1, "password": 1, "thumb_num": 1, "tags": 1, "gender": 1,
                             "interested_tags": 1, 'university': 1, 'college': 1, "desc": 1, "birthday": 1, 'followers_num': 1,
                             "following_num": 1, "state": 1, "state_desc": 1, "honor": 1, "is_postgraduate_star": 1,
                             "is_certificate_star": 1, "is_USA_star": 1, "is_work_star": 1, "is_campus_star": 1, "is_internship_star": 1, "_id": 0}
        if is_mine:
            filter_dict.update({"qq": 1, "phone": 1})
        db_user = yield self._db.users.find_one({"user": user}, filter_dict)
        raise gen.Return(db_user)

    @gen.coroutine
    def find_user(self, user, preview=False):
        db_user = self.get_cached_user(user)
        if db_user is None:
            db_user = yield self._db.users.find_one({"user": user}, self.PREVIEW_FIELDS)
            if db_user:
                db_user["star_info"] = [v for k, v in STAR_CLASS.iteritems() if v in db_user]
                # TODO(bonelee.lzh) remove the code and put it other place
                coins_of_user = yield self._db.coins_of_user.find_one({"user": user}, {"coins_by_study": 1})
                if coins_of_user:
                    coins_by_study = coins_of_user.get('coins_by_study', 0)
                    if coins_by_study:
                        db_user['coins_by_study'] = int(coins_by_study)
                self.set_cached_user(user, db_user)
        if preview:
            if db_user and "password" in db_user:
                del db_user["password"]
        raise gen.Return(db_user)

    @gen.coroutine
    def find_user_by_nick(self, nick_name):
        db_user = yield self._db.users.find_one({"nick_name": nick_name}, self.PREVIEW_FIELDS)
        if db_user:
            self.set_cached_user(db_user["user"], db_user)
        raise gen.Return(db_user)


    @gen.coroutine
    def find_user_by_id(self, uid):
        db_user = yield self._db.users.find_one({"uid": uid},  self.PREVIEW_FIELDS)
        if db_user:
            self.set_cached_user(db_user["user"], db_user)
            if "password" in db_user:
                del db_user["password"]
        raise gen.Return(db_user)

    def set_cached_user(self, user, user_info, preview=False):
        if  preview:
            cached_key = self._REDIS_USER_INFO+"preview:"+user
        else:
            cached_key = self._REDIS_USER_INFO+user
        ONE_WEEK = 2 * 3600
        self._redis_cache.setex(cached_key, ONE_WEEK, json.dumps(user_info))

    def get_cached_user(self, user):
        cached_key = self._REDIS_USER_INFO+user
        cached_user = self._redis_cache.get(cached_key)
        if cached_user:
            db_user = json.loads(cached_user)
            return db_user
        else:
            return None

    def update_password_of_user_cache(self, user, new_passwd):
        user_info = self.get_cached_user(user)
        if user_info:
            user_info["password"] = new_passwd
            self.set_cached_user(user, user_info)

    @classmethod
    def generate_uid(cls, user):
        r = cls._generate_salt(user)
        tmp_uid = str(long(time())) + str(r)
        uid = long(tmp_uid)
        return uid

    @classmethod
    def generate_user_icon(cls):
        return str(random.randint(1, 36))

    @classmethod
    def _generate_salt(cls, user):
        random.seed(hash(user))
        r = random.randint(1, 10000)
        if r < 10:
            r = "000" + str(r)
        elif r < 100:
            r = "00" + str(r)
        elif r < 1000:
            r = "0" + str(r)
        return r

    @classmethod
    def generate_salt_passwd(cls, user, passwd):
        r = cls._generate_salt(user)
        return passwd + str(r)

    @gen.coroutine
    def change_college(self, user, university, college):
        self.add_to_statistic(university, college, user)
        updated_fields = {"university": university, "college": college, "university_short_name": self._udb.get_short_name(university),
                      "university_id": self._udb.get_university_id(university)}
        yield self._db.users.update({"user": user}, {"$set": updated_fields})
        db_user = self.get_cached_user(user)
        if db_user:
            yield self._user_searcher.update_multi_fields(db_user["uid"], updated_fields)
            db_user["university"] = university
            db_user["college"] = college
            self.set_cached_user(user, db_user)
            raise gen.Return(True)
        else:
            raise gen.Return(False)
    
    @gen.coroutine
    def set_star_user_info(self, user, university, college, degree, entrance_year, university_mail=None):
        db_user = self.get_cached_user(user)
        if db_user:
            db_user["university"] = university
            db_user["college"] = college
            db_user["entrance_year"] = entrance_year
            db_user["degree"] = degree
            db_user["university_mail"] = university_mail
            db_user["university_id"] = self._udb.get_university_id(university)
            self.set_cached_user(user, db_user)
        updated_fields = {"university": university, "college": college,
                           "university_id": self._udb.get_university_id(university),
                           "university_short_name": self._udb.get_short_name(university),
                           "degree": degree, "university_mail": university_mail, "entrance_year": entrance_year}
        user_info = yield self._db.users.find_and_modify({"user": user},
                                    {"$set": updated_fields})
        yield self._user_searcher.update_multi_fields(user_info["uid"], updated_fields)

    @gen.coroutine
    def change_user_info(self, user, university, college, gender, real_name, nick_name):
        self.add_to_statistic(university, college, user)
        updated_fields = {"university": university, "college": college,
                          "university_id": self._udb.get_university_id(university),
                          "university_short_name": self._udb.get_short_name(university),
                          "nick_name": nick_name, "real_name": real_name, 'gender': gender}
        user_info = yield self._db.users.find_and_modify({"user": user},
                                    {"$set": updated_fields})
        if user_info:
            # patch for user
            yield self._db.coins_of_user.update({"uid": user_info["uid"]}, {"$set": {"user": user_info["user"]}}, upsert=False)
        db_user = self.get_cached_user(user)
        yield self._user_searcher.update_multi_fields(user_info["uid"], updated_fields)
        if db_user:
            db_user["university"] = university
            db_user["college"] = college
            db_user["university_id"] = self._udb.get_university_id(university)
            db_user["nick_name"] = nick_name
            db_user["real_name"] = real_name
            db_user["gender"] = gender
            self.set_cached_user(user, db_user)

    @gen.coroutine
    def change_user_basic_info(self, user, info_dict):
        #yield self._db.users.update({"user": user}, {"$set": info_dict})
        user_info = yield self._db.users.find_and_modify({"user": user},
                                    {"$set": info_dict})
        if user_info:
            yield self._user_searcher.update_multi_fields(user_info["uid"], info_dict)
        preview_cached_key = self._REDIS_USER_INFO+"preview:"+user
        cached_key = self._REDIS_USER_INFO+user
        self._redis_cache.delete(preview_cached_key)
        self._redis_cache.delete(cached_key)

    @gen.coroutine
    def get_user_info(self, user):
        auth_fields = {"university": 1, "college": 1, "tags": 1,
                       "nick_name": 1, "entrance_year": 1, "degree": 1,
                       "real_name": 1, 'gender': 1, "_id": 0}
        for _, v in STAR_CLASS.iteritems():
            auth_fields[v] = 1
        ret = yield self._db.users.find_one({"user": user}, auth_fields)
        raise gen.Return(ret)

    @gen.coroutine
    def insert_my_tags(self, user, uid, tags_with_class):
        yield [self._db.users.update({"user": user}, {"$inc": {"tags."+tag: 1}, "$addToSet": {"tags_list": tag}}, upsert=True) for tag in tags_with_class]
        self._user_searcher.add_to_set(uid, "tags_list", tags_with_class)

    @gen.coroutine
    def insert_my_interested_tags(self, user, tag_with_class):
        assert ":" in tag_with_class
        tag_with_class = utf8(tag_with_class)
        user_info = yield self._db.users.find_and_modify({"user": user}, {"$addToSet": {"interested_tags": tag_with_class}}, upsert=True)
        pipe = self._redis_cache.pipeline()
        key = self._REDIS_EXPERIENCE_TAG+user
        pipe.sadd(key, tag_with_class)
        pipe.expire(key, self.TWO_DAY)
        pipe.execute()
        if user_info and "university_id" in user_info:
            university_id = user_info["university_id"]
            # self._hot_board.user_tag_change(user, university_id)

    @gen.coroutine
    def remove_my_interested_tags(self, user, tag_with_class):
        assert ":" in tag_with_class
        tag_with_class = utf8(tag_with_class)
        user_info = yield self._db.users.find_and_modify({"user": user}, {"$pull": {"interested_tags": tag_with_class}})
        pipe = self._redis_cache.pipeline()
        key = self._REDIS_EXPERIENCE_TAG+user
        pipe.srem(key, tag_with_class)
        pipe.expire(key, self.TWO_DAY)
        pipe.execute()
        if user_info and "university_id" in user_info:
            university_id = user_info["university_id"]
            # self._hot_board.user_tag_change(user, university_id)

    @gen.coroutine
    def get_my_interested_tags(self, user, force_db=False):
        key = self._REDIS_EXPERIENCE_TAG+user
        ret = self._redis_cache.smembers(key)
        if force_db or ret is None:
            data = yield self._db.users.find_one({"user": user}, {"interested_tags": 1})
            if data and "interested_tags" in data:
                tags = [utf8(tag) for tag in data["interested_tags"]]
                pipe = self._redis_cache.pipeline()
                key = self._REDIS_EXPERIENCE_TAG+user
                for tag in tags:
                    pipe.sadd(key, tag)
                pipe.expire(key, self.TWO_DAY)
                pipe.execute()
                raise gen.Return(set(tags))
            else:
                raise gen.Return(set())
        else:
            raise gen.Return(ret)

    @gen.coroutine
    def get_thumb_num(self, user):
        user = yield self._db.users.find_one({"user": user}, {"thumb_num": 1})
        if user and "thumb_num" in user:
            raise gen.Return(user["thumb_num"])
        else:
            raise gen.Return(0)

    @gen.coroutine
    def get_post_num_by_tag(self, user, tag_class):
        user_info = yield self.get_user_info(user)
        ret = 0
        tag_class = to_unicode(tag_class)
        if user_info and "tags" in user_info:
            for tag in user_info["tags"]:
                if tag_class in tag:
                    ret += 1
        raise gen.Return(ret)


    # TODO add to experience manager
    @gen.coroutine
    def inc_thumb_num(self, user):
        user_info = yield self._db.users.find_and_modify({"user": user}, {"$inc": {"thumb_num": 1}}, upsert=True)
        if user_info:
            user_info["thumb_num"] = 1 if "thumb_num" not in user_info else user_info["thumb_num"]+1
            if "uid" in user_info:
                yield self._user_searcher.update_multi_fields(user_info["uid"], {"thumb_num": user_info["thumb_num"]})

    @gen.coroutine
    def inc_thanks_coin(self, user, how_much):
        yield self._db.users.update({"user": user}, {"$inc": {"thanks_coin": how_much}}, upsert=True)

    @gen.coroutine
    def inc_answers_num(self, user):
        yield self._db.users.update({"user": user}, {"$inc": {"answers_num": 1}}, upsert=True)

    @gen.coroutine
    def follow(self, user, follower):
        if user == follower:
            return
        # TODO FIXME may this doc will exceed max 18MB.
        user1, user2 = yield [self._db.followers.find_and_modify({"user": user}, {"$addToSet": {"followers": follower}}, upsert=True),
               self._db.followers.find_and_modify({"user": follower}, {"$addToSet": {"following": user}}, upsert=True)]
        if not user1 or "followers" not in user1 or follower not in user1["followers"]:
            yield [self._db.users.update({"user": user}, {"$inc": {"followers_num": 1}}, upsert=True),
                   self._db.users.update({"user": follower}, {"$inc": {"following_num":1}}, upsert=True)]
            # pipe = self._redis_cache.pipeline()
            # key = self._REDIS_USER_FOLLOWERS+user
            # pipe.sadd(key, follower)
            # pipe.expire(key, self.TWO_DAY)
            # pipe.execute()
            raise gen.Return(True)
        else:
            raise gen.Return(False)

    @gen.coroutine
    def unfollow(self, user, follower):
        if user == follower:
            return
        # TODO FIXME may this doc will exceed max 18MB.
        user1, user2 = yield [self._db.followers.find_and_modify({"user": user}, {"$pull": {"followers": follower}}, upsert=True),
               self._db.followers.find_and_modify({"user": follower}, {"$pull": {"following": user}}, upsert=True)]
        if user1 and follower in user1["followers"]:
            yield [self._db.users.update({"user": user}, {"$inc": {"followers_num": -1}}),
                   self._db.users.update({"user": follower}, {"$inc": {"following_num": -1}})]
            # pipe = self._redis_cache.pipeline()
            # key = self._REDIS_USER_FOLLOWERS+user
            # pipe.srem(key, follower)
            # pipe.expire(key, self.TWO_DAY)
            # pipe.execute()
            raise gen.Return(True)
        else:
            raise gen.Return(False)

    @gen.coroutine
    def get_following_users(self, user):
        doc = yield self._db.followers.find_one({"user": user}, {"_id":0, "following":1})
        if doc and "following" in doc:
            ret = yield [self.find_user(_, True) for _ in doc["following"] if _]
        else:
            ret = []
        raise gen.Return(sorted(ret, key=lambda x: pinyin(to_unicode(("real_name" in x and x["real_name"]) or ""), style=TONE2)))

    @gen.coroutine
    def get_followers(self, user, use_cache=True):
        doc = yield self._db.followers.find_one({"user": user}, {"_id":0, "followers":1})
        if doc and "followers" in doc:
            ret = set(doc["followers"])
        else:
            ret = set()
        raise gen.Return(ret)

    @gen.coroutine
    def get_my_tags(self, user, use_cache=True):
        key = self._REDIS_USER_TAG_LIST+user
        tags = self._redis_cache.get(key)
        if use_cache and tags:
            ret = json.loads(tags)
        else:
            doc = yield self._db.users.find_one({"user": user}, {"_id":0, "tags":1})
            if doc and "tags" in doc:
                ret = doc["tags"]
                if ret:
                    self._redis_cache.setex(key, self.TWO_MINUTES, json.dumps(ret))
            else:
                ret = []
        raise gen.Return(ret)

    @gen.coroutine
    def get_user_by_tag(self, tag_with_class, university=None, use_cache=True):
        # TODO unit test and use cache
        if university:
            university = utf8(university)
            cache_key = "users:tagged:" + university + ":" + tag_with_class
        else:
            cache_key = "users:tagged:" + tag_with_class
        users_list_str = self._redis_cache.get(cache_key)
        if use_cache and users_list_str:
            users_list = json.loads(users_list_str)
        else:
            if university:
                cursor = self._db.users.find({"tags_list": tag_with_class, "university_id": self._udb.get_university_id(university)}, self.PREVIEW_FIELDS)
            else:
                cursor = self._db.users.find({"tags_list": tag_with_class}, self.PREVIEW_FIELDS)
            cursor = cursor.sort([("thumb_num", self._DESCENDING)]).limit(self.MAX_USER_CNT)
            users_list = yield cursor.to_list(None)
            self._redis_cache.setex(cache_key, 30 * 60, json.dumps(users_list))
        raise gen.Return(users_list)

    @gen.coroutine
    def get_user_by_thumb_num(self, university=None, page=1, use_cache=True):
        if university:
            cache_key = "users:recommended:" + university
        else:
            cache_key = "users:recommended"
        users_list_str = self._redis_cache.get(cache_key)
        if use_cache and users_list_str:
            users_list = json.loads(users_list_str)
        else:
            fields = dict(self.PREVIEW_FIELDS)
            del fields["password"]
            if university:
                cursor = self._db.users.find({"university_id": self._udb.get_university_id(university)}, fields)
            else:
                cursor = self._db.users.find({}, fields)
            cursor = cursor.sort([("thumb_num", self._DESCENDING)]).limit(self.MAX_USER_CNT)
            users_list = yield cursor.to_list(None)
            self._redis_cache.setex(cache_key, 60 * 60, json.dumps(users_list))
        raise gen.Return([(len(users_list) + self.PAGE_NUM - 1) / self.PAGE_NUM, page,
                      users_list[(page - 1) * self.PAGE_NUM:page * self.PAGE_NUM]])

    @gen.coroutine
    def search_user(self, keyword, current_page, use_cache=True):
        cache_key = "user:search:user:"+keyword
        self.record_keyword(keyword)
        cached_data = self._redis_cache.get(cache_key)
        if use_cache and cached_data:
            users = json.loads(cached_data)
        else:
            users = yield self._user_searcher.search(keyword)
            # users.sort(key=lambda x: x.get('thumb_num', 0), reverse=True)
            if users:
                self._redis_cache.setex(cache_key, 10*60, json.dumps(users))
            else:
                users = []
        total_res_num = len(users)
        raise gen.Return([(total_res_num+self.PAGE_NUM-1)/self.PAGE_NUM, current_page,
                          users[(current_page-1)*self.PAGE_NUM:self.PAGE_NUM*current_page]])

    @gen.coroutine
    def clear_search_db(self):
        yield self._user_searcher.clean_all()

    @gen.coroutine
    def star_user_helper(self, user, field, operation="set"):
        field = to_unicode(field)
        if field in STAR_CLASS:
            if operation == "set":
                yield self._db.users.update({"user": user}, {"$set": {STAR_CLASS[field]: 1}, "$addToSet": {"star_info": STAR_CLASS[field]}})
            else:
                yield self._db.users.update({"user": user}, {"$unset": {STAR_CLASS[field]: 1}, "$pull": {"star_info": STAR_CLASS[field]}})
            db_user = self.get_cached_user(user)
            if db_user:
                if operation == "set":
                    db_user[STAR_CLASS[field]] = 1
                else:
                    if STAR_CLASS[field] in db_user:
                        del db_user[STAR_CLASS[field]]
                self.set_cached_user(user, db_user)
            raise gen.Return(True)
        else:
            raise gen.Return(False)

    @gen.coroutine
    def set_star_user(self, user, field):
        ret = yield self.star_user_helper(user, field, "set")
        raise gen.Return(ret)

    @gen.coroutine
    def unset_star_user(self, user, field):
        ret = yield self.star_user_helper(user, field, "unset")
        raise gen.Return(ret)

    @gen.coroutine
    def get_top_star_users(self, use_cache=True):
        ret = {}
        for k,v in STAR_CLASS.iteritems():
            cache_key = "users:star:" + v
            users_list_str = self._redis_cache.get(cache_key)
            if use_cache and users_list_str:
                users_list = json.loads(users_list_str)
            else:
                cursor = self._db.users.find({"star_info": v}, self.PREVIEW_FIELDS)
                cursor = cursor.sort([("thumb_num", self._DESCENDING)]).limit(self.TOP_STAR_USER_CNT)
                users_list = yield cursor.to_list(None)
                if users_list:
                    self._redis_cache.setex(cache_key, 30 * 60, json.dumps(users_list))
            ret[k] = users_list
        raise gen.Return(ret)

    @gen.coroutine
    def get_some_recommended_users(self, page=1, use_cache=True):
        cache_key = "users:recommended:random"
        users_list_str = self._redis_cache.get(cache_key)
        if use_cache and users_list_str:
            users_list = json.loads(users_list_str)
        else:
            fields = dict(self.PREVIEW_FIELDS)
            del fields["password"]
            cursor = self._db.users.find({}, fields)
            cursor = cursor.sort([("thumb_num", self._DESCENDING)]).limit(200)
            users_list = yield cursor.to_list(None)
            if users_list:
                self._redis_cache.setex(cache_key, 30 * 60, json.dumps(users_list))
        raise gen.Return([(len(users_list)+self.PAGE_NUM-1)/self.PAGE_NUM, page,
                          users_list[((page-1)*self.PAGE_NUM):(page*self.PAGE_NUM)]])

    @gen.coroutine
    def get_rank(self):
        cache_key = "user:rank:by_total_study_coin"
        rank_list = self._redis_cache.get(cache_key)
        if not rank_list:
            res = yield self.get_total_rank_helper()
            rank_list = json.dumps({"data": res, "type": 6})
            self._redis_cache.setex(cache_key, 24 * 60, rank_list)
        raise gen.Return(rank_list)

    @gen.coroutine
    def get_total_rank_helper(self, sort_item="coins_by_study"):
        cursor2 = self._db.coins_of_user.find({}, {"uid": 1, sort_item: 1, "_id": 0, "user": 1}).sort([(sort_item, -1),]).limit(100)
        user_list = yield cursor2.to_list(None)
        ret = []
        for item in user_list:
            if "user" in item:
                user_info = yield self.find_user(item["user"], preview=True)
            else:
                user_info = yield self.find_user_by_id(item["uid"])
            if user_info:
                item_data = {}
                item_data["nick_name"] = user_info["nick_name"]
                item_data["icon"] = user_info["icon"]
                item_data["coin"] = int(item["coins_by_study"])
                item_data["uid"] = item["uid"]
                item_data["delta"] = item_data["coin"]
                item_data.update(user_info)
                ret.append(item_data)
        raise gen.Return(ret)

    def is_star_user(self, user_info):
        for _, v in STAR_CLASS.iteritems():
            if v in user_info:
                return True
        return False

    @gen.coroutine
    def get_today_users(self):
        fields = dict(self.PREVIEW_FIELDS)
        del fields["password"]
        cursor = self._db.users.find({"index_ctime": {"$gt": seconds_of_today_at_wee_hours()}}, fields)
        users_list = yield cursor.to_list(None)
        raise gen.Return(users_list)
