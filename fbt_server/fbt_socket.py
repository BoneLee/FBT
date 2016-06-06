# -*- coding: utf-8 -*-
from time import time
import simplejson as json
import os
import socket

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
from tornado import gen
from tornado.options import define, options
import tornado.websocket

from redis_handler import RedisHandler
from resource_manager import ResourceStoreManager
from user_ip_cache import UserIPCache
from http_server_info_cache import HttpServerInfoCache
import msg_handle
import util
from fb_manager import FBCoinManager
from users_manager import  UserManager
import motorclient
from constant import *
from user_log import LogForUser
#from redis_handler import RedisHandler

#import threading
import logging
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2
# from pymongo import ReadPreference


define("port", default=8004, help="run on the given port", type=int)
#db = motor.MotorClient().fbt#motor.MotorClient().open_sync().fbt
#db_client = motor.ReplicaSetClient(hosts_or_uri="127.0.0.1:27017",io_loop=self.io_loop, replicaSet='fbt_repl')
#db_client = motor.MotorReplicaSetClient(hosts_or_uri="127.0.0.1:27017",replicaSet='fbt_repl')
#db_client.read_preference = ReadPreference.SECONDARY_ONLY
#db = db_client.fbt
#log_db = motor.MotorClient().fbt_log
#log_db = db_client.fbt_log
#login_token = {}
#login_user = {}
#upload_uid = {}
db = None
log_db = None
extend = "extend"
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        fbt_user = ""
        if self.get_argument("from", "chrome") == "client":
            fbt_user = util.g_cookie(self, "fbt_user")
        else:
            fbt_user = self.get_cookie("fbt_user")
        if fbt_user:
            user_json = util.decrypt(15, fbt_user)
            #print user_json
            if not user_json: return None
            return user_json
        else:
            return None

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/inform', InformHandler),
            (r'/socket', SocketHandler),
            (r"/redirect_socket", RedirectSocketHandler),
            
            #for debug
            (r"/debug/users", UsersListHandler),
            (r"/debug/loginuser", LoginUserHandler),
            (r"/debug/logintoken", LoginTokenHandler),
            (r"/debug/loginS", LoginSocketHandler),
            (r"/debug/http_server_info", ViewHttpServerInfoHandler),
        ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #xsrf_cookies=True,
            #cookie_secret="p9/fgwB0R5+qV/rs6ICKe0pOdOhkckpEv2Zc/E1ZeYk=",
            login_url="/login",
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class LoginUserHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key", "") == "fbt":
            login_user = RedisHandler.f_hgetall(LOGIN_U)
            if not login_user:
                return
            self.render("user.html", title="login user", items=login_user, online_cnt=len(login_user))
        else:
            raise tornado.web.HTTPError(404)


class LoginTokenHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key", "") == "fbt":
            login_token = RedisHandler.f_hgetall(LOGIN_T)
            if not login_token:
                return
            self.render("user.html", title="login token", items=login_token, online_cnt=len(login_token))
        else:
            raise tornado.web.HTTPError(404)
        

class LoginSocketHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key", "") == "fbt":
            self.render("user.html", title="login socket", items=SocketHandler.client_uid_user, online_cnt=len(SocketHandler.client_user_heart))
        else:
            raise tornado.web.HTTPError(404)

class UsersListHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key", "") == "fbt":
            user_ip_list = UserIPCache.get_user_ip_list()
            if not user_ip_list:
                return
            self.render("user_ip_list.html", title="user ip list", items=user_ip_list, online_cnt=len(user_ip_list))
        else:
            raise tornado.web.HTTPError(404)

class ViewHttpServerInfoHandler(tornado.web.RequestHandler):
    '''
    this will see how many user are online.
    '''

    def get(self):
        if self.get_argument("key", "") == "fbt":
            http_server_info = HttpServerInfoCache.get_server_info()
            if not http_server_info:
                return
            self.render("http_server_info.html", server_info=http_server_info)
        else:
            raise tornado.web.HTTPError(404)


class InformHandler(BaseHandler):
    def get(self):
        if self.get_argument("user","") and self.get_argument("pwd",""):
            user = self.get_argument("user","")
            pwd = self.get_argument("pwd","")
            to = self.get_argument("to","")
            if user == "fbt2user" and pwd == "fbt2user" and os.path.isfile("inform.json"):
                inform = open("inform.json")
                inform_content = json.load(inform)
                inform.close()
                #type 0 inform all the online user, type 1 inform when login
                #type 2 inform one
                #msg 0 show toast, 1 add to msg center
                #sticky 0 show toast, sticky 1 show sticky toast
                if inform_content["type"] == 0:
                    inform_content["type"] = 7
                    SocketHandler.send_inform(json.dumps(inform_content))
                elif inform_content["type"] == 2 and to:
                    inform_content["type"] = 7
                    SocketHandler.send_to_one(to,json.dumps(inform_content))
                self.write(json.dumps({"type":1}))
                self.finish()
            else:
                self.write(json.dumps({"type":0}))
                self.finish()
        else:
            self.write(json.dumps({"type":0}))
            self.finish()
        
class SocketHandler(tornado.websocket.WebSocketHandler):
    client_socket = {}
    client_user = {}
    client_uid_user = {}
    client_user_uid = {}
    client_user_heart = {}
    login_user = {}
    user_online_at = dict()
    _ioloop = None
    sub_user_login = None
    sub_user_inform = None
    sub_user_coin = None
    
    @staticmethod
    def init():
        SocketHandler.sub_user_login = util.RedisSub(CHANNEL_LOGIN, SocketHandler.user_login)
        SocketHandler.sub_user_inform = util.RedisSub(CHANNEL_INFORM, SocketHandler.user_inform)
        SocketHandler.sub_user_coin = util.RedisSub(CHANNEL_COIN_VARY, SocketHandler.user_coin)

    @staticmethod
    def user_login(message):
        try:
            message = json.loads(message)
            l_user = message["user"]
            if l_user in SocketHandler.login_user:
                #SocketHandler.login_user[l_user] = 0
                sock = SocketHandler.client_user.get(l_user)
                msg = json.dumps({"type":5})
                if sock:
                    yield handle_close(l_user,sock,False,True)
                    try:
                        sock.write_message(msg)
                    except Exception, e:
                        pass  
                    try:
                        sock.close()
                    except Exception, e:
                        pass
            SocketHandler.login_user[l_user] = 1
        except Exception, e:
            pass
    #{"uid1": coin-vary-value1,"uid2": coin-vary-value2,"uid3": coin-vary-value3....}
    @staticmethod
    def user_coin(message):
        try:
            message = json.loads(message)
            for (k,v) in message.iteritems():
                SocketHandler.update_fb(k,v,1)
        except Exception, e:
            pass
    #type 0 single , 1 all except sender socket, 2 all except sender user, 3 all
    #uid inform user(type=0) send user(type=1)
    #msg inform content(you should give me a str)
    @staticmethod
    def user_inform(message):
        try:
            message = json.loads(message)
            tp = int(message["type"])
            uid = str(message["uid"])
            msg = message["msg"]
            user = message["user"]
            if not user:
                user = SocketHandler.client_uid_user.get(uid)
            if not user and tp != 3:
                return
            if tp == 0: 
                if user not in SocketHandler.client_user:
                    return             
                SocketHandler.send_to_one(user, msg)
            elif tp == 1:
                SocketHandler.send_to_all(SocketHandler.client_user[user], msg)
            elif tp == 2:
                SocketHandler.send_to_all_r(user, msg)
            elif tp == 3:
                myId = getId()
                if uid != myId:
                    SocketHandler.send_to_all_s(msg)
        except Exception, e:
            pass


    @classmethod
    def notify_open_file_server(cls, user_ids, for_who, file_hash):
        assert len(user_ids)>0
        assert file_hash>0
        assert for_who>=0
        OPEN_UDP_SERVER=1
        for uid in user_ids:
            uid = str(uid)
            client_uid_user = SocketHandler.client_uid_user
            if uid in client_uid_user:
                try:
                    user = client_uid_user[uid]
                    msg = json.dumps({"type":0,"message_type": OPEN_UDP_SERVER, "file_hash": file_hash, "what": "open udp server","for": for_who})
                    SocketHandler.send_to_one(user, msg)
                    # else:
                    #     t = util.RedisHandle.f_hget(CLIENT_USER_TORNADO, user)
                    #     if t:
                    #         util.HttpClient.get(MSG_URL+MSG_PORT[int(t)]+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user)
                except:
                    logging.info("Warning: writing open udp server message failed. the user has left."+str(uid))
    @staticmethod
    def send_to_all(s, message):
    #this is for the system information
        # for i in range(len(MSG_PORT)):
        #     if i == 0:
        #         continue
        #     util.HttpClient.get(MSG_URL+MSG_PORT[i]+MSG_URL_AUTH+str(MSG_SEND_ALL)+"&msg="+message)
        for (k,v) in SocketHandler.client_user.iteritems():
            if v == s:
                continue
            try:
                v.write_message(message)
            except Exception, e:
                print e
        send = json.dumps({"type": 3, "msg": message, "uid": getId(), "user": ""})        
        util.RedisPub.publish(CHANNEL_INFORM, send)

    @staticmethod
    def send_to_all_r(user, message):
    #this is for the system information
        # for i in range(len(MSG_PORT)):
        #     if i == 0:
        #         continue
        #     util.HttpClient.get(MSG_URL+MSG_PORT[i]+MSG_URL_AUTH+str(MSG_SEND_ALL)+"&msg="+message)
        for (k,v) in SocketHandler.client_user.iteritems():
            if k == user:
                continue
            try:
                v.write_message(message)
            except Exception, e:
                print e
        send = json.dumps({"type": 3, "msg": message, "uid": getId(), "user": ""})        
        util.RedisPub.publish(CHANNEL_INFORM, send)

    @staticmethod
    def send_inform(message):
        send = json.dumps({"type": 3, "msg": message, "uid": getId(), "user": ""})        
        util.RedisPub.publish(CHANNEL_INFORM, send)
        SocketHandler.send_to_all_s(message)

    @staticmethod
    def send_to_all_s(message):
    #this is for the system information
        # for i in range(len(MSG_PORT)):
        #     if i == 0:
        #         continue
        #     util.HttpClient.get(MSG_URL+MSG_PORT[i]+MSG_URL_AUTH+str(MSG_SEND_ALL)+"&msg="+message)
        for (k,v) in SocketHandler.client_user.iteritems():
            try:
                v.write_message(message)
            except Exception, e:
                print e           

    @staticmethod
    def update_fb(uid, fb, add=0):
        tell = {"add":add,"type":4, "coin": fb}
        msg = json.dumps(tell)
        uid = str(uid)
        if uid in SocketHandler.client_uid_user:
            user = SocketHandler.client_uid_user[uid]
            SocketHandler.send_to_one(user, msg)                                 
            # else:
            #     t = util.RedisHandle.f_hget(CLIENT_USER_TORNADO, user)
            #     if t:
            #         util.HttpClient.get(MSG_URL+MSG_PORT[int(t)]+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user) 

    @staticmethod
    def send_to_one(user, msg):
        #print msg
        try:
            if user in SocketHandler.client_user:                  
                SocketHandler.client_user[user].write_message(msg)
            else:
                send = json.dumps({"type": 0, "msg": msg, "uid": 0, "user": user})        
                util.RedisPub.publish(CHANNEL_INFORM, send)
            # else:
            #     t = util.RedisHandle.f_hget(CLIENT_USER_TORNADO, user)
            #     if t:
            #         util.HttpClient.get(MSG_URL+MSG_PORT[int(t)]+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user)
        except Exception, e:
            print e

    @staticmethod
    def check_on_line():
        if not SocketHandler._ioloop:
            return
        cur_t = long(time())
        for (user, t) in SocketHandler.client_user_heart.iteritems():
            t = long(t)
            if cur_t - t > 3600 and user in SocketHandler.client_user:
                try:
                    SocketHandler.client_user[user].close()
                except Exception, e:
                    print e
                    yield handle_close(user,SocketHandler.client_user[user],True,True)
        SocketHandler._ioloop.add_timeout(long(time()) + 3600, lambda: SocketHandler.check_on_line())

    @staticmethod
    def set_io_loop(ioloop):
        SocketHandler._ioloop = ioloop

    @staticmethod
    def send_to_friends(users, msg):
        for item in users:
            if item in SocketHandler.client_user:
                try:
                    SocketHandler.client_user[item].write_message(msg)
                except Exception, e:
                    print e
            # else:
            #     t = util.RedisHandle.f_hget(CLIENT_USER_TORNADO, item)
            #     if t:
            #         util.HttpClient.get(MSG_URL+MSG_PORT[int(t)]+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+item)            

    @gen.coroutine
    def open(self):
        util.log("SocketHandler Welcome ")
        if os.path.isfile("inform.json"):
            inform = open("inform.json")
            inform_content = json.load(inform)
            inform.close()
            #type 0 inform all the online user, type 1 inform when login
            #msg 0 show toast, 1 add to msg center
            #sticky 0 show toast, sticky 1 show sticky toast
            if inform_content["type"] == 1:
                inform_content["type"] = 7;
                self.write_message(json.dumps(inform_content))
        #self.write_message(json.dumps({"type":0, "msg": "hello"}))
        #SocketHandler.send_to_all(str(id(self)) + ' has joined')
        #SocketHandler.clients.add(self)

    #type 0 for sys, 1 for left, 2 for single chat, 3 for group chat, 4 for fb refresh, 5 for multi login
    @gen.coroutine
    def on_message(self, message):
        #global login_user
        #global upload_uid
        json_data = {}
        try:
            json_data = json.loads(message)
        except:
            print "json error"+message
            return
        if "type" in json_data:
            if json_data["type"] == 0:
                #print message
                name = util.decrypt(15, json_data["user"])
                uid_tmp = str(json_data["uid"])
                try:
                    token = str(json_data["token"])
                    if check_token(uid_tmp, token):
                        if json_data["connect"] == 1:
                            #login_user[name] = 1
                            SocketHandler.login_user[name] = 1
                        elif json_data["connect"] == 0:
                            pass
                        else:
                            #print "connect param error"
                            return
                    else:
                        #print "token param error"
                        return
                except ValueError:
                    self.write_message(json.dumps({"type":0, "err": "token error"}))
                    return
                if name in SocketHandler.client_user:
                    sock = SocketHandler.client_user.get(name)
                    msg = json.dumps({"type":5})
                    if sock and sock != self:
                        yield handle_close(name,sock,True,True)
                        try:
                            sock.write_message(msg)
                        except Exception, e:
                            pass  
                        try:
                            sock.close()
                        except Exception, e:
                            pass
                SocketHandler.client_user[name] = self
                SocketHandler.client_socket[self] = name
                SocketHandler.client_user_heart[name] = long(time())
                # util.RedisHandle.f_hset(CLIENT_SOCKET, id(self), name)
                # util.RedisHandle.f_hset(CLIENT_USER, name, id(self))
                # util.RedisHandle.f_hset(CLIENT_USER_HEART, name, long(time()))
                user = json_data["uid"]
                try:
                    user=long(user)
                    util.RedisPub.publish(CHANNEL_ON_OFF, json.dumps({"type":0, "uid": user, "token": token, "ip":self.request.remote_ip}))
                    SocketHandler.client_uid_user[str(user)] = name
                    SocketHandler.client_user_uid[name] = user
                    SocketHandler.user_online_at[str(user)]=long(time())
                    #util.RedisHandle.f_hset(CLIENT_USER_TORNADO, user, 0)
                    # util.RedisHandle.f_hset(CLIENT_UID_USER, str(user), name)
                    # util.RedisHandle.f_hset(CLIENT_USER_UID, name, str(user))
                    # util.RedisHandle.f_hset(USER_ONLINE_AT, str(user), str(long(time())))
                    self.write_message(json.dumps({"type":0, "err": "", "ip": self.request.remote_ip}))
                except ValueError:
                    self.write_message(json.dumps({"type":0, "err": "uid error"}))
                    return
                #use send_to_all to test
                #SocketHandler.send_to_all(self, json.dumps(tell))
                cursor = yield db.users.find_one({"user":name},{"_id":0,"friends":1,"nick_name":1,"gender":1,"school":1})
                tell = {"type":0, "msg":cursor["nick_name"]+u" 上线了", "sys": user}
                SocketHandler.send_to_friends(getOnlineFriend(cursor["friends"]), json.dumps(tell))
                if json_data["connect"] == 1:
                    self.write_message(json.dumps({"type":8,"uid":getOnlineFriendUid(cursor["friends"])}))
                if os.path.isfile("inform.json"):
                    inform = open("inform.json")
                    inform_content = json.load(inform)
                    inform.close()
                    #type 0 inform all the online user, type 1 inform when login
                    #type 2 inform one
                    #msg 0 show toast, 1 add to msg center
                    #sticky 0 show toast, sticky 1 show sticky toast
                    if inform_content["type"] == 2 and "to" in inform_content:
                        to = inform_content["to"].split(",")
                        if name in to:
                            inform_content["type"] = 7
                            self.write_message(json.dumps(inform_content))
                # gender = -1
                # if cursor["gender"]:
                #     if cursor["gender"] == u"男":
                #         gender = 1
                #     else:
                #         gender = 0
                # RedisHandler.f_hset(GENDERKEY, uid_tmp, gender)
                # RedisHandler.f_hset(SCHOOLKEY, uid_tmp, cursor["school"])
            elif json_data["type"] == 2:
                #print message
                #{"type":2,"recv":who,"sender":who,"msg":content,"time":time}
                try:
                    token = str(json_data["token"])
                    uid_tmp = str(json_data["sender"])
                    if check_token(uid_tmp, token):
                        u = SocketHandler.client_uid_user[str(json_data["recv"])]
                        #u = util.RedisHandle.f_hget(CLIENT_UID_USER, str(json_data["recv"]))
                        json_data['msg'] = escape(json_data['msg'])
                        SocketHandler.send_to_one(u, json.dumps(json_data))
                    else:
                        #print "token param error"
                        return
                except ValueError:
                    self.write_message(json.dumps({"type":0, "err": "uid error"}))
                    return
            elif json_data["type"] == 3:
                #print message
                #{"type":3,"recv":"","sender":who,"msg":content,"time":time}
                try:
                    token = str(json_data["token"])
                    uid_tmp = str(json_data["uid"])
                    if check_token(uid_tmp, token):
                        json_data["sender"] = util.decrypt(15, json_data["sender"])
                        #cursor = yield db.users.find_one({"user":SocketHandler.client_socket[self]},{"_id":0})
                        #SocketHandler.send_to_friends(getOnlineFriend(cursor["friends"]), json.dumps(json_data))
                        json_data['msg'] = escape(json_data['msg'])
                        gender, school = yield util.getGenderAndSchoolByUid(uid_tmp)
                        if gender or gender == 0:
                            json_data['gender'] = gender
                        if school:
                            json_data['school'] = school
                        SocketHandler.send_to_all(self, json.dumps(json_data))
                    else:
                        #print "token param error"
                        return
                except ValueError:
                    self.write_message(json.dumps({"type":0, "err": "uid error"}))
                    return
            elif json_data["type"] == 9:
                if self in SocketHandler.client_socket:
                    name = SocketHandler.client_socket[self]
                    SocketHandler.client_user_heart[name] = long(time())
                # if util.RedisHandle.f_hexists(CLIENT_SOCKET, self):
                #     name = util.RedisHandle.f_hget(CLIENT_SOCKET, self)
                #     util.RedisHandle.f_hset(CLIENT_USER_HEART, name, long(time()))
                self.write_message(json.dumps({"type":13}))
            # elif json_data["type"] == 10:
            #     #print message
            #     try:
            #         token = str(json_data["token"])
            #         uid_tmp = str(json_data["uid"])
            #         if util.RedisHandle.f_hget(LOGIN_T, uid_tmp) == token:
            #             uid_list = json_data["uid_list"].split(",")
            #             for item in uid_list:
            #                 item = str(item)
            #                 if(item in upload_uid):
            #                     upload_uid[item].append(long(uid_tmp))
            #                 else:
            #                     tmp = []
            #                     tmp.append(long(uid_tmp))
            #                     upload_uid[item] = tmp
            #         else:
            #             print "token param error"
            #             return
            #     except ValueError:
            #         self.write_message(json.dumps({"type":0, "err": "uid error"}))
            #         return
            elif json_data["type"] == 11:
                #print message
                #not use
                return
                # try:
                #     token = str(json_data["token"])
                #     uid_tmp = str(json_data["uid"])
                #     if check_token(uid_tmp, token):
                #         data = json.loads(json_data["data"])
                #         h = data.get("hash")
                #         main_type = data.get("mainType")
                #         sub_type = data.get("subType")
                #         res_grade = data.get("grade")
                #         file_size = data.get("fileSize")
                #         uid = uid_tmp
                #         is_public = data.get("isPublic","1")
                #         tag = Cipher.decrypt(data.get("label","")).strip().split(',')
                #         fileName = Cipher.decrypt(data.get("name","")).strip()
                #         desc = Cipher.decrypt(data.get("desc","")).strip()
                #         nick = data.get("nick_name","")
                #         try:
                #             uid = long(uid)
                #             main_type = int(main_type)
                #             sub_type = int(sub_type)
                #             res_grade = float(res_grade)
                #             if res_grade < 0:
                #                 res_grade = 5
                #             file_size = int(file_size)
                #             h = long(h)
                #             is_public = int(is_public)
                #             assert h > 0
                #             assert len(fileName) > 0
                #             assert uid > 0
                #             assert main_type >= 0
                #             assert sub_type >= 0
                #             assert file_size > 0
                #             assert len(nick) > 0
                #             assert len(desc) > 0
                #             assert res_grade >= 0 and res_grade <= 10
                #             assert is_public == 0 or is_public == 1
                #             assert len(tag) > 0
                #         except:
                #             self.write_message(json.dumps({"type":11, "suc": 0, "hash":h}))
                #             return
                #         #print uid
                #         if uid:
                #             #print "start upload"
                #             yield  ResourceStoreManager.user_upload_resource(uid, nick,
                #                                                         h,
                #                                                         fileName, file_size,
                #                                                         is_public,
                #                                                         tag,
                #                                                         main_type, sub_type,
                #                                                         res_grade,
                #                                                         desc)
                #             self.write_message(json.dumps({"type":11, "suc": 1, "hash":h}))
                #     else:
                #         print "token param error"
                #         return
                # except ValueError:
                #     self.write_message(json.dumps({"type":0, "err": "uid error"}))
                #     return
        else:
            print "no type in json"
            self.write_message(json.dumps({"type":0, "err": "type error"}))      

    @gen.coroutine
    def on_close(self):
        util.log( "SocketHandler close ")
        if self in SocketHandler.client_socket:
            name = SocketHandler.client_socket[self]
            yield handle_close(name,self,True,False)
        # if util.RedisHandle.f_hexists(CLIENT_SOCKET, self):
        #     name = util.RedisHandle.f_hget(CLIENT_SOCKET, self)
        #     handle_close(name,self,True)
        #SocketHandler.send_to_all(name + ' has left')
@gen.coroutine
def handle_close(name,s,isOut,skipTell):
    #global login_user
    #global upload_uid
    user_to_del = long(SocketHandler.client_user_uid.get(name))
    if not user_to_del:
        return
    user_id = str(user_to_del)
    # if user_id in upload_uid:
    #     for item in upload_uid[user_id]:
    #         item = long(item)
    #         if item in SocketHandler.client_uid_user:
    #             n_user = SocketHandler.client_uid_user[item]
    #             SocketHandler.client_user[n_user].write_message(json.dumps({"type":9,"uid":user_to_del}))
    #     del(upload_uid[user_id])
    cursor = yield db.users.find_one({"user":name},{"friends":1,"_id":0,"nick_name":1})
    util.log("SocketHandler.on_close")
    util.RedisPub.publish(CHANNEL_ON_OFF, json.dumps({"type":1, "uid": user_to_del}))
    if not skipTell:
        tell = {"type":1, "msg":cursor["nick_name"]+u" 下线了", "user": user_to_del}
        #use send_to_all to test
        #SocketHandler.send_to_all(self, json.dumps(tell))
        SocketHandler.send_to_friends(getOnlineFriend(cursor["friends"]), json.dumps(tell))
    yield FBCoinManager.user_online_ok(user_to_del,long(SocketHandler.user_online_at[user_id]),long(time()))
    try:
        SocketHandler.user_online_at.pop(user_id, None)
        SocketHandler.client_socket.pop(s, None)
        SocketHandler.client_user.pop(name, None)
        SocketHandler.client_user_heart.pop(name, None)
        SocketHandler.client_uid_user.pop(user_id, None)
        SocketHandler.client_user_uid.pop(name, None)
        #util.RedisHandle.f_hdel(USER_ONLINE_AT,*[user_id])
        # util.RedisHandle.f_hdel(CLIENT_SOCKET,*[s])
        # util.RedisHandle.f_hdel(CLIENT_USER, *[name])
        # util.RedisHandle.f_hdel(CLIENT_USER_HEART, *[name])
        #util.RedisHandle.f_hdel(CLIENT_USER_UID, *[name])
        #util.RedisHandle.f_hdel(CLIENT_UID_USER, *[user_id])
        #maybe I shouldn't delete the token if we should reconnect
        #util.RedisHandle.f_delete(util.RedisHandle.type_token, *[user_id])
        util.MemCache.delete(user_id, LOGIN_T)
        util.MemCache.delete(None, user_id+extend)
        #util.RedisHandle.f_hdel(CLIENT_USER_TORNADO, *[name])
    except:
        print "del error"
    if isOut and name in SocketHandler.login_user:
        del(SocketHandler.login_user[name])
        #util.RedisHandle.f_hdel(LOGIN_U, *[name])
    util.log("SocketHandler.on_close finish")

def getOnlineFriend(users):
    re = []
    for item in users:
        if item["user"] in SocketHandler.client_user:
            re.append(item["user"])
    return re
def getOnlineFriendUid(users):
    re = []
    for item in users:
        if item["user"] in SocketHandler.client_user:
            re.append(item["uid"])
    return re 
def getUid(s):
    return util.g_cookie(s, "fbt_user_id")

def getNickName(s):
    return util.g_cookie(s, "fbt_nick_name")

def check_token(uid, token):
    if util.MemCache.get(str(uid), LOGIN_T) != token:
        store_t = RedisHandler.f_get(str(uid), RedisHandler.type_token)
        if store_t != token:
            return False
        else:
            util.MemCache.set(str(uid), token, LOGIN_T, 7200)
    return True

class RedirectSocketHandler(BaseHandler):
    def get(self):
        if self.get_argument("auth_user","") == MSG_AUTH and self.get_argument("auth_pwd","") == MSG_AUTH:
            self.handle_redirect()
        else:
            self.write(json.dumps({"type":0}))
            self.finish()
    # def post(self):
    #     if self.get_argument("auth_user","") == MSG_AUTH and self.get_argument("auth_pwd","") == MSG_AUTH:
    #         self.handle_redirect()
    #     else:
    #         self.write(json.dumps({"type":0}))
    #         self.finish()

    # TODO FIXME this function is dangerous. --BoneLee
    def handle_redirect(self):
        msg_type = self.get_argument("msg_type","")
        if msg_type:
            msg_type = int(msg_type)
            if msg_type == MSG_SOCKET_CLOSE:
                user = self.get_argument("user","")
                msg = self.get_argument("msg", "")
                if user in SocketHandler.client_user:
                    sock = SocketHandler.client_user[user]
                    try:
                        if msg:
                            sock.write_message(msg)
                        yield handle_close(user,sock,True,False)
                        sock.close()
                    except Exception, e:
                        print e                    
            elif msg_type == MSG_SEND_ONE:
                user = self.get_argument("user","")
                msg = self.get_argument("msg", "")
                SocketHandler.send_to_one(user, msg)
            elif msg_type == MSG_SEND_ALL:
                msg = self.get_argument("msg", "")
                SocketHandler.send_to_all_s(msg)
            elif msg_type == MSG_SEND_ALL_R:
                user = self.get_argument("user","")
                msg = self.get_argument("msg", "")
                SocketHandler.send_to_all_r(user, msg)
        self.finish()

def getId():
    return str(socket.gethostname())

def main():
    global db
    global log_db
    # if os.path.isfile("login_token.json") and os.path.isfile("login_user.json"):
    #     in_token = open("login_token.json")
    #     login_token = json.load(in_token)
    #     in_token.close()
    #     RedisHandler.f_hmset(LOGIN_T, login_token)
    #     in_user = open("login_user.json")
    #     SocketHandler.login_user = json.load(in_user)
    #     #util.RedisHandle.f_hmset(LOGIN_U, login_user)
    #     in_user.close()
    #     os.rename("login_token.json", "login_token"+str(long(time()))+".json")
    #     os.rename("login_user.json", "login_user"+str(long(time()))+".json")
    access = logging.getLogger("tornado.access")
    access.addHandler(NullHandler())
    access.propagate = False
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    try:
        util.MemCache.load(str(options.port))
        #util.RedisHandle.f_delete(*[CLIENT_UID_USER,CLIENT_USER_UID,USER_ONLINE_AT,USER_IP_LIST,HTTP_SERVER_INFO])
        ioloop=tornado.ioloop.IOLoop.instance()
        #db_client = motor.MotorReplicaSetClient(hosts_or_uri="127.0.0.1:27017",replicaSet='fbt_repl',io_loop=ioloop)
        #db_client.read_preference = ReadPreference.SECONDARY_ONLY
        #db = db_client.fbt
        #log_db = motor.MotorClient().fbt_log
        #log_db = db_client.fbt_log
        db = motorclient.fbt
        log_db = motorclient.fbt_log
        ResourceStoreManager.set_db(db)
        FBCoinManager.set_db(db)
        UserManager.set_db(db)
        msg_handle.set_db(db)
        LogForUser.set_db(log_db)
        #FBCoinManager.set_update_fb_callback(SocketHandler.update_fb)
        #FBRankManager.initialize() #load rank info from file
        #FBRankTimer.set_io_loop(ioloop)
        #FBRankTimer.run() #backup the weekly and monthly rank
        
        SocketHandler.set_io_loop(ioloop)
        SocketHandler.init()
        ioloop.add_timeout(long(time()) + 3600, lambda: SocketHandler.check_on_line())
        ioloop.start()
    except Exception, e:
        print e
        print "OK. I will exit..."
    finally:
        SocketHandler.sub_user_coin.close()
        SocketHandler.sub_user_login.close()
        SocketHandler.sub_user_inform.close()
        # close sub client
        
        RedisHandler.f_save()
        util.MemCache.save(str(options.port))
        #FBRankManager.save_info_to_file() #backup rank info to file
class NullHandler(logging.Handler):
    def __init__(self,level=logging.ERROR):
        logging.Handler.__init__(self,level)
    def emit(self,record):
        pass

if __name__ == "__main__":
    main()
