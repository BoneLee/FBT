#-*- coding:utf-8 -*-
import re
import os
import tornadoredis
import motorclient
from cipher import WaveCipher as Cipher
from constant import *
from redis_handler import RedisHandler
from download_medium import DownloadMedium

import simplejson as json
from time import time
from datetime import datetime
import uuid
from tornado import gen
import logging
import tornado.ioloop

Cache_Expire = [30*60, 10*60, 5*60]
class transaction:
    '''
    args={"db": db_obj, "transaction": [{"collection": "collection", "action":"insert|update|remove", "argument":[...]},...]}
    '''
    def batch_exec(args):
        db = args["db"]
        db.transaction.insert({"status": "init", "transaction": args["transaction"]})
#redis for pubsub
class RedisSub(object):
    #@channel str
    #@callback function invoke when the sub msg come
    def __init__(self,channel,callback):
        self.callback = callback
        self.sub_client = tornadoredis.Client(host=PUB_SUB_HOST, password=PUB_SUB_PWD,port=PUB_SUB_PORT)
        self.channel = channel
        # self.subscribe()
        self.sub_client._io_loop.add_future(self.subscribe(), lambda future: self.sub_client.listen(self.on_redis_message))

    @gen.coroutine
    def subscribe(self):
        self.sub_client.connect()
        yield gen.Task(self.sub_client.subscribe, self.channel)
        # self.sub_client.listen(self.on_redis_message)

    def on_redis_message(self, message):
        # logging.info("Redis message received: "+str(message.body))
        kind, body = message.kind, message.body
        if kind == 'message' and self.callback:
            self.callback(body)
        if kind == 'disconnect':
            self.close()

    def close(self):
        if self.sub_client.subscribed:
            self.sub_client.unsubscribe(self.channel)
            self.sub_client.disconnect()
class RedisPub(object):
    _redisPub = None
    @staticmethod 
    def init():
        if not RedisPub._redisPub:
            RedisPub._redisPub = tornadoredis.Client(host=PUB_SUB_HOST, password=PUB_SUB_PWD,port=PUB_SUB_PORT)
    #@message str the publish message
    #@channel str the publish channel
    @staticmethod
    def publish(channel, message):
        RedisPub.init()
        # logging.info("Redis message send: " + message)
        RedisPub._redisPub.publish(channel, message)

class MemCache():
    _expire_time = {}
    _cache = {}
    _expire_limit = 24*60*60
    @staticmethod
    def get(key, name=None):
        cur_t = long(time())
        if name and name in MemCache._expire_time:
            t = MemCache._expire_time[name]
            if t[1] != -1 and cur_t - t[0] >= t[1]:
                MemCache._expire_time.pop(name, None)
                MemCache._cache.pop(name, None)
                return None
            else:
                if not key:
                    return MemCache._cache[name]
                if key in MemCache._cache[name]:
                    return MemCache._cache[name][key]
                else:
                    return None
        else:
            if key in MemCache._expire_time:
                t = MemCache._expire_time[key]
                if t[1] != -1 and cur_t - t[0] >= t[1]:
                    MemCache._expire_time.pop(key, None)
                    MemCache._cache.pop(key, None)
                    return None
                else:
                    return MemCache._cache.get(key)
            else:
                return None
    @staticmethod
    def set(key, value, name=None, expire=-1):
        if name:
            if name not in MemCache._cache:
                MemCache._cache[name] = {}
            MemCache._cache[name][key] = value
            if name not in MemCache._expire_time:
                MemCache._expire_time[name] = [long(time()), expire]
        else:
            MemCache._cache[key] = value
            MemCache._expire_time[key] = [long(time()), expire]
    @staticmethod
    def delete(key, name=None):
        if name:
            if key:
                (MemCache._cache[name]).pop(key, None)
            else:
                MemCache._cache.pop(name, None)
                MemCache._expire_time.pop(name, None)
        else:
            MemCache._cache.pop(key, None)
            MemCache._expire_time.pop(key, None)
    @staticmethod
    def clear():
        MemCache._expire_time = {}
        MemCache._cache = {}
    @staticmethod
    def clearFb():
        MemCache._expire_time.pop(WEEKLY_TOP, None)
        MemCache._expire_time.pop(MONTHLY_TOP, None)
        MemCache._expire_time.pop(TOTAL_RANK, None)
        MemCache._cache.pop(WEEKLY_TOP, None)
        MemCache._cache.pop(MONTHLY_TOP, None)
        MemCache._cache.pop(TOTAL_RANK, None)
    @staticmethod
    def clearRes():
        MemCache._expire_time.pop(RES_MAIN_180, None)
        MemCache._expire_time.pop(RES_MAIN_179, None)
        MemCache._cache.pop(RES_MAIN_180, None)
        MemCache._cache.pop(RES_MAIN_179, None)
    @staticmethod
    def save(port):
        out_time = open(port+"cache_time.json","w")
        out_time.write(json.dumps(MemCache._expire_time))
        out_time.close()
        out_c = open(port+"cache_content.json","w")
        out_c.write(json.dumps(MemCache._cache))
        out_c.close()
    @staticmethod
    def load(port):
        if os.path.isfile(port+"cache_time.json") and os.path.isfile(port+"cache_content.json"):
            in_time = open(port+"cache_time.json","r")
            MemCache._expire_time = json.load(in_time)
            in_time.close()
            in_c = open(port+"cache_content.json","r")
            MemCache._cache = json.load(in_c)
            in_c.close()

def log(msg):
    pass


'''
types:0 for error, 1 for fine
'''
def write(obj, types, error, result):
    msg = {}
    msg["type"] = types
    msg["error"] = error
    msg["result"] = result
    msg = json.dumps(msg)
    obj.set_header("Content-Type","application/json")
    obj.write(msg)

'''
types:0 for error, 1 for fine
'''
def write_d(obj, msg):
    obj.set_header("Content-Type","application/json")
    obj.write(msg)

'''
0 for param error, 1 for db error
'''
def errorHandle(obj, num):
    if num == 0:
        write(obj, 0, "400", {})
    elif num == 1:
        write(obj, 0, "sorry", {})

def del_space(s):
    if not s:
        return s
    tmp = ""
    for item in s:
        if item != " ":
            tmp += item
    return tmp

def g_cookie(s,name):
    name = name.strip()
    c = del_space(s.request.headers.get("Cookie"))
    if not c:
        c = s.get_argument("cookie","")
        if not c:
            return None
    cookie = json.loads(c)
    if name in cookie:
        return cookie[name]
    else:
        return None

def encrypt(key, s):
    b = bytearray(str(s).encode("utf-8"))
    n = len(b)
    c = bytearray(n*2)
    j = 0
    for i in range(0, n):
        b1 = b[i]
        b2 = b1 ^ key
        c1 = b2 % 16
        c2 = b2 // 16
        c1 = c1 + 65
        c2 = c2 + 65
        c[j] = c1
        c[j+1] = c2
        j = j+2
    return c.decode("utf-8")

def decrypt(key, s):
    c = bytearray(str(s).encode("utf-8"))
    n = len(c)
    if n % 2 != 0 :
        return ""
    n = n // 2
    b = bytearray(n)
    j = 0
    for i in range(0, n):
        c1 = c[j]
        c2 = c[j+1]
        j = j+2
        c1 = c1 - 65
        c2 = c2 - 65
        b2 = c2*16 + c1
        b1 = b2^ key
        b[i]= b1
    try:
        return b.decode("utf-8")
    except:
        return "failed"

def encode(obj):
    obj = obj.replace("<", "&lt;")
    return obj.replace(">", "&lt;")


def gen_file_id(file_hash,file_size):
    assert file_size>0
    return str(file_hash)+"_"+str(file_size)

def gen_file_hash(file_id):
    return file_id.split("_")

def add_download_info_to_resource_list(resource_list):
    for resource in resource_list:
        assert 'file_id' in resource
        resource["online_owners_num"] = int(DownloadMedium.get_online_owners_num_of_res(resource['file_id']))
        resource["online_owners_num"] = min(resource["total_owners_num"], resource["online_owners_num"])


def cipher_resource_list(resource_list, version = "1.9"):
    #a comment: {"who": user_name, "uid": uid, "content": comment, "ctime": long(time())})
    #all comments: ret[file_hash]['comments'] = cls._all_resources[k]['comments']
    #comments is a list
    for resource in resource_list:
        if version < "2.0":
            for comment in resource['comments']:
                comment['content'] = Cipher.encrypt(comment['content'])
        resource['tags'] = Cipher.encrypt(resource['tags'])
        resource['file_name'] = Cipher.encrypt(resource['file_name'])

def cacheUserInfo(user):
    uid_tmp = str(user["uid"])
    gender = user["gender"]
    if gender:
        if gender == u"男":
            gender = 1
        else:
            gender = 0
    info = json.dumps({"nick_name": user["nick_name"], "icon": user["icon"], 
                    "user": user["user"], "gender": gender, "school": user["school"]})
    RedisHandler.f_hset(FRIENDINFO, uid_tmp, json.dumps(user["friends"]))
    RedisHandler.f_hset(USERINFO, uid_tmp, info)

@gen.coroutine
def getUserInfoById(uid):
    uid = long(uid)
    uid_tmp = str(uid)
    info = RedisHandler.f_hget(USERINFO, uid_tmp)
    if info:
        raise gen.Return(json.loads(info))
    else:
        user = yield motorclient.fbt_realtime.users.find_one({"uid": uid}, {"_id": 0})
        if user:
            cacheUserInfo(user)
            gender = user["gender"]
            if gender:
                if gender == u"男":
                    gender = 1
                else:
                    gender = 0
            info = {"nick_name": user["nick_name"], "icon": user["icon"], 
                            "user": user["user"], "gender": gender, "school": user["school"]}
            raise gen.Return(info)
        else:
            raise gen.Return(None)

@gen.coroutine
def getFriendsById(uid):
    uid = long(uid)
    uid_tmp = str(uid)
    info = RedisHandler.f_hget(FRIENDINFO, uid_tmp)
    if info:
        raise gen.Return(json.loads(info))
    else:
        user = yield motorclient.fbt_realtime.users.find_one({"uid": uid}, {"_id": 0, "friends": 1})
        if user:
            RedisHandler.f_hset(FRIENDINFO, uid_tmp, json.dumps(user["friends"]))
            raise gen.Return(user["friends"])
        else:
            raise gen.Return(None)

@gen.coroutine
def updateFriendsById(uid):
    uid = long(uid)
    uid_tmp = str(uid)
    user = yield motorclient.fbt_realtime.users.find_one({"uid": uid}, {"_id": 0, "friends": 1})
    if user:
        RedisHandler.f_hset(FRIENDINFO, uid_tmp, json.dumps(user["friends"]))

@gen.coroutine
def getIconByUid(uid):
    info = yield getUserInfoById(uid)
    if info:
        raise gen.Return(info["icon"])
    else:
        raise gen.Return(None)

@gen.coroutine
def getUserByNick(nick_name):
    user = RedisHandler.f_hget(NICKINFO, nick_name)
    if user:
        raise gen.Return(user)
    else:
        user = yield motorclient.fbt_realtime.users.find_one({"nick_name": nick_name}, {"_id": 0, "user": 1})
        if user:
            RedisHandler.f_hset(NICKINFO, nick_name, user["user"])
            raise gen.Return(user["user"])
        else:
            raise gen.Return(None)

@gen.coroutine
def getGenderAndSchoolByUid(uid):
    info = yield getUserInfoById(uid)
    if info:
        raise gen.Return((info["gender"], info["school"]))
    else:
        raise gen.Return((None, None))

def generate_pkey():
    return uuid.uuid1().get_hex()

def generate_ukey(uid, ctime):
    return str(uid) + "_" +str(ctime)

def get_prefix(rid):
    return rid.split("_")[0]

@gen.coroutine
def get_next_sequence(db, key, ext):
    if key == "reward":
        ret_type = yield db.reward_counters.find_and_modify(query={ "_id": key },
            update={ "$inc": { "seq"+str(ext): 1 } },upsert=True)
        ret_all = yield db.reward_counters.find_and_modify(query={ "_id": key },
            update={ "$inc": { "seq": 1 } },upsert=True)
        if ret_type is None and ret_all is None:
            raise gen.Return((0, 0))
        elif ret_type is None:
            raise gen.Return((0, ret_all["seq"]))
        else:
            raise gen.Return((ret_type["seq"+str(ext)], ret_all["seq"]))
    else:
        key += str(ext).split("_")[0][-1]
        ret = yield db.reward_counters.find_and_modify(query={ "_id": key },
            update={ "$inc": { "seq"+str(ext): 1 } },upsert=True)
        if not ret:
            raise gen.Return(0)
        else:
            raise gen.Return(ret["seq"+str(ext)])

@gen.coroutine
def set_next_sequence(db, key, val):
    yield db.reward_counters.find_and_modify(query={ "_id": key },
        update={ "$set": { "seq": val } },upsert=True)


def fetch_token_in_cache(uid):
    return RedisHandler.f_get(str(uid), RedisHandler.type_token)

def getPages(size):
    return (size + RES_CNT_IN_A_PAGE - 1) / RES_CNT_IN_A_PAGE


def is_validate_email(email):
    if len(email) > 7:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) is not None:
            return True
    return False

def seconds_of_today_at_wee_hours():
    now = datetime.now()
    return long(time()) - now.hour * 3600 - now.minute * 60 - now.second

def lower_bound(arr, item):
    '''
    binary search for lower bound.
    '''
    assert arr
    if item <= arr[0]:
        return 0
    if item > arr[-1]:
        return -1
    low, high = 0, len(arr)-1
    while low <= high:
        mid = (low + high) >> 1
        if arr[mid] > item:
            high = mid - 1
        elif arr[mid] < item:
            low = mid + 1
        else:
            return mid
    return low


if __name__ == "__main__":
    assert lower_bound([1], 0) == 0
    assert lower_bound([1], 2) == -1
    assert lower_bound([1, 3, 7], 2) == 1
    assert lower_bound([1, 3, 7], 4) == 2
    assert lower_bound([1, 3, 7], 3) == 1
    assert lower_bound([1, 3, 7], 1) == 0
    assert lower_bound([1, 3, 7], 7) == 2
    print "lower_bound passed test."
