#-*- coding:utf-8 -*-
import util
import uuid
from datetime import datetime
import time
import redis_handler
import json
import mongoclient

"""
PORT = 7778
msgRedisPassWd = '123-fbt-msg-!@#'
PORT = 7777
msgRedisPassWd = None
"""
#redis_msg_conn = redis.Redis()#redis.Redis(host='127.0.0.1', port=PORT, db =0, password = msgRedisPassWd)
redis_msg_conn = redis_handler.RedisHandler(redis_handler.RedisHandler.type_msg)
pipe = redis_msg_conn.pipeline()

db_msg = mongoclient.fbt
"""
from pymongo import MongoClient
db_msg = MongoClient('localhost', 27017).fbt
"""

def set_db(db):
    global db_msg
    db_msg = db
'''
msg format >>> deprecated
{"user":user_name, "msg_list":[{"isRead":True/False, "sender":user_name, "type":0 for sys/1 for add, "content":msg_content may be ""},...]}

msg in redis
type: 
zset
key-name: 'msg-list':user
member: id
score: time

hashes
key-name: 'msg-box':user
key: id
value: '{"sender":user_name, "type":0 for sys/1 for add, "content":msg_content, "time":}'

TODO: id to be replaced by array index of list for low complexity!!!
             to rm msgs having been read, and to rm isRead!!!

user_shuo format >>> deprecated
user:
shuo_list: [{
    content:
    comment: []
    id:
    time:
    }]
{   
    “user”: “1@qq.com”,
    “shuo_list”: [{
    "content": "whatever",
    "comment": [],
    "id": "123",
    "time": "2014-09-12 15:10"
    }]
}

user_shuo in redis
old
================
type: 
zset
key-name: 'shuo-list':user
member: id
score: time

hashes
key-name: 'shuo-box':user
key: id
value: '{"content": 'blabla', 'comment': [], 'time': }'
===============
new 
hashes
key-name: 'shuo-box'
key: user
value: content

TODO: when we need to compliment comment logic, we need to seprate comment from the hashes
'''

# @gen.coroutine
# def initMsg(user):
#     new_msg = {"user":user, "msg_list":[]}
#     result = yield db_msg.user_msg.insert(new_msg)
#     print "initMsg" + str(result)
'''
check if current user send add req to the user
'''
def isMsgExist(user, sender):
    result = redis_msg_conn.hvals('msg-box:' + user)
    result = map(json.loads, result)
    for item in result:
        if 'sender' in item and sender == item['sender']:
            return True
    
    return False

'''
all handle about user msg
'''
def addMsg(user, content, s, suc, fail):
    uid = content['id']
    pipe.multi()
    pipe.zadd('msg-list:' + user, time.time(), uid)
    pipe.hset('msg-box:' + user, uid, json.dumps(content))
    res = pipe.execute()
    util.log( "addMsg" + user )

    if s:
        if res[-1]:
            result = {"result" : suc}
            util.write(s, 1, "", result)
            s.finish()
        else:
            util.write(s, 0, fail, {})
            s.finish()

def getAllMsg(user):
    msg_ids = redis_msg_conn.zrange('msg-list:' + user, 0, -1)
    result = list()
    if msg_ids:
        result = redis_msg_conn.hmget('msg-box:' + user, msg_ids)
        result = map(json.loads, result)
        for uid, item in zip(msg_ids, result):
            item['isRead'] = 0
            item['id'] = uid

    return {'user': user, 'msg_list': result}
    #util.log(result)
    #util.log( "getAllMsg" + user)

def delMsg(user):
    pipe.multi()
    pipe.delete('msg-list:' + user)
    pipe.delete('msg-box:' + user)
    pipe.execute()
    util.log("delMsg")

def ReadMsg(user, i):
    pipe.multi()
    pipe.zrem('msg-list:' + user, i)
    pipe.hdel('msg-box:' + user, i)
    pipe.execute()

    util.log("ReadMsg")

def ReadAllMsg(user):
    pipe.multi()
    pipe.delete('msg-list:' + user)
    pipe.delete('msg-box:' + user)
    pipe.execute()

'''
all handle about user's shuoshuo and others' comment
'''
def addShuo(user, content):
    redis_msg_conn.hset('shuo-box', user, content)

def getShuo(user):
    return redis_msg_conn.hget('shuo-box', user) 
'''
def addShuo(user, content, s, suc, fail):
    re = {}
    re["id"] = uid = str(uuid.uuid1().int)
    re["content"] = content
    re["time"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    re["comment"] = []

    pipe.multi()
    pipe.zadd('shuo-list:' + user, time.time(), uid)
    pipe.hset('shuo-box:' + user, uid, json.dumps(re))
    res = pipe.execute()
    util.log( "addShuo" + user )

    if s:
        if res[-1]:
            result = {"result" : suc}
            util.write(s, 1, "", result)
            s.finish()
        else:
            util.write(s, 0, fail, {})
            s.finish()
'''
'''
def delShuo(user, i, s, suc, fail):
    pipe.multi()
    pipe.zrem('shuo-list:' + user, i)
    pipe.hdel('shuo-box:' + user, i)
    result = pipe.execute()

    util.log( "delShuo")

    if s:
        if result[-1]:
            result = {"result" : suc}
            util.write(s, 1, "", result)
            s.finish()
        else:
            util.write(s, 0, fail, {})
            s.finish()

def getAllShuo(user):
    msg_ids = redis_msg_conn.zrange('shuo-list:' + user, 0, -1)
    result = list()
    if msg_ids:
        result = redis_msg_conn.hmget('shuo-box:' + user, msg_ids)
        result = map(json.loads, result)
        for uid, item in zip(msg_ids, result):
            item['id'] = uid

    return {'user': user, 'shuo_list': result}
'''
# def getRecentShuo(user):
#     re = ""
#     result = yield db_msg.user_shuo.find_one({'user': user})
#     if result:
#         tmp = result["msg_list"]
#         re = tmp[len(tmp)-1]
#     return re

def main():
    """
    init by reading all msg and shuo in mongo into redis
    """
    for record in db_msg.user_msg.find({'msg_list.0': {'$exists': True}}, {"_id": 0}):
        user = record['user']
        msg_list = record['msg_list']
        msg_list = filter(lambda x: 0 == x['isRead'], msg_list)
        if msg_list:
            map(lambda x: x.pop('isRead'), msg_list)
            uid_list = list()
            pipe.multi()
            for msg in msg_list:
                uid = msg['id']
                uid_list.append(uid)
                msg_time  = msg['time']
                pipe.zadd('msg-list:' + user, time.mktime(time.strptime(msg_time, '%Y-%m-%d %H:%M')), uid)

            pipe.hmset('msg-box:' + user, dict(zip(uid_list, map(json.dumps, msg_list))))
            res = pipe.execute()
            print 'msg', user

    for record in db_msg.user_shuo.find({'shuo_list.0': {'$exists': True}}, {"_id": 0}):
        user = record['user']
        shuo_list = record['shuo_list']
        pipe.multi()
        uid_list = list()
        for shuo in shuo_list:
            uid = shuo['id']
            uid_list.append(uid)
            shuo_time  = shuo['time']
            pipe.zadd('shuo-list:' + user, time.mktime(time.strptime(shuo_time, '%Y-%m-%d %H:%M')), uid)

        pipe.hmset('shuo-box:' + user, dict(zip(uid_list, map(json.dumps, shuo_list))))
        res = pipe.execute()
        print 'shuo', user

if __name__ == "__main__":
    main()