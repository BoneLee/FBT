# -*- coding: utf-8 -*-
from datetime import datetime
from time import time
import uuid
import simplejson as json
import random
import os
import logging
import math

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
from tornado import gen
from tornado.options import define, options
import tornado.websocket

from redis_handler import RedisHandler
from util import gen_file_id, add_download_info_to_resource_list, cipher_resource_list
from resource_manager import ResourceStoreManager
import ip_address as IP
from user_ip_cache import UserIPCache
from http_server_info_cache import HttpServerInfoCache
from download_medium import DownloadMedium
from resource_info import ResourceInfo
import msg_handle
import util
from cipher import WaveCipher as Cipher
from fb_manager import FBCoinManager
from  users_manager import UserManager
from online_resources import OnlineResources
from constant import *
from user_log import LogForUser
import find_password
from rpctcpclient import TCPClient, RPCClient
from offer_reward import Reward
from comment import CommentManager
from feed import FeedManager
import motorclient

from request_handler import SendResetEmailHandler, ResetPwdHandler
from fileNameSearcher import FileNameSearcher


try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2

# from os.path import expanduser, join
#import tcelery, tasks
#tcelery.setup_nonblocking_producer()

#HOME = expanduser("~")
define("port", default=8001, help="run on the given port", type=int)
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
def tokenCheck(fn):
    def _deco(self, *args, **kwargs):
        if self.get_argument("token", ""):
            try:
                token = str(self.get_argument("token"))
                if util.MemCache.get(str(getUid(self)), LOGIN_T) != token:
                    # store_t = RedisHandler.f_get(str(getUid(self)), RedisHandler.type_token)
                    store_t = util.fetch_token_in_cache(getUid(self))
                    if store_t != token:
                        util.errorHandle(self, 0)
                        self.finish()
                        return
                    else:
                        util.MemCache.set(str(getUid(self)), token, LOGIN_T, -1)
            except ValueError:
                util.errorHandle(self, 0)
                self.finish()
                return
        else:
            util.errorHandle(self, 0)
            self.finish()
            return
        fn(self, *args, **kwargs)

    return _deco

db_realtime = None
db = None
log_db = None


def server_info(message):
    try:
        message = json.loads(message)
        if message["type"] == 1:
            if "port" in message:
                HttpServerInfoCache.update_ipv6_address(long(message["uid"]), message["ip"], message["port"])
            else:
                HttpServerInfoCache.update_ipv6_address(long(message["uid"]), message["ip"], 8886)
        elif message["type"] == 0:
            if "port" in message:
                HttpServerInfoCache.update_ipv4_address(long(message["uid"]), message["ip"], message["port"])
            else:
                HttpServerInfoCache.update_ipv4_address(long(message["uid"]), message["ip"], 8884)
    except Exception, e:
        pass


def user_off(message):
    try:
        message = json.loads(message)
        if message["type"] == 1:
            UserIPCache.delete_my_ip(long(message["uid"]))
            HttpServerInfoCache.delete_user(long(message["uid"]))
            util.MemCache.delete(str(message["uid"]), LOGIN_T)
        elif message["type"] == 0:
            UserIPCache.update_my_ip(long(message["uid"]), message["ip"])  #!!! record the user IP
            util.MemCache.set(str(message["uid"]), message["token"], LOGIN_T, -1)
    except Exception, e:
        pass


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
            (r"/sns_share", SnsShareHandler),
            (r"/", MainHandler),
            (r"/index", MainHandler),
            (r"/registration", RegistrationHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r'/mySpace', MySpaceHandler),
            (r'/myInfo', MyInfoHandler),
            (r'/myFriend', MyFriendHandler),
            (r'/myShuo', MyShuoHandler),
            (r'/token', TokenHandler),
            (r'/res', ResourceHandler),
            (r'/res/delete', ResourceDelHandler),
            (r'/res/upload/file', ResourceUploadHandler),
            (r'/res/upload/dir', ResourceDirUploadHandler),
            (r'/comment', CommentHandler),
            (r'/feed', FeedHandler),
            (r'/getDir', ViewDirHandler),
            (r"/getFileName", GetFileNameHandler),
            (r"/get_file_info", GetFileInfoHandler),
            (r"/get_summary", GetSummaryHandler),
            (r"/report_http_server_info", HttpServerInfoHandler),
            (r"/report_tcp_server_info", TcpServerInfoHandler),
            (r"/tip_off_resource", TipOffResourceHandler),
            (r"/download_resource", ResourceDownloadHandler),
            (r"/view_resource_download", ResourceDownloadViewHandler),
            (r"/download_over", ResourceDownloadOverHandler),
            (r"/view_user_resource", UserResourceViewHandler),
            (r"/view_friends_resources", FriendsResourceViewHandler),
            (r"/report", ReportErrorHandler),
            (r"/check_update", CheckUpdateHandler),
            (r"/reset_password", SendResetEmailHandler),
            (r"/do_reset_password", ResetPwdHandler),
            (r"/resource404", Resource404Handler),
            (r"/get_nav_info", NavInfoHandler),  #TODO FIXME dengbo
            (r"/registry_confirm", RegistryConfirmHandler),
            (r"/offer_reward", OfferRewardHandler),
            (r"/append_reward", AppendRewardHandler),
            (r"/my_reward", MyRewardHandler),
            (r"/all_reward", AllRewardHandler),
            (r"/cancel_reward", CancelRewardHandler),
            (r"/send_msg", SendMsgHandler),
            (r"/ad", AdHandler),

            #for debug
            (r"/debug/users", UsersListHandler),
            (r"/debug/logintoken", LoginTokenHandler),
            (r"/debug/clearAll", ClearCacheHandler),
            (r"/debug/clearfb", ClearFbHandler),
            (r"/debug/clearRes", ClearResHandler),
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

class GetFileNameHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("fileIds", ""):
            #fileNames = yield ResourceStoreManager.get_file_names_by_ids(self.get_argument("fileIds"))
            #util.write(self, 1, "", fileNames)
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class SendMsgHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        content = self.get_argument("content")
        to = self.get_argument("to")
        if content and to:
            to_user = yield util.getUserByNick(to)
            if not to_user:
                util.write(self, 0, u"用户不存在", "")
                self.finish()
                return
            content = escape(content)
            msg = {}
            msg["type"] = 0
            msg["id"] = str(uuid.uuid1().int)
            msg["sender"] = "0"
            msg["nick"] = "0"
            msg["content"] = content
            msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
            msg_handle.addMsg(to_user, msg, "", "", "")
            util.write(self, 1, "", "")
            self.finish()

class GetSummaryHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        file_id = self.get_argument("fileId", "")
        if file_id:
            summary = yield ResourceStoreManager.get_summary(file_id)
            if summary:
                util.write(self, 1, "", summary)
            else:
                util.write(self, 0, "", "")
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class GetFileInfoHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        file_id = self.get_argument("fileId", "")
        if file_id:
            one_resource = yield ResourceStoreManager.get_one_resource(file_id)
            if one_resource:
                util.write(self, 1, "", one_resource)
            else:
                util.write(self, 0, u"资源未找到", "")
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class ClearCacheHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
            util.MemCache.clear()
        else:
            raise tornado.web.HTTPError(404)


class ClearFbHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
            util.MemCache.clearFb()
        else:
            raise tornado.web.HTTPError(404)


class ClearResHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
            util.MemCache.clearRes()
        else:
            raise tornado.web.HTTPError(404)


class LoginTokenHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
            login_token = RedisHandler.f_hgetall(LOGIN_T)
            if not login_token:
                return
            self.render("user.html", title="login token", items=login_token, online_cnt=len(login_token))
        else:
            raise tornado.web.HTTPError(404)


class UsersListHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
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
        if self.get_argument("key1", "") == "friendsbt2I" and  self.get_argument("key2", "friendsbt2U") :
            http_server_info = HttpServerInfoCache.get_server_info()
            if not http_server_info:
                return
            self.render("http_server_info.html", server_info=http_server_info)
        else:
            raise tornado.web.HTTPError(404)


class TokenHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        token = str(uuid.uuid1().int)
        util.write(self, 1, "", token)
        self.finish()
        
class AdHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    def get(self):
        if os.path.isfile("ad.json"):
            f_ad = open("ad.json")
            ad_info = json.load(f_ad)
            util.write(self, 1, "", ad_info)
        else:
            util.write(self, 0, "not found", {})
        self.finish()


class RegistryConfirmHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.get_argument("key", "") and self.get_argument("user", ""):
            token = self.get_argument("key")
            token = token.replace('_', '')
            user = self.get_argument("user")
            cursor = yield db_realtime.tmp_users.find_one({"token": token, "user": user})
            if cursor and "token" in cursor:
                refer = cursor["refer"]
                identify = cursor["identify"]
                del cursor["token"]
                del cursor["refer"]
                del cursor["identify"]
                result = yield db_realtime.users.find_one({"user": user}, {"user": 1})
                if not result:
                    yield db_realtime.users.insert(cursor)
                    yield FBCoinManager.register_ok(cursor["uid"])
                    yield db_realtime.tmp_users.remove({"token": token, "user": user})
                #msg_handle.initMsg(self.get_argument("user"))
                self.write(u"您的FBT账号已经通过验证，请到客户端开启您的FBT之旅")
                self.finish()
                if refer and identify:
                    #add coin for the refer name
                    r = yield db.refer.find_one({"refer": refer}, {"identify": 1, "refer": 1})
                    notExist = True
                    if r and r["refer"] and identify in r["identify"]:
                        notExist = False
                    if notExist:
                        yield db.refer.update({"refer": refer}, {"$push": {"identify": identify}}, True)
                        cursor = yield db_realtime.users.find_one({"$or": [{"nick_name": refer}, {"real_name": refer}]},
                                                {"uid": 1, "user": 1})
                        if cursor and "uid" in cursor:
                            yield FBCoinManager.invite_a_user(cursor["uid"])
                            msg = {}
                            msg["type"] = 7
                            msg["content"] = u"您推荐的用户已注册成功，FBT奖励您100F币，请查收"
                            msg["sticky"] = 1
                            SocketHandler.send_to_one(cursor["uid"], json.dumps(msg))
                            msg = {}
                            msg["type"] = 0
                            #msg["isRead"] = 0
                            msg["id"] = str(uuid.uuid1().int)
                            msg["sender"] = "0"
                            msg["nick"] = "0"
                            msg["content"] = u"您推荐的用户已注册成功，FBT奖励您100F币，请查收"
                            msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
                            msg_handle.addMsg(cursor["user"], msg, "", "", "")
                find_password.send_intro_mail(user)
            else:
                cursor = yield db_realtime.users.find_one({"user": user}, {"user":1})
                if cursor and cursor["user"]:
                    self.write(u"您的邮箱已经验证过了，请直接到FBT客户端使用。")
                else:
                    self.write(u"对不起，您的邮箱验证失败，请重试或者换用其他邮箱注册试试。")
                self.finish()
        else:
            self.write(u"参数错误")
            self.finish()

class CheckUpdateHandler(BaseHandler):
    def get(self):
        #use version code , not version
        version = self.get_argument("v", "")
        platform = self.get_argument("platform", "win32")
        arch = self.get_argument("arch", "32")
        t = self.get_argument("type", "6")
        if (not version) or (not platform):
            self.write(json.dumps({"type": 0}))
            self.finish()
            return
        try:
            tmp_t = int(t)
            if tmp_t < 5:
                t = "5"
            elif tmp_t > 6:
                t = "6"
            version = int(version)
            if os.path.isfile("version.json"):
                f_version = open("version.json")
                version_info = json.load(f_version)
                cur_version = version_info["version"]
                path = ""
                name = ""
                if platform == "linux":
                    path = version_info[platform][arch]["path"]
                    name = version_info[platform][arch]["name"]
                elif platform == "win32":
                    path = version_info[platform][t]["path"]
                    name = version_info[platform][t]["name"]
                else:
                    path = version_info[platform]["path"]
                    name = version_info[platform]["name"]
                if int(cur_version) > version and path and name:
                    self.write(json.dumps({"type": 1, "path": path, "name": name}))
                else:
                    self.write(json.dumps({"type": 0}))
            else:
                self.write(json.dumps({"type": 0}))
            self.finish()
        except Exception, e:
            logging.info(e)
            self.write(json.dumps({"type": 0}))
            self.finish()


class ReportErrorHandler(BaseHandler):
    def post(self):
        error = self.get_argument("error", "")
        log = self.get_argument("log", "")
        if error and log:
            folder = str(long(time()*1000))
            try:
                os.makedirs(r'%s/%s/%s' % (os.getcwd(), "report", folder))
            except Exception, e:
                logging.info(e)
            out = open(os.path.join(os.getcwd(), "report", folder, "error"), "w")
            out.write(error.encode("utf-8"))
            out.close()
            out = open(os.path.join(os.getcwd(), "report", folder, "log"), "w")
            out.write(log.encode("utf-8"))
            out.close()
            self.write(json.dumps({"type": 1}))
            self.finish()
        else:
            self.write(json.dumps({"type": 0}))
            self.finish()


class SnsShareHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # set cookie just for mock
        msg = {}
        uid = self.get_argument("uid", None)
        remote_ip = self.get_argument("ip", None)
        if uid:
            try:
                uid = long(uid)
                # remote_ip = self.request.remote_ip
                user_ip = UserIPCache.get_user_ip(uid)
                if (remote_ip is not None) and (remote_ip != user_ip):
                    yield FBCoinManager.sns_share_ok(uid, remote_ip)
                    msg = {"err": 0}
                else:
                    msg = {"err": 1, "what": "uid error"}
            except:
                msg = {"err": 1, "what": "uid error"}
        self.write(json.dumps(msg))
        self.finish()

# class TvHandler(BaseHandler):
#     @tokenCheck
#     @tornado.web.asynchronous
#     def get(self):
#         self.render("tv.html")
class OfferRewardHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        desc = self.get_argument("desc")
        fileName = self.get_argument("fileName")
        fb = self.get_argument("fb") 
        res_type = self.get_argument("res_type") 
        res_year = self.get_argument("res_year") 
        res_country = self.get_argument("res_country")
        uid = getUid(self)
        if uid and desc and fileName and fb and res_type and res_year and res_country:
            try:
                res_type = int(res_type)
                fb = long(fb)
                uid = long(uid)
                assert len(fileName) > 0
                assert ResourceInfo.is_valid_main_type(res_type)
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            desc = escape(desc)
            fileName = escape(fileName)
            res_year = escape(res_year)
            res_country = escape(res_country)
            yield Reward.user_offer_reward(uid, desc, fileName, fb, res_type, res_year, res_country)
            util.write(self, 1, "", {})
            self.finish()
            return
        else:
            util.errorHandle(self, 0)
            self.finish()

class AppendRewardHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        rid = self.get_argument("rid")
        appendFb = self.get_argument("appendFb")
        uid = getUid(self)
        if uid and rid and appendFb:
            try:
                uid = long(uid)
                appendFb = long(appendFb)
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            yield Reward.user_append_reward(uid, appendFb, rid)
            util.write(self, 1, "", {})
            self.finish()
            return
        else:
            util.errorHandle(self, 0)
            self.finish()

class CancelRewardHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        rid = self.get_argument("rid")
        res_type = self.get_argument("res_type")
        uid = getUid(self)
        if uid and rid and res_type:
            try:
                uid = long(uid)
                if res_type:
                    res_type = int(res_type)
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            result = yield Reward.user_cancel_reward(uid, rid, res_type)
            if result:
                util.write(self, 1, "", {})
            else:
                util.write(self, 0, "删除失败，请重试", {})
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class MyRewardHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        uid = getUid(self)
        res_type = self.get_argument("res_type", None)
        page = self.get_argument("page", 1)
        version = self.get_argument("version", 1.9)
        if uid:
            try:
                uid = long(uid)
                page = int(page)
                if res_type:
                    res_type = int(res_type)
                assert page > 0
            except:
                util.errorHandle(self, 0)
                self.finish()
                return            
            result = yield Reward.get_my_reward_by_type(version, uid, page, REWARD_CNT_IN_A_PAGE, res_type)
            all_rewards = result["rewards"]
            for item in all_rewards:
                if "file_infos" in item:
                    cipher_resource_list(item["file_infos"], version)
                    add_download_info_to_resource_list(item["file_infos"])
            util.write(self, 1, "", result)
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class AllRewardHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        uid = getUid(self)
        res_type = self.get_argument("res_type", None)
        time = self.get_argument("time", 1)
        page = self.get_argument("page", 1)
        sort_by = self.get_argument("sort_by", Reward.reward_sort_by["time"])
        version = self.get_argument("version", 1.9)
        if uid:
            try:
                uid = long(uid)
                time = int(time)
                sort_by = int(sort_by)
                page = int(page)
                if res_type is not None:
                    res_type = int(res_type)
                assert time > 0
                assert sort_by == Reward.reward_sort_by["time"] or sort_by == Reward.reward_sort_by["reward"]
            except:
                util.errorHandle(self, 0)
                self.finish()
                return            
            all_rewards = yield Reward.get_all_reward_by_type(version, page, time, REWARD_CNT_IN_A_PAGE, sort_by, res_type)
            size = yield Reward.get_reward_count_by_type(res_type)
            util.write(self, 1, "", {"total_page": util.getPages(size), "rewards": all_rewards})
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

'''
msg format
{"user":user_name, "msg_list":[{"isRead":True/False, "sender":user_name, "type":0 for sys/1 for add, "content":msg_content may be ""},...]}
when user login, we should store his/her http port,private-ip,public-ip(todo)
'''


class MainHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        #util.log(json.loads(self.request.headers.get("Cookie")))
        #token = self.xsrf_token
        remote_ip = self.request.remote_ip
        #cursor = yield db_realtime.users.find_one({"user":self.current_user},{"_id":0})
        #util.log("MainHandler.get")
        #util.log( cursor)
        ##msg = yield db.user_msg.find_one({'user': self.current_user}, {"_id": 0})
        msg = msg_handle.getAllMsg(self.current_user)
        #util.log(msg)  
        if msg:
            msg = msg["msg_list"]
            count = len(msg)
            '''
            for item in msg:
                if not item["isRead"]:
                    count += 1
            '''
            if self.get_argument("from", "chrome") == "client":
                #print "client"
                ret = {}
                ret["msg"] = msg
                ret["count"] = count
                ret["user"] = self.current_user
                util.write(self, 1, "", ret)
                self.finish()
            else:
                #print "chrome"            
                self.render("index.html", msg=msg, count=count)
        else:
            if self.get_argument("from", "chrome") == "client":
                #print "client"
                ret = {}
                ret["msg"] = []
                ret["count"] = 0
                ret["user"] = self.current_user
                util.write(self, 1, "", ret)
                self.finish()
            else:
                self.finish()
                #print "chrome"
                #self.render("index.html", msg=[], count=0)


class LoginHandler(BaseHandler):
    def get(self):
        raise tornado.web.HTTPError(404)

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        #token = self.xsrf_token
        #global login_token
        #global login_user
        if self.get_argument("user", "") and self.get_argument("pwd", "") and self.get_argument("token", ""):
            random.seed(hash(self.get_argument("user")))
            r = random.randint(1, 10000)
            if r == 10000:
                r = 9999
            elif r < 10:
                r = "000" + str(r)
            elif r < 100:
                r = "00" + str(r)
            elif r < 1000:
                r = "0" + str(r)
            user = yield db_realtime.users.find_one(
                                  {"user": self.get_argument("user"), "password": self.get_argument("pwd") + str(r)},
                                  {"_id": 0})
            #find = False
            if user and "user" in user:
                token = str(self.get_argument("token"))
                util.RedisPub.publish(CHANNEL_LOGIN, json.dumps({"user": user["user"]}))
                RedisHandler.f_set(key=str(user["uid"]), value=token, tp=RedisHandler.type_token)
                util.cacheUserInfo(user)                
                #print "redis token"
                #print util.RedisHandle.f_get(str(user["uid"]),util.RedisHandle.type_token)
                util.MemCache.set(str(user["uid"]), token, LOGIN_T, -1)
                #print "login user flag: " + str(login_user[l_user])
                self.set_cookie("fbt_user", util.encrypt(15, self.get_argument("user")))
                self.set_cookie("fbt_user_id", str(user["uid"]))
                # if self.get_argument("remember", "") and self.get_argument("remember") == "1":
                #     self.set_cookie("fbt_u",self.get_argument("user"))
                #     self.set_cookie("fbt_pwd",self.get_argument("pwd"))
                result = {}
                result["user"] = self.get_argument("user")
                result["nick_name"] = user["nick_name"]
                util.write(self, 1, "", result)
                self.finish()
                return
            else:
                #util.write(self, 0, u"登录邮箱没有通过邮箱验证或者登录邮箱与密码不匹配", {})
                util.write(self, 0, u"登录邮箱与密码不匹配，请重试", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


#when user close the client window, this requst can't be invoke,so there will be some
#token store in the login_token if this user don't use this account, when user login again
#the token will update
#delete for simple
class LogoutHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        #global login_token
        #when logout, close the socket
        #user_uid = str(getUid(self))
        #if util.RedisHandle.f_hexists(LOGIN_T, user_uid):
        #    util.RedisHandle.f_hdel(LOGIN_T, *[user_uid])
        #del(login_token[user_uid])
        #client_user = util.RedisHandle.f_hgetall(CLIENT_USER)
        #util.HttpClient.get(MSG_URL+MSG_URL_AUTH+str(MSG_SOCKET_CLOSE)+"&user="+self.current_user)
        # if util.RedisHandle.f_hexists(CLIENT_USER, self.current_user):
        #     util.log("logout, sock close")
        #     # cursor = yield db_realtime.users.find_one({"user":self.current_user},{"friends":1})
        #     # util.log("LogoutHandler.get")
        #     # util.log( cursor)
        #     # tell = {"type":1, "msg":self.current_user+" left"}
        #     #use send_to_all to test
        #     #SocketHandler.send_to_all(SocketHandler.client_user[self.current_user], json.dumps(tell))
        #     #SocketHandler.send_to_friends(cursor["friends"], json.dumps(tell))
        #     c = util.RedisHandle.f_hget(CLIENT_USER, self.current_user)
        #     sock = ctypes.cast(long(c), ctypes.py_object).value
        #     handle_close(self.current_user,sock,True)
        #     sock.close()
        self.clear_cookie("fbt_user")
        self.clear_cookie("fbt_user_id")
        self.clear_cookie("fbt_nick_name")
        util.write(self, 1, "", {})
        self.finish()


class RegistrationHandler(BaseHandler):
    def get(self):
        #token = self.xsrf_token
        #self.render("registration.html")
        pass

    #如果不需要邮件验证，则打开这个注释，并将另一个post函数注释即可
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        #token = self.xsrf_token
        if self.get_argument("user", "") and self.get_argument("pwd", ""):
            util.log("RegistrationHandler.post")
            util.log(self.get_argument("user"))
            user = yield db_realtime.users.find_one( {"user": self.get_argument("user")}, {"user": 1})
            if user and "user" in user:
                util.write(self, 0, u"注册邮箱已经存在,请选用其他注册邮箱", {})
                self.finish()
            else:
                nick = ""
                t = datetime.now()
                random.seed(hash(self.get_argument("user")))
                r = random.randint(1, 10000)
                if r == 10000:
                    r = 9999
                elif r < 10:
                    r = "000" + str(r)
                elif r < 100:
                    r = "00" + str(r)
                elif r < 1000:
                    r = "0" + str(r)
                tmp_uid = str(long(time())) + str(r)
                uid = long(tmp_uid)
                if self.get_argument("nick", ""):
                    nick = escape(self.get_argument("nick"))
                    user = yield db_realtime.users.find_one( {"nick_name": nick}, {"user": 1})
                    if user and "user" in user:
                        util.write(self, 0, u"昵称已经存在,请选用其他昵称", {})
                        self.finish()
                        return
                else:
                    nick = "fbt_" + str(uid)[0:10]
                r_i = str(random.randint(1, 36))
                icon = self.static_url('images/user_icon/' + r_i + '.jpg')
                real_name = escape(self.get_argument("name",""))
                gender = self.get_argument("gender", "")
                school = self.get_argument("school", "")
                university = school
                college = self.get_argument("college", "")

                new_user = {"uid": uid, 'user': escape(self.get_argument("user")), 'time': t.strftime('%Y-%m-%d %H:%M'),
                            'icon': icon, 'desc': u'我很懒，别怪我什么也没有留下！', 'real_name': real_name, 'phone': '', 'qq': '',
                            'gender': gender, 'love_state': '', 'school': school, 'address': '', 'college': college, 
                            'university': university, 'password': self.get_argument("pwd") + str(r), 'nick_name': nick, 'friends': []
                }
                refer = self.get_argument("refer", "")
                if refer and (refer == nick or refer == real_name):
                    util.write(self, 0, u"推荐人请不要与所填昵称或者真名相同", {})
                    self.finish()
                    return
                result = yield db_realtime.users.insert(new_user)
                yield FBCoinManager.register_ok(uid)
                identify = self.get_argument("identify", "")
                #msg_handle.initMsg(self.get_argument("user"))
                if self.get_argument("from", "client") == "chrome":
                    if self.get_argument("next", ""):
                        self.redirect(self.get_argument("next"))
                else:
                    util.write(self, 1, "", {"result": "注册成功，请直接登录！"})
                    self.finish()
                if refer and identify:
                    #add coin for the refer name
                    r = yield db.refer.find_one({"refer": refer}, {"identify": 1, "refer": 1})
                    notExist = True
                    if r and r["refer"] and identify in r["identify"]:
                        notExist = False
                    if notExist:
                        yield db.refer.update({"refer": refer}, {"$push": {"identify": identify}}, True)
                        cursor = yield db_realtime.users.find_one({"$or": [{"nick_name": refer}, {"real_name": refer}]},
                                                {"uid": 1, "user": 1})
                        if cursor and "uid" in cursor:
                            yield FBCoinManager.invite_a_user(cursor["uid"])
                            msg = {}
                            msg["type"] = 7
                            msg["content"] = u"您推荐的用户已注册成功，FBT奖励您100F币，请查收"
                            msg["sticky"] = 1
                            SocketHandler.send_to_one(cursor["uid"], json.dumps(msg))
                            msg = {}
                            msg["type"] = 0
                            #msg["isRead"] = 0
                            msg["id"] = str(uuid.uuid1().int)
                            msg["sender"] = "0"
                            msg["nick"] = "0"
                            msg["content"] = u"您推荐的用户已注册成功，FBT奖励您100F币，请查收"
                            msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
                            msg_handle.addMsg(cursor["user"], msg, "", "", "")
                find_password.send_intro_mail(self.get_argument("user"))
        else:
            util.errorHandle(self, 0)
            self.finish()
    # @tornado.web.asynchronous
    # @tornado.gen.coroutine
    # def post(self):
    #     #token = self.xsrf_token
    #     if self.get_argument("user", "") and self.get_argument("pwd", ""):
    #         user = yield db_realtime.tmp_users.find_one({"user":self.get_argument("user")},{"user":1})
    #         if user and "user" in user:
    #             util.write(self, 0, u"注册邮箱已经注册过，请到所用邮箱去验证", {})
    #             self.finish()
    #             return
    #         user = yield db_realtime.users.find_one({"user":self.get_argument("user")},{"user":1})
    #         if user and "user" in user:
    #             util.write(self, 0, u"注册邮箱已经存在,请选用其他邮箱注册", {})
    #             self.finish()
    #             return
    #         else:
    #             nick = ""
    #             t = datetime.now()
    #             random.seed(hash(self.get_argument("user")))
    #             r = random.randint(1, 10000)
    #             if r == 10000:
    #                 r = 9999
    #             elif r < 10:
    #                 r = "000" + str(r)
    #             elif r < 100:
    #                 r = "00" + str(r)
    #             elif r < 1000:
    #                 r = "0" + str(r)
    #             ##########################################
    #             ##########################################
    #             # DONT use tmp_uid = str(long(time()*1000)) + str(r)
    #             # tmp_uid = str(long(time()*1000)) + str(r)
    #             # if uid is 14342496299334313
    #             # javascript parseInt(14342496299334313)
    #             # will 14342496299334312
    #             ##########################################
    #             ##########################################
    #             tmp_uid = str(long(time())) + str(r)
    #             uid = long(tmp_uid)
    #             if self.get_argument("nick", ""):
    #                 nick = escape(self.get_argument("nick"))
    #                 user = yield db_realtime.users.find_one({"nick_name":nick},{"user":1})
    #                 if user and "user" in user:
    #                     util.write(self, 0, u"昵称已经存在,请选用其他昵称", {})
    #                     self.finish()
    #                     return
    #             else:
    #                 nick = "fbt_"+str(uid)[0:10]
    #             r_i = str(random.randint(1, 36))
    #             icon = self.static_url('images/user_icon/'+r_i+'.jpg')
    #             real_name = escape(self.get_argument("name",""))
    #             gender = self.get_argument("gender", "")
    #             school = self.get_argument("school", "")
    #             university = school
    #             college = self.get_argument("college", "")

    #             new_user = {"uid": uid, 'user': escape(self.get_argument("user")), 'time': t.strftime('%Y-%m-%d %H:%M'),
    #                         'icon': icon, 'desc': u'点击编辑', 'real_name': real_name, 'phone': '', 'qq': '',
    #                         'gender': gender, 'love_state': '', 'school': school, 'address': '', 'college': college, 
    #                         'university': university, 'password': self.get_argument("pwd") + str(r), 'nick_name': nick, 'friends': []
    #             }
    #             token = str(uuid.uuid1().int)
    #             new_user["token"] = token
    #             refer = self.get_argument("refer","")
    #             if refer and (refer == nick or refer == real_name):
    #                util.write(self, 0, u"推荐人请不要与所填昵称或者真名相同", {})
    #                self.finish()
    #                return
    #             identify = self.get_argument("identify","")
    #             new_user["refer"] = refer
    #             new_user["identify"] = identify
    #             yield db_realtime.tmp_users.insert(new_user)
    #             random.seed(token)
    #             r = random.randint(1, len(token)-1)
    #             tmp = token[:r]+"_"+token[r:]
    #             ret = find_password.send_registry_mail(new_user["user"], new_user["nick_name"], tmp)
    #             if ret:
    #                 util.write(self, 1, "", {"result": "注册成功，请验证您的邮箱！"})
    #                 self.finish()
    #             else:
    #                 util.write(self, 0, u"注册时出了点故障，请重试", {})
    #                 self.finish()
    #     else:
    #         util.errorHandle(self, 0)
    #         self.finish()


'''
param:op=[0=search,1=add,2=confirmAdd,3=delete,4 for star,5 for unstar,get fro getinfo],[search=search | user = user]
'''


class MyFriendHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("uid", ""):
            uid = self.get_argument("uid")
            try:
                uid = long(uid)
                user = yield util.getUserInfoById(uid)
                if user:
                    ##shuo = yield db.user_shuo.find_one({'user': user["user"]}, {"_id": 0})
                    re = msg_handle.getShuo(user["user"])
                    if re is None:
                        re = "点我编辑说说"
                    ret = {}
                    ret["shuo"] = re
                    ret["user"] = user
                    ret["size"] = yield ResourceStoreManager.get_one_resources_count(uid)
                    ret["size"] = util.getPages(ret["size"])
                    util.write(self, 1, "", ret)
                else:
                    util.write(self, 1, "", {})
                self.finish()
            except ValueError:
                util.errorHandle(self, 0)
                self.finish()
                return
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("op", ""):
            op = self.get_argument("op")
            if op[0] >= '0' and op[0] <= '9':
                op = int(op)
                util.log("MyFriendHandler.post")
                util.log(op)
                if op == 0:
                    yield self.search()
                elif op == 1:
                    yield self.add()
                elif op == 2:
                    yield self.confirmAdd()
                elif op == 3:
                    yield self.delete()
                elif op == 4:
                    yield self.star()
                elif op == 5:
                    yield self.unStar()
                elif op == 6:
                    self.readMsg()
                elif op == 7:
                    self.readAllMsg()
                elif op == 8:
                    yield self.addByNick()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    def readMsg(self):
        if self.get_argument("id", ""):
            msg_handle.ReadMsg(self.current_user, self.get_argument("id"))
            util.write(self, 1, "", "")
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    def readAllMsg(self):
        msg_handle.ReadAllMsg(self.current_user)
        util.write(self, 1, "", "")
        self.finish()

    @tornado.gen.coroutine
    def search(self):
        if self.get_argument("search", ""):
            search = self.get_argument("search")
            data = []
            cursor = db_realtime.users.find({"$or":
                                        [
                                            {"nick_name": {"$regex": search, '$options': '-i'}},
                                            {"real_name": {"$regex": search, '$options': '-i'}},
                                            {"user": {"$regex": search, '$options': '-i'}}
                                        ]})
            while (yield cursor.fetch_next):
                user = cursor.next_object()
                if user["user"] == self.current_user:
                    continue
                result = {}
                result["icon"] = user["icon"]
                result["nick_name"] = user["nick_name"]
                result["user"] = user["user"]
                result["real_name"] = user["real_name"]
                result["is_friend"] = 0
                for item in user["friends"]:
                    if item["user"] == self.current_user:
                        result["is_friend"] = 1
                        break
                data.append(result)
                # db_realtime.users.find({"$or":
            #     [
            #     {"user":search},
            #     {"nick_name":search}
            # ]},callback=(yield gen.Callback("key")))
            # user = yield gen.Wait("key")
            util.write(self, 1, "", json.dumps(data))
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    '''
    msg format
    {"user":user_name, "msg_list":[{"isRead":1/0, "sender":user_name, "type": 0, "content":msg_content may be ""},...]}
    '''

    @tornado.gen.coroutine
    def add(self):
        if self.get_argument("user", ""):
            user = self.get_argument("user")
            isExist = msg_handle.isMsgExist(user, self.current_user)
            #print "add friend"
            #print isExist
            if isExist:
                result = {"result": u"添加好友请求已发送,请等待对方确认"}
                util.write(self, 1, "", result)
                self.finish()
                return
            nick_name = yield db_realtime.users.find_one({'user': self.current_user}, {"nick_name": 1, "real_name": 1, "uid": 1})
            nick = nick_name["nick_name"]
            msg = {}
            msg["type"] = 0
            #msg["isRead"] = 0
            msg["id"] = str(uuid.uuid1().int)
            msg["sender"] = self.current_user
            msg["nick"] = nick
            if nick_name["real_name"]:
                nick = nick_name["real_name"] + "(" + nick + ")"
            msg["content"] = nick + u"想加你为好友,是否同意"
            msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
            SocketHandler.send_to_one(0, json.dumps(msg), user)
            msg_handle.addMsg(user, msg, self, u"添加好友请求已发送,请等待对方确认", u"添加好友请求失败,请重试")
            util.log("MyFriend.add")
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tornado.gen.coroutine
    def addByNick(self):
        if self.get_argument("nick_name", ""):
            nick_name = yield db_realtime.users.find_one({'user': self.current_user}, {"nick_name": 1, "real_name": 1, "uid": 1})
            target = yield db_realtime.users.find_one({'nick_name': self.get_argument("nick_name")}, {"user": 1})
            if not target:
                util.write(self, 0, "很抱歉，无法添加该好友", {})
                self.finish()
                return
            isExist = msg_handle.isMsgExist(target["user"], self.current_user)
            nick = nick_name["nick_name"]
            #print "add friend"
            #print isExist
            if isExist:
                result = {"result": u"添加好友请求已发送,请等待对方确认"}
                util.write(self, 1, "", result)
                self.finish()
                return
            msg = {}
            msg["type"] = 0
            #msg["isRead"] = 0
            msg["id"] = str(uuid.uuid1().int)
            msg["sender"] = self.current_user
            msg["nick"] = nick_name["nick_name"]
            if nick_name["real_name"]:
                nick = nick_name["real_name"] + "(" + nick + ")"
            msg["content"] = nick + u"想加你为好友,是否同意"
            msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')
            SocketHandler.send_to_one(0, json.dumps(msg), target["user"])
            msg_handle.addMsg(target["user"], msg, self, u"添加好友请求已发送,请等待对方确认", u"添加好友请求失败,请重试")
            util.log("MyFriend.add")
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tornado.gen.coroutine
    def delete(self):
        if self.get_argument("user", "") and self.get_argument("star", "") and self.get_argument("uid", ""):
            user = self.get_argument("user")
            star = self.get_argument("star")
            uid = self.get_argument("uid")
            my_uid = getUid(self)
            try:
                uid = long(uid)
            except ValueError:
                util.errorHandle(self, 0)
                self.finish()
                return;
            if star[0] >= '0' and star[0] <= '9':
                u1 = {"user": self.current_user, "isStar": 0}
                u2 = {"user": self.current_user, "isStar": 1}
                yield db_realtime.users.update({'user': user}, {'$pull': {"friends": u1}})
                yield db_realtime.users.update({'user': user}, {'$pull': {"friends": u2}})
                u = {"user": user, "isStar": int(star)}
                result = yield db_realtime.users.update({'user': self.current_user}, {'$pull': {"friends": u}})
                util.log("MyFriend.delete" + str(result))
                if ("nModified" in result and result["nModified"] == 1) \
                        or ("updatedExisting" in result and result["updatedExisting"] == True) \
                        or ("ok" in result and result["ok"] == 1):
                    if not ("writeConcernError" in result):
                        yield util.updateFriendsById(uid)
                        yield util.updateFriendsById(my_uid)
                        result = {"result": u"删除好友成功"}
                        util.write(self, 1, "", result)
                        self.finish()
                        SocketHandler.send_to_one(0, json.dumps({"type": 6, "uid": uid}), user)
                    else:
                        util.log(result["writeConcernError"])
                        util.write(self, 0, u"删除好友请求失败,请重试", {})
                        self.finish()
                else:
                    #util.log( result["writeError"])
                    util.write(self, 0, u"删除好友请求失败,请重试", {})
                    self.finish()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tornado.gen.coroutine
    def confirmAdd(self):
        flag = self.get_argument("flag", "")
        if flag and int(flag) == 0:
            msg_handle.ReadMsg(self.current_user, self.get_argument("id"))
            result = {"result": u"消息处理成功"}
            util.write(self, 1, "", result)
            self.finish()
            return
        if self.get_argument("user", "") and self.get_argument("id", ""):
            user = self.get_argument("user")
            uid_name = yield db_realtime.users.find_one({'user': self.current_user}, {'uid': 1, "nick_name": 1, "real_name": 1})
            re = {"user": self.current_user, "isStar": 0, "uid": uid_name["uid"], "nick_name": uid_name["nick_name"],
                  "real_name": uid_name["real_name"]}
            result = yield db_realtime.users.update({'user': user}, {'$addToSet': {"friends": re}})
            nick_name = uid_name["nick_name"]
            uid = uid_name["uid"]
            real_name = uid_name["real_name"]
            yield util.updateFriendsById(uid_name["uid"])

            uid_name = yield db_realtime.users.find_one({'user': user}, {'uid': 1, "nick_name": 1, "real_name": 1})
            re = {"user": user, "isStar": 0, "uid": uid_name["uid"], "nick_name": uid_name["nick_name"],
                  "real_name": uid_name["real_name"]}
            result = yield db_realtime.users.update({'user': self.current_user}, {'$addToSet': {"friends": re}})
            yield util.updateFriendsById(uid_name["uid"])

            msg_handle.ReadMsg(self.current_user, self.get_argument("id"))
            util.log("MyFriend.confirmAdd" + str(result))
            if ("nModified" in result and result["nModified"] == 1) \
                    or ("updatedExisting" in result and result["updatedExisting"] == True) \
                    or ("ok" in result and result["ok"] == 1):
                if not ("writeConcernError" in result):
                    result = {"result": u"添加好友成功"}
                    util.write(self, 1, "", result)
                    self.finish()
                    online = 0
                    all_token = util.MemCache.get(None, LOGIN_T)
                    #if self.current_user in SocketHandler.client_user:
                    if str(uid) in all_token:
                        online = 1
                    icon = yield util.getIconByUid(uid)
                    gender, school = yield util.getGenderAndSchoolByUid(uid)
                    msg = {"type": 0, "user": self.current_user, "uid": uid, "nick_name": nick_name, "online": online,
                           "real_name": real_name, "icon": icon, "gender": gender, "school": school, "isStar": 0}
                    SocketHandler.send_to_one(0, json.dumps(msg), user)
                    online = 0
                    if str(re["uid"]) in all_token:
                        online = 1
                    icon = yield util.getIconByUid(re["uid"])
                    gender, school = yield util.getGenderAndSchoolByUid(re["uid"])
                    msg = {"type": 0, "user": user, "uid": re["uid"], "nick_name": re["nick_name"], "online": online,
                           "real_name": uid_name["real_name"], "icon": icon, "gender": gender, "school": school, "isStar": 0}
                    SocketHandler.send_to_one(0, json.dumps(msg), self.current_user)
                else:
                    util.log(result["writeConcernError"])
                    util.write(self, 0, u"添加好友请求失败,请重试", {})
                    self.finish()
            else:
                #util.log( result["writeError"])
                util.write(self, 0, u"添加好友请求失败,请重试", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tornado.gen.coroutine
    def star(self):
        if self.get_argument("user", ""):
            user = self.get_argument("user")
            result = yield db_realtime.users.update({'user': self.current_user, "friends.user": user},
                                           {'$set': {"friends.$.isStar": 1}})
            util.log("MyFriend.star" + str(result))
            if ("nModified" in result and result["nModified"] == 1) \
                    or ("updatedExisting" in result and result["updatedExisting"] == True) \
                    or ("ok" in result and result["ok"] == 1):
                if not ("writeConcernError" in result):
                    result = {"result": u"关注好友成功"}
                    util.write(self, 1, "", result)
                    self.finish()
                else:
                    util.log(result["writeConcernError"])
                    util.write(self, 0, u"关注好友请求失败,请重试", {})
                    self.finish()
            else:
                #util.log( result["writeError"])
                util.write(self, 0, u"关注好友请求失败,请重试", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tornado.gen.coroutine
    def unStar(self):
        if self.get_argument("user", ""):
            user = self.get_argument("user")
            result = yield db_realtime.users.update({'user': self.current_user, "friends.user": user},
                                           {'$set': {"friends.$.isStar": 0}})
            util.log("MyFriend.unStar" + str(result))
            if ("nModified" in result and result["nModified"] == 1) \
                    or ("updatedExisting" in result and result["updatedExisting"] == True) \
                    or ("ok" in result and result["ok"] == 1):
                if not ("writeConcernError" in result):
                    result = {"result": u"取消关注好友成功"}
                    util.write(self, 1, "", result)
                    self.finish()
                else:
                    util.log(result["writeConcernError"])
                    util.write(self, 0, u"取消关注好友请求失败,请重试", {})
                    self.finish()
            else:
                #util.log( result["writeError"])
                util.write(self, 0, u"取消关注好友请求失败,请重试", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


'''
op: 0 for add, 1 for get, 2 for del
param:
'''


class MyShuoHandler(BaseHandler):
    @tokenCheck
    def post(self):
        if self.get_argument("op", ""):
            op = self.get_argument("op")
            if op[0] >= '0' and op[0] <= '9':
                op = int(op)
                util.log("MyShuoHandler.post")
                util.log(op)
                if op == 0:
                    self.add()
                elif op == 1:
                    pass
                    #self.g()
                elif op == 2:
                    pass
                    #self.delete()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    def add(self):
        if self.get_argument("param", ""):
            param = self.get_argument("param")
            param = escape(param)
            msg_handle.addShuo(self.current_user, param)
            util.write(self, 1, "", "")
            util.log("MyShuoHandler.add")
        else:
            util.errorHandle(self, 0)
            self.finish()

    def g(self):
        ##result = yield db.user_shuo.find_one({'user': self.current_user}, {"_id": 0})
        result = msg_handle.getAllShuo(self.current_user)
        util.log("MyShuoHandler.get" + str(result))
        if result:
            util.write(self, 1, "", result)
        else:
            util.errorHandle(self, 1)

    def delete(self):
        if self.get_argument("param", ""):
            param = self.get_argument("param")
            msg_handle.delShuo(self.current_user, param, self, u"删除成功", u"删除失败,请重试")
            util.log("MyShuoHandler.delete")
        else:
            util.errorHandle(self, 0)
            self.finish()


# class MySpaceHandler(BaseHandler):
#     @tokenCheck
#     @gen.coroutine
#     @tornado.web.asynchronous
#     def get(self):
#         if self.current_user:
#             cursor = yield db_realtime.users.find_one( {"user": self.current_user}, {"_id": 0, "time": 0})
#             util.log("MySpaceHandler.get")
#             util.log(cursor)
#             friends = cursor["friends"]
#             count = 0
#             client_user = util.MemCache.get(None, LOGIN_T)
#             #print client_user
#             for item in friends:
#                 item["icon"] = yield util.getIconByUid(item["uid"])
#                 gender, school = yield util.getGenderAndSchoolByUid(item["uid"])
#                 item["gender"] = gender
#                 item["school"] = school
#                 if str(item["uid"]) in client_user:
#                     item["online"] = 1
#                     count += 1
#                 else:
#                     item["online"] = 0
#             re = ""
#             ##shuo = yield db.user_shuo.find_one({'user': self.current_user}, {"_id": 0})
#             shuo = msg_handle.getAllShuo(self.current_user)
#             util.log(shuo)
#             if shuo:
#                 tmp = shuo["shuo_list"]
#                 re = tmp[len(tmp) - 1]["content"]
#             #get all the friends' shuo
#             # all_shuo = []
#             # for item in friends:
#             #     shuo = yield db.user_shuo.find_one({'user': self.current_user},{"_id":0})
#             #     if shuo:
#             #         tmp = shuo["shuo_list"]
#             #         all_shuo.append(tmp[len(tmp)-1])
#             #sorted(all_shuo, key=itemgetter("time"))
#             fb_coin = yield FBCoinManager.get_user_total_fb_coin(long(getUid(self)))
#             #print "fb_coin "+str(fb_coin)
#             if self.get_argument("from", "chrome") == "client":
#                 # l = cursor["icon"].find("?")
#                 # cursor["icon"] = cursor["icon"][0:l]
#                 ret = {}
#                 #ret["all_shuo"] = all_shuo
#                 ret["friends"] = friends
#                 ret["icon"] = cursor["icon"]
#                 ret["nick_name"] = cursor["nick_name"]
#                 ret["real_name"] = cursor["real_name"]
#                 ret["shuo"] = re
#                 ret["count"] = len(friends)
#                 ret["count_online"] = count
#                 ret["fb_coin"] = fb_coin
#                 util.write(self, 1, "", ret)
#                 self.finish()
#             else:
#                 self.render("mySpace.html", user=cursor, friends=friends, shuo=re,
#                             count=len(friends), count_online=count)

class MySpaceHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.current_user:
            version = self.get_argument("version", "1.9")
            cursor = yield db_realtime.users.find_one( {"user": self.current_user}, {"_id": 0, "time": 0})
            util.log("MySpaceHandler.get")
            util.log(cursor)
            friends = cursor["friends"]
            count = 0
            client_user = util.MemCache.get(None, LOGIN_T)
            if version >= "2.0":
                for item in friends:
                    item["icon"] = yield util.getIconByUid(item["uid"])
                    gender, school = yield util.getGenderAndSchoolByUid(item["uid"])
                    item["gender"] = gender
                    item["school"] = school
                    if str(item["uid"]) in client_user:
                        item["online"] = 1
                        count += 1
                    else:
                        item["online"] = 0
            else:
                for item in friends:
                    if str(item["uid"]) in client_user:
                        item["online"] = 1
                        count += 1
                    else:
                        item["online"] = 0
            re = msg_handle.getShuo(self.current_user)
            if re is None:
                re = "点我编辑说说"
            # shuo = msg_handle.getAllShuo(self.current_user)
            # util.log(shuo)
            # if shuo:
            #     tmp = shuo["shuo_list"]
            #     re = tmp[len(tmp) - 1]["content"]
            fb_coin = yield FBCoinManager.get_user_total_fb_coin(long(getUid(self)))
            if self.get_argument("from", "chrome") == "client":
                ret = {}
                ret["friends"] = friends
                ret["icon"] = cursor["icon"]
                ret["nick_name"] = cursor["nick_name"]
                ret["real_name"] = cursor["real_name"]
                ret["shuo"] = re
                ret["count"] = len(friends)
                ret["count_online"] = count
                ret["fb_coin"] = fb_coin
                if version >= "2.0":
                    ret["size"] = yield ResourceStoreManager.get_one_resources_count(long(getUid(self)))
                    ret["size"] = util.getPages(ret["size"])
                util.write(self, 1, "", ret)
                self.finish()
            else:
                self.render("mySpace.html", user=cursor, friends=friends, shuo=re,
                            count=len(friends), count_online=count)

class MyInfoHandler(BaseHandler):
    keys = ["real_name", "phone", "qq", "gender", "love_state", "school", "address", "nick_name", "password",
            "originPwd", "college", "freshyear", "weibo"]

    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        version = self.get_argument("version", "1.9")
        user = yield db_realtime.users.find_one( {"user": self.current_user}, {"_id": 0, "time": 0})
        if not user:
            if self.get_argument("from", "chrome") == "client":
                ret = {}
                ret["shuo"] = u"点击编辑，鼠标移开即可保存"
                ret["user"] = {}
                ret["size"] = 0
                util.write(self, 1, "", ret)
                self.finish()
            else:
                self.render("myInfo.html", user={}, shuo="")
        else:
            ##shuo = yield db.user_shuo.find_one({'user': self.current_user}, {"_id": 0})
            re = msg_handle.getShuo(self.current_user)
            if re is None:
                re = "点我编辑说说"
            if self.get_argument("from", "chrome") == "client":
                # l = user["icon"].find("?")
                # user["icon"] = user["icon"][0:l]
                ret = {}
                ret["shuo"] = re
                ret["user"] = user
                if version < "2.0":
                    ret["size"] = yield ResourceStoreManager.get_one_resources_count(user["uid"])
                    ret["size"] = util.getPages(ret["size"])
                util.write(self, 1, "", ret)
                self.finish()
            else:
                self.render("myInfo.html", user=user, shuo=re)

    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("data", "") and self.get_argument("ext", ""):
            ext = self.get_argument("ext")
            if ext[0] != ".":
                ext = "." + ext
            p = os.path.join(os.getcwd(), "static", "images", "user_icon", str(getUid(self)) + ext)
            try:
                f = open(p, "wb")
                data = self.get_argument("data").decode('base64')
                f.write(data)
                f.close()
                icon = self.static_url('images/user_icon/' + getUid(self) + ext)
                result = yield db_realtime.users.update({"user": self.current_user}, {"$set": {"icon": icon}})
                if ("nModified" in result and result["nModified"] == 1) \
                        or ("updatedExisting" in result and result["updatedExisting"] == True) \
                        or ("ok" in result and result["ok"] == 1):
                    if not ("writeConcernError" in result):
                        util.write(self, 1, "", icon)
                        self.finish()
                    else:
                        util.log(result["writeConcernError"])
                        util.write(self, 0, u"保存失败,请重试", {})
                        self.finish()
                else:
                    #util.log( result["writeError"])
                    util.write(self, 0, u"保存失败,请重试", {})
                    self.finish()
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            return
        if self.get_argument("user", ""):
            user = self.get_argument("user")
            try:
                user = json.loads(user)
            except Exception, e:
                print e
                util.errorHandle(self, 0)
                self.finish()
                return
            if not user:
                util.errorHandle(self, 0)
                self.finish()
                return
            isError = False
            for item in user.keys():
                if item not in MyInfoHandler.keys:
                    isError = True
                    break
            if not isError:
                if "school" in user:
                    user["university"] = user["school"]
                if "icon" in user:
                    user["icon"] = self.static_url(user["icon"])
                if "password" in user:
                    random.seed(hash(self.current_user))
                    r = random.randint(1, 10000)
                    if r == 10000:
                        r = 9999
                    elif r < 10:
                        r = "000" + str(r)
                    elif r < 100:
                        r = "00" + str(r)
                    elif r < 1000:
                        r = "0" + str(r)
                    u = yield db_realtime.users.find_one({"user": self.current_user, "password": user["originPwd"] + str(r)},{"user":1})
                    if u and "user" in u:
                        user["password"] = user["password"] + str(r)
                        del user["originPwd"]
                    else:
                        util.write(self, 0, u"原始密码不符,请重试", {})
                        self.finish()
                        return
                if "nick_name" in user:
                    nick = user["nick_name"]
                    if nick:
                        u = yield db_realtime.users.find_one({"nick_name": nick},{"user":1})
                        if u and "user" in u:
                            util.write(self, 0, u"昵称已经存在,请选用其他昵称", {})
                            self.finish()
                            return
                    else:
                        del (user["nick_name"])
                        if not user:
                            result = {"result": u"保存成功"}
                            util.write(self, 1, "", result)
                            self.finish()
                            return
                future = db_realtime.users.update({'user': self.current_user}, {'$set': user})
                result = yield future
                util.log(result)
                if ("nModified" in result and result["nModified"] == 1) \
                        or ("updatedExisting" in result and result["updatedExisting"] == True) \
                        or ("ok" in result and result["ok"] == 1):
                    if not ("writeConcernError" in result):
                        result = {"result": u"保存成功"}
                        util.write(self, 1, "", result)
                        self.finish()
                        return
                    else:
                        util.log(result["writeConcernError"])
                        util.write(self, 0, u"保存失败,请重试", {})
                        self.finish()
                        return
                else:
                    #util.log( result["writeError"])
                    util.write(self, 0, u"保存失败,请重试", {})
                    self.finish()
                    return
            else:
                util.write(self, 0, u"保存失败,请重试", {})
                self.finish()
                return
        else:
            util.errorHandle(self, 0)
            self.finish()
            return


class HttpServerInfoHandler(BaseHandler):
    def get(self):
        user = getUid(self)
        if not user:
            user = self.get_argument("user", None)  # mock user since node client has no cookie
            user = Cipher.decrypt(user)
        if user:
            try:
                user = long(user)
            except ValueError:
                err = json.dumps({"err": 5, "what": "invalid uid"})
                self.write(err)
                return
            ip = self.get_argument("ip", None)
            port = self.get_argument("port", None)
            if ip and port:
                ip = Cipher.decrypt(ip)
                port = Cipher.decrypt(port)
                if port.isdigit():
                    port = int(port)
                    if IP.is_valid_ipv4_address(ip):
                        #print "v4 info"
                        util.RedisPub.publish(CHANNEL_SERVER_INFO, json.dumps({"type": 0, "ip": ip, "uid": user, "port": port}))
                        HttpServerInfoCache.update_ipv4_address(user, ip, port)
                        util.write(self, 1, "", "success")
                        self.finish()
                    elif IP.is_valid_ipv6_address(ip):
                        #print "v6 info"
                        util.RedisPub.publish(CHANNEL_SERVER_INFO, json.dumps({"type": 1, "ip": ip, "uid": user, "port": port}))
                        HttpServerInfoCache.update_ipv6_address(user, ip, port)
                        util.write(self, 1, "", "success")
                        self.finish()
                    else:
                        util.write(self, 0, "port number err or ip address format err. ip:" + ip + " port:" + port, {})
                        self.finish()
                else:
                    util.errorHandle(self, 0)
                    self.finish()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.write(self, 0, u"请先登录", {})
            self.finish()


class TcpServerInfoHandler(BaseHandler):
    def get(self):
        user = getUid(self)
        if not user:
            user = self.get_argument("user", None)  # mock user since node client has no cookie
        if user:
            try:
                user = long(user)
            except ValueError:
                err = json.dumps({"err": 5, "what": "invalid uid"})
                self.write(err)
                return
            ip_list_str = self.get_argument("ip_list", None)
            if ip_list_str:
                try:
                    ip_list = json.loads(ip_list_str)
                except Exception as e:
                    err = json.dumps({"err": 5, "what": "invalid ip"})
                    self.write(err)
                    return
                util.write(self, 1, "", "success:"+ip_list_str)
                self.finish()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.write(self, 0, u"请先登录", {})
            self.finish()


class ViewDirHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        dir_hash = self.get_argument("dirHash", None)
        dir_size = self.get_argument("dirSize", None)
        uid = self.get_argument("uid", None)
        try:
            if uid:
                uid = long(uid)
            dir_size = long(dir_size)
            assert dir_size > 0
            assert dir_hash is not None
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        dirId = gen_file_id(dir_hash, dir_size)
        resource_list = yield ResourceStoreManager.get_files_from_dir(dirId, uid)
        util.write(self, 1, "", resource_list)
        self.finish()

class FeedHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        uid = getUid(self)
        time = self.get_argument("time", 1)
        page = self.get_argument("page", 1)
        try:
            time = int(time)
            page = int(page)
            uid = int(uid)
        except Exception, e:
            util.errorHandle(self, 0)
            self.finish()
            return
        feeds = yield FeedManager.get_feed(uid, time, page)
        util.write(self, 1, "", feeds)
        self.finish()

class CommentHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        uid = getUid(self)
        op = self.get_argument('op', '')
        hash = self.get_argument('hash', '')
        size = self.get_argument('size', '')
        comment = self.get_argument('comment', '')
        fname = self.get_argument('rname', '')
        time = self.get_argument('time', 1)
        try:
            uid = int(uid)
        except Exception, e:
            util.errorHandle(self, 0)
            self.finish()
            return
        if op and hash and size:
            if op == '0':
                #get comment
                try:
                    time = int(time)
                except Exception, e:
                    util.errorHandle(self, 0)
                    self.finish()
                    return
                comments = yield CommentManager.getComment(gen_file_id(hash, size), time)
                util.write(self, 1, "", comments)
                self.finish()
            elif op == '1' and comment and fname:
                #post comment
                comment = escape(comment)
                info = yield util.getUserInfoById(uid)
                rid = gen_file_id(hash, size)
                yield CommentManager.addComment(rid, fname, uid, info["nick_name"], info["icon"], comment)
                yield FeedManager.add_feed(rid, fname, uid, FeedManager.TYPE_COMMENT, "")
                util.write(self, 1, "", "comment success")
                self.finish()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

class ResourceDelHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("del", "") and self.get_argument("uid", ""):
            del_list = str(self.get_argument("del"))
            if del_list == "nul":
                util.write(self, 1, "", "delete success")
                self.finish()
                return
            size_list = self.get_argument("size", None)
            if size_list:
                size_list = map(int, str(size_list).split(","))
            dir_list = self.get_argument("isDir", None)
            if dir_list:
                dir_list = map(int, str(dir_list).split(","))
            del_list = del_list.split(",")
            uid = self.get_argument("uid")
            i = 0
            for file_hash in del_list:
                file_id = None
                try:
                    uid = long(uid)
                    file_hash = long(file_hash)
                    assert (uid >= 0)
                    assert (file_hash > 0)
                except:
                    util.errorHandle(self, 0)
                    self.finish()
                    return
                is_subfile = False
                if size_list:
                    if dir_list[i]:
                        is_subfile = True
                    file_id = gen_file_id(file_hash, size_list[i])
                    yield ResourceStoreManager.remove_owner(file_id, uid, is_subfile)
                else:
                    file_id = yield ResourceStoreManager.file_hash2file_id(file_hash)
                    yield ResourceStoreManager.remove_owner(file_id, uid)
                i += 1
                yield LogForUser.log_user_delete(uid, long(time()), file_id)
                util.RedisPub.publish(CHANNEL_RES_DEL, json.dumps({"file_id": file_id, "uid": uid, 'is_subfile': is_subfile}))
            #tell = {"type":4, "coin": FBCoinManager._coin_rules["delete_an_uploaded_public_resource"]}
            #SocketHandler.send_to_one(SocketHandler.client_uid_user[uid], json.dumps(tell))
            util.write(self, 1, "", "delete success")
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


class ResourceDirUploadHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("name", "") and self.get_argument("label", "") \
                and self.get_argument("fileInfo", "") and self.get_argument("desc", "") and self.get_argument(
                "mainType", "") \
                and self.get_argument("subType", "") and self.get_argument("grade", "") and self.get_argument(
                "isPublic", "") \
                and self.get_argument("nick_name", ""):
            fileInfo = self.get_argument("fileInfo")
            main_type = self.get_argument("mainType")
            sub_type = self.get_argument("subType")
            res_grade = self.get_argument("grade")
            uid = getUid(self)
            is_public = self.get_argument("isPublic", "1")
            tag = Cipher.decrypt(self.get_argument("label")).strip()
            fileName = Cipher.decrypt(self.get_argument("name")).strip()
            desc = Cipher.decrypt(self.get_argument("desc")).strip()
            userDirId = self.get_argument("userDirId", None)
            isV4 = self.get_argument("isV4", "0")
            rid = self.get_argument("rid", "")
            reward = 0
            if rid:
                reward = 1
            result = {"result": "1"}
            try:
                uid = long(uid)
                main_type = int(main_type)
                sub_type = int(sub_type)
                res_grade = float(res_grade)
                if res_grade < 0:
                    res_grade = 5
                fileInfo = json.loads(fileInfo)
                file_size = len(fileInfo)
                is_public = int(is_public)
                reward = int(reward)
                assert len(fileName) > 0
                assert uid > 0
                assert main_type >= 0
                assert sub_type >= 0
                assert file_size > 0
                assert len(self.get_argument("nick_name")) > 0
                assert len(desc) > 0
                assert res_grade >= 0 and res_grade <= 10
                assert is_public == 0 or is_public == 1
                assert len(tag) > 0
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            r = random.randint(1, 999)
            if r < 10:
                r = "00" + str(r)
            elif r < 100:
                r = "0" + str(r)
            fileHash = long(str(long(time()*1000))+str(r))
            #print uid
            if uid:
                #print "start upload"
                #fileInfo [{"hash":567868,"name":"test","size":1234},{}]
                ext_info = self.get_argument("ext_info", "")
                if ext_info:
                    ext_info = json.loads(ext_info)
                    if "img" in ext_info:
                        p_dir = os.path.join(os.getcwd(), "static", "images", "res_icon")
                        if not os.path.isdir(p_dir):
                            os.makedirs(p_dir)
                        p = os.path.join(p_dir, str(getUid(self)) + str(int(time())) + ".jpg")
                        try:
                            f = open(p, "wb")
                            data = ext_info["img"].decode('base64')
                            f.write(data)
                            f.close()
                            icon = self.static_url('images/res_icon/' + str(getUid(self)) + str(int(time())) + ".jpg")
                            ext_info["link"] = icon
                            del ext_info["img"]
                            #del ext_info["img"]
                            #print icon
                        except:
                            ext_info["link"] = ""
                        #add comment from douban
                        if "comments" in ext_info:
                            # for comment in ext_info["comments"]:
                            # comment=Cipher.decrypt(comment)
                            # yield ResourceStoreManager.add_comment(h,14156112684836,u"豆瓣",comment)
                            del ext_info["comments"]
                            #ext_info = json.dumps(ext_info)
                    yield ResourceStoreManager.user_upload_dir(reward, isV4, fileInfo, uid, self.get_argument("nick_name"),
                                                               fileHash,
                                                               fileName, file_size,
                                                               is_public,
                                                               [tag],
                                                               main_type, sub_type,
                                                               res_grade,
                                                               desc,ext_info,userDirId)
                else:
                    yield ResourceStoreManager.user_upload_dir(reward, isV4, fileInfo, uid, self.get_argument("nick_name"),
                                                               fileHash,
                                                               fileName, file_size,
                                                               is_public,
                                                               [tag],
                                                               main_type, sub_type,
                                                               res_grade,
                                                               desc,None,userDirId)
                #tell = {"type":4, "coin": FBCoinManager._coin_rules["uploaded_a_public_resource"]}
                #SocketHandler.send_to_one(self.current_user, json.dumps(tell))
                #print "finish upload"
                fileId = gen_file_id(fileHash, file_size)
                yield FeedManager.add_feed(fileId, fileName, uid, FeedManager.TYPE_UPLOAD, "")
                util.write(self, 1, "", result)
                self.finish()
                if rid:
                    yield Reward.user_upload_file(uid, fileId, rid)
                yield LogForUser.log_user_upload(uid, long(time()), fileId)
            else:
                util.write(self, 0, u"cookie 错误", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


class ResourceUploadHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("name", "") and self.get_argument("label", "") \
                and self.get_argument("hash", "") and self.get_argument("desc", "") and self.get_argument("mainType",
                                                                                                          "") \
                and self.get_argument("subType", "") and self.get_argument("grade", "") and self.get_argument(
                "isPublic", "") \
                and self.get_argument("fileSize", "") and self.get_argument("nick_name", ""):
            h = self.get_argument("hash")
            main_type = self.get_argument("mainType")
            sub_type = self.get_argument("subType")
            res_grade = self.get_argument("grade")
            file_size = self.get_argument("fileSize")
            uid = getUid(self)
            is_public = self.get_argument("isPublic", "1")
            tag = Cipher.decrypt(self.get_argument("label")).strip().split(',')
            fileName = Cipher.decrypt(self.get_argument("name")).strip()
            desc = Cipher.decrypt(self.get_argument("desc")).strip()
            isV4 = self.get_argument("isV4", "0")
            rid = self.get_argument("rid", "")
            reward = 0
            if rid:
                reward = 1
            result = {"result": "1"}
            try:
                uid = long(uid)
                main_type = int(main_type)
                sub_type = int(sub_type)
                res_grade = float(res_grade)
                if res_grade < 0:
                    res_grade = 5
                file_size = int(file_size)
                h = long(h)
                is_public = int(is_public)
                desc = escape(desc)
                fileName = escape(fileName)
                reward = int(reward)
                assert h > 0
                assert len(fileName) > 0
                assert uid > 0
                assert main_type >= 0
                assert sub_type >= 0
                assert file_size > 0
                assert len(self.get_argument("nick_name")) > 0
                assert len(desc) > 0
                assert res_grade >= 0 and res_grade <= 10
                assert is_public == 0 or is_public == 1
                assert len(tag) > 0
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            #print uid
            if uid:
                #print "start upload"
                ext_info = self.get_argument("ext_info", "")
                if ext_info:
                    ext_info = json.loads(ext_info)
                    if "img" in ext_info:
                        p_dir = os.path.join(os.getcwd(), "static", "images", "res_icon")
                        if not os.path.isdir(p_dir):
                            os.makedirs(p_dir)
                        p = os.path.join(p_dir, str(getUid(self)) + str(int(time())) + ".jpg")
                        try:
                            f = open(p, "wb")
                            data = ext_info["img"].decode('base64')
                            f.write(data)
                            f.close()
                            icon = self.static_url('images/res_icon/' + str(getUid(self)) + str(int(time())) + ".jpg")
                            ext_info["link"] = icon
                            del ext_info["img"]
                            #del ext_info["img"]
                            #print icon
                        except:
                            ext_info["link"] = ""
                        #add comment from douban
                        if "comments" in ext_info:
                            # for comment in ext_info["comments"]:
                            # comment=Cipher.decrypt(comment)
                            # yield ResourceStoreManager.add_comment(h,14156112684836,u"豆瓣",comment)
                            del ext_info["comments"]
                            #ext_info = json.dumps(ext_info)
                    yield ResourceStoreManager.user_upload_resource(reward, isV4, uid, self.get_argument("nick_name"),
                                                                    h, fileName, file_size, is_public, tag, main_type,
                                                                    sub_type, res_grade, desc,
                                                                    ext_info)
                else:
                    yield ResourceStoreManager.user_upload_resource(reward, isV4, uid, self.get_argument("nick_name"),
                                                                    h, fileName, file_size, is_public, tag, main_type,
                                                                    sub_type, res_grade, desc,
                                                                    None)
                #tell = {"type":4, "coin": FBCoinManager._coin_rules["uploaded_a_public_resource"]}
                #SocketHandler.send_to_one(self.current_user, json.dumps(tell))
                #print "finish upload"
                fileId = gen_file_id(h, file_size)
                link = ''
                description = ''
                if ext_info and 'link' in ext_info and 'summary' in ext_info:
                    link = ext_info['link']
                    description = ext_info['summary']
                yield FeedManager.add_feed(fileId, fileName, uid, FeedManager.TYPE_UPLOAD, "", link, description)
                info = yield util.getUserInfoById(uid)
                yield CommentManager.addComment(fileId, fileName, uid, info["nick_name"], info["icon"], desc)
                ext_info = None
                util.write(self, 1, "", result)
                self.finish()
                if rid:
                    yield Reward.user_upload_file(uid, fileId, rid)
                yield LogForUser.log_user_upload(uid, long(time()), fileId)
            else:
                util.write(self, 0, u"cookie 错误", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


'''
res_tag={"tag":"tag1","hash_list":[hash1,hash2,...],...}
res_content={"hash":"hash1","content":{"tags": [], name: "", owners:[{"user":"","desc":"","time":""},],comments:[{name:"",content:"",time:""},{}]}
res_user={"user":user,"hash":[]}
when user login, we should update his/her resource msg, this action is not over
op(7 for search, 1 for get, 2 for update, 3 for del, 4 for get res list,5 for comment,6 for score)
'''


class ResourceHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.get_argument("op", ""):
            op = self.get_argument("op")
            if op == '4':
                yield self.get_res_list()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        if self.get_argument("op", ""):
            op = self.get_argument("op")
            if op[0] >= '0' and op[0] <= '9':
                op = int(op)
                util.log("ResourceHandler.post")
                util.log(op)
                if op == 7:
                    #yield self.search()
                    #yield util.remoteRequest(self, 'http://localhost:8891/res/search', 'POST', ["version", "user", "page", "sort_by", "key_word"])
                    args = dict()
                    for arg in ["version", "user", "page", "sort_by", "key_word"]:
                        val = self.get_argument(arg, None)
                        if val:
                            args[arg] = val
                    RPC_client = RPCClient()
                    if RPC_client.is_iostream_setted():
                        tcp_client = TCPClient()
                        RPC_iostream = tcp_client.connect('127.0.0.1', SEARCH_RPC_SERVER_PORT)
                        RPC_client.set_iostream(RPC_iostream)
                    RPC_client.add_request(self, 'search', **args)
                elif op == 1:
                    yield self.g()
                elif op == 2:
                    yield self.update()
                elif op == 3:
                    yield self.delete()
                elif op == 4:
                    yield self.get_res_list()
                elif op == 5:
                    yield self.comment()
                elif op == 6:
                    yield self.score()
            else:
                util.errorHandle(self, 0)
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    # '''
    # param:
    # op(0 for search, 1 for get, 2 for update, 3 for del, 4 for get res list,5 for comment),name|tag
    # '''
    # @gen.coroutine
    # @tornado.web.asynchronous
    # def search(self):
    #     """ by type{by hot,by latest},by page """
    #     version = self.get_argument("version","")
    #     user = self.get_argument("user", None) 
    #     page = self.get_argument("page", 1)
    #     sort_by = self.get_argument("sort_by", ResourceStoreManager.res_sort_by["time"])
    #     key_word = self.get_argument("key_word", "")
    #     try:
    #         user = long(user)
    #         page = int(page)
    #         assert page>0
    #         sort_by = int(sort_by)
    #         assert sort_by==ResourceStoreManager.res_sort_by["time"] or sort_by==ResourceStoreManager.res_sort_by["download_num"]
    #         key_word=Cipher.decrypt(key_word).strip()
    #         assert len(key_word)>0
    #     except:
    #         util.errorHandle(self, 0)
    #         self.finish()
    #         return
    #     RES_CNT_IN_A_PAGE=20
    #     result = yield ResourceStoreManager.search_resources(version, key_word,page,sort_by,RES_CNT_IN_A_PAGE)
    #     resource_list = result["res"]
    #     cipher_resource_list(resource_list)
    #     add_download_info_to_resource_list(resource_list)       
    #     if version >= "1.8":
    #         util.write(self, 1, "", {"size":result["size"], "res":resource_list})
    #     else:
    #         util.write(self, 1, "", resource_list)
    #     self.finish()
    #     yield LogForUser.log_user_search(user, long(time()), key_word, result["size"])

    @gen.coroutine
    def g(self):
        pass

    '''
    param:
    op(0 for search, 1 for get, 2 for update, 3 for del),id,name,hash,label,desc
    '''

    @gen.coroutine
    def update(self):
        if self.get_argument("name", "") and self.get_argument("label", "") \
                and self.get_argument("hash", "") and self.get_argument("desc", "") and self.get_argument("mainType",
                                                                                                          "") \
                and self.get_argument("subType", "") and self.get_argument("grade", "") and self.get_argument(
                "isPublic", "") \
                and self.get_argument("fileSize", "") and self.get_argument("nick_name", ""):
            h = self.get_argument("hash")
            main_type = self.get_argument("mainType")
            sub_type = self.get_argument("subType")
            res_grade = self.get_argument("grade")
            file_size = self.get_argument("fileSize")
            uid = getUid(self)
            is_public = self.get_argument("isPublic", "1")
            tag = Cipher.decrypt(self.get_argument("label")).strip().split(',')
            fileName = Cipher.decrypt(self.get_argument("name")).strip()
            desc = Cipher.decrypt(self.get_argument("desc")).strip()
            isV4 = self.get_argument("isV4", "0")
            rid = self.get_argument("rid", "")
            reward = 0
            if rid:
                reward = 1
            result = {"result": "1"}
            try:
                uid = long(uid)
                main_type = int(main_type)
                sub_type = int(sub_type)
                res_grade = float(res_grade)
                if res_grade < 0:
                    res_grade = 5
                file_size = int(file_size)
                h = long(h)
                is_public = int(is_public)
                desc = escape(desc)
                fileName = escape(fileName)
                assert h > 0
                assert len(fileName) > 0
                assert uid > 0
                assert main_type >= 0
                assert sub_type >= 0
                assert file_size > 0
                assert len(self.get_argument("nick_name")) > 0
                assert len(desc) > 0
                assert res_grade >= 0 and res_grade <= 10
                assert is_public == 0 or is_public == 1
                assert len(tag) > 0
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            #print uid
            if uid:
                #print "start upload"
                ext_info = self.get_argument("ext_info", "")
                if ext_info:
                    ext_info = json.loads(ext_info)
                    if "img" in ext_info:
                        p_dir = os.path.join(os.getcwd(), "static", "images", "res_icon")
                        if not os.path.isdir(p_dir):
                            os.makedirs(p_dir)
                        p = os.path.join(p_dir, str(getUid(self)) + str(int(time())) + ".jpg")
                        try:
                            f = open(p, "wb")
                            data = ext_info["img"].decode('base64')
                            f.write(data)
                            f.close()
                            icon = self.static_url('images/res_icon/' + str(getUid(self)) + str(int(time())) + ".jpg")
                            ext_info["link"] = icon
                            del ext_info["img"]
                            #del ext_info["img"]
                            #print icon
                        except:
                            ext_info["link"] = ""
                        #add comment from douban
                        if "comments" in ext_info:
                            # for comment in ext_info["comments"]:
                            # comment=Cipher.decrypt(comment)
                            # yield ResourceStoreManager.add_comment(h,14156112684836,u"豆瓣",comment)
                            del ext_info["comments"]
                            #ext_info = json.dumps(ext_info)
                    yield ResourceStoreManager.user_upload_resource(reward, isV4, uid, self.get_argument("nick_name"),
                                                                    h, fileName, file_size, is_public, tag, main_type,
                                                                    sub_type, res_grade, desc,
                                                                    ext_info)
                else:
                    yield ResourceStoreManager.user_upload_resource(reward, isV4, uid, self.get_argument("nick_name"),
                                                                    h, fileName, file_size, is_public, tag, main_type,
                                                                    sub_type, res_grade, desc,
                                                                    None)
                #tell = {"type":4, "coin": FBCoinManager._coin_rules["uploaded_a_public_resource"]}
                #SocketHandler.send_to_one(self.current_user, json.dumps(tell))
                #print "finish upload"
                fileId = gen_file_id(h, file_size)
                link = ''
                description = ''
                if ext_info:
                    link = ext_info['link']
                    description = ext_info['summary']
                yield FeedManager.add_feed(fileId, fileName, uid, FeedManager.TYPE_UPLOAD, "", link, description)
                ext_info = None
                util.write(self, 1, "", result)
                self.finish()
                if rid:
                    yield Reward.user_upload_file(uid, fileId, rid)
                yield LogForUser.log_user_upload(uid, long(time()), fileId)
            else:
                util.write(self, 0, u"cookie 错误", {})
                self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    '''
    param:
    op(0 for search, 1 for get, 2 for update, 3 for del),del
    '''

    @gen.coroutine
    def delete(self):
        if self.get_argument("del", "") and self.get_argument("uid", ""):
            del_list = str(self.get_argument("del"))
            if del_list == "nul":
                util.write(self, 1, "", "delete success")
                self.finish()
                return
            size_list = self.get_argument("size", None)
            if size_list:
                size_list = map(int, str(size_list).split(","))
            dir_list = self.get_argument("isDir", None)
            if dir_list:
                dir_list = map(int, str(dir_list).split(","))
            del_list = del_list.split(",")
            uid = self.get_argument("uid")
            i = 0
            for file_hash in del_list:
                file_id = None
                try:
                    uid = long(uid)
                    file_hash = long(file_hash)
                    assert (uid >= 0)
                    assert (file_hash > 0)
                except:
                    util.errorHandle(self, 0)
                    self.finish()
                    return
                is_subfile = False
                if size_list:
                    if dir_list[i]:
                        is_subfile = True
                    file_id = gen_file_id(file_hash, size_list[i])
                    yield ResourceStoreManager.remove_owner(file_id, uid, is_subfile)
                else:
                    file_id = yield ResourceStoreManager.file_hash2file_id(file_hash)
                    yield ResourceStoreManager.remove_owner(file_id, uid, None)
                i += 1
                yield LogForUser.log_user_delete(uid, long(time()), file_id)
                util.RedisPub.publish(CHANNEL_RES_DEL, json.dumps({"file_id": file_id, "uid": uid, "is_subfile": is_subfile}))
            #tell = {"type":4, "coin": FBCoinManager._coin_rules["delete_an_uploaded_public_resource"]}
            #SocketHandler.send_to_one(SocketHandler.client_uid_user[uid], json.dumps(tell))
            util.write(self, 1, "", "delete success")
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @gen.coroutine
    def get_res_list(self):
        #user = self.get_argument("user", None)
        page = self.get_argument("page", 1)
        #print page
        sort_by = self.get_argument("sort_by", ResourceStoreManager.res_sort_by["download_num"])
        #print sort_by
        res_type = self.get_argument("res_type", ResourceInfo.get_main_index_by_type("电影"))
        tag = self.get_argument("tag", None)
        year = self.get_argument("year", None)
        country = self.get_argument("country", None)
        version = self.get_argument("version", "")
        #print res_type
        try:
            #user = long(user)
            page = int(page)
            assert page >= 0
            sort_by = int(sort_by)
            assert sort_by == ResourceStoreManager.res_sort_by["time"] or sort_by == ResourceStoreManager.res_sort_by[
                "download_num"] or sort_by == ResourceStoreManager.res_sort_by["online_num"]
            res_type = int(res_type)
            assert ResourceInfo.is_valid_main_type(res_type)
        except:
            util.errorHandle(self, 0)
            self.finish()
            raise gen.Return(None)
        key = "s" + str(sort_by) + "_r" + str(res_type) + "_p" + str(page)
        shouldCache = False
        if page <= 20:
            ret = None
            shouldCache = True
            if version >= "1.8":
                ret = util.MemCache.get(key, RES_MAIN_180)
            else:
                ret = util.MemCache.get(key, RES_MAIN_179)
            if ret:
                util.write_d(self, ret)
                self.finish()
                raise gen.Return(None)
        #print "no cache"
        #RES_CNT_IN_A_PAGE = 20
        msg = {}
        msg["type"] = 1
        msg["error"] = ""
        if sort_by == ResourceStoreManager.res_sort_by["online_num"]:
            resource_list = yield OnlineResources.get_online_resources_by_type(res_type, page, RES_CNT_IN_A_PAGE)
            if version >= "1.8":
                size = OnlineResources.get_online_resources_count(res_type)
                size = util.getPages(size)
                msg["result"] = {"size": size, "res": resource_list}
                ret = json.dumps(msg)
                if shouldCache:
                    util.MemCache.set(key, ret, RES_MAIN_180, util.Cache_Expire[sort_by])
                util.write(self, 1, "", {"size": size, "res": resource_list})
            else:
                msg["result"] = resource_list
                ret = json.dumps(msg)
                if shouldCache:
                    util.MemCache.set(key, ret, RES_MAIN_179, util.Cache_Expire[sort_by])
                util.write(self, 1, "", resource_list)
            self.finish()
            raise gen.Return(None)
        #print "get res start"
        resource_list = yield ResourceStoreManager.get_resources_overview(version, res_type, page, sort_by, RES_CNT_IN_A_PAGE)
        # TODO FIXME dengbo
        #resource_list = yield ResourceStoreManager.navigate_resources(version, res_type,page,sort_by,RES_CNT_IN_A_PAGE,tag,year,country)
        #print resource_list
        cipher_resource_list(resource_list, version)
        #print resource_list
        add_download_info_to_resource_list(resource_list)
        #print "get res finish"
        #print resource_list
        #resource_data = json.dumps({"err": 0, "resource_list": resource_list})
        if version >= "1.8":
            size = yield ResourceStoreManager.get_resources_count(res_type)
            size = util.getPages(size)
            msg["result"] = {"size": size, "res": resource_list}
            ret = json.dumps(msg)
            if shouldCache:
                util.MemCache.set(key, ret, RES_MAIN_180, util.Cache_Expire[sort_by])
            util.write(self, 1, "", {"size": size, "res": resource_list})
        else:
            msg["result"] = resource_list
            ret = json.dumps(msg)
            if shouldCache:
                util.MemCache.set(key, ret, RES_MAIN_179, util.Cache_Expire[sort_by])
            util.write(self, 1, "", resource_list)
        self.finish()

    @gen.coroutine
    def comment(self):
        if self.get_argument("fileHash", "") and self.get_argument("comment", "") and self.get_argument("nick_name",
                                                                                                        ""):
            file_hash = self.get_argument("fileHash")  #default is public
            comment = self.get_argument("comment").strip()  #default is public
            comment = Cipher.decrypt(comment)
            uid = getUid(self)
            user_name = self.get_argument("nick_name")
            file_size = self.get_argument("size", None)
            fileId = None
            try:
                uid = long(uid)
                file_hash = long(file_hash)
                if file_size:
                    fileId = gen_file_id(file_hash, file_size)
                else:
                    fileId = yield ResourceStoreManager.file_hash2file_id(file_hash)
                comment = escape(comment)
                assert uid >= 0
                assert len(user_name) > 0
                assert len(comment) > 0
                assert file_hash > 0
                assert fileId is not None
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            fileName = yield ResourceStoreManager.get_file_name(fileId)
            yield FeedManager.add_feed(fileId, fileName, uid, FeedManager.TYPE_COMMENT, "")
            info = yield util.getUserInfoById(uid)
            yield CommentManager.addComment(fileId, fileName, uid, info["nick_name"], info["icon"], comment)
            util.write(self, 1, "", {})
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()

    @gen.coroutine
    def score(self):
        if self.get_argument("fileHash", "") and self.get_argument("score", ""):
            file_hash = self.get_argument("fileHash", "")
            score = self.get_argument("score", "")
            file_size = self.get_argument("size", None)
            fileName = self.get_argument("rname", "")
            uid = getUid(self)
            file_id = None
            try:
                file_hash = long(file_hash)
                score = float(score)
                uid = long(uid)
                assert uid >= 0
                assert score >= 0 and score <= 10
                assert file_hash > 0
                if file_size:
                    file_id = gen_file_id(file_hash, file_size)
                else:
                    file_id = yield ResourceStoreManager.file_hash2file_id(file_hash)
                assert file_id is not None
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            if not fileName:
                fileName = yield ResourceStoreManager.get_file_name(file_id)
            yield ResourceStoreManager.add_score(file_id, uid, score)
            yield FeedManager.add_feed(file_id, fileName, uid, FeedManager.TYPE_GRADE, "")
            util.write(self, 1, "", {})
            self.finish()
        else:
            util.errorHandle(self, 0)
            self.finish()


class ResourceDownloadHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        #user is uid
        if self.get_argument("user", "") and self.get_argument("file_hash", ""):
            uid = self.get_argument("user", "")
            file_hash = self.get_argument("file_hash")  #default is public
            is_private = self.get_argument("private", 0)
            file_size = self.get_argument("size", 0)
            allowV4Download = self.get_argument("allowV4Download", "0")
            if allowV4Download == "0":
                allowV4Download = False
            else:
                allowV4Download = True
            dirHash = self.get_argument("dirHash", "")
            dirSize = self.get_argument("dirSize", "")
            if dirHash and long(dirHash) == 0:
                dirHash = ""
                dirSize = ""
            #print "uid" + str(uid)
            #print "file_hash" + str(file_hash)
            #print "is_private" + str(is_private)
            fileId = None
            dirId = None
            try:
                file_hash = long(file_hash)
                uid = long(uid)
                is_private = int(is_private)
                if file_size:
                    file_size = long(file_size)
                    fileId = gen_file_id(file_hash, file_size)
                else:
                    file_size = yield ResourceStoreManager.get_file_size(file_hash)
                    fileId = gen_file_id(file_hash, file_size)
                    #fileId = yield ResourceStoreManager.file_hash2file_id(file_hash)
                if dirHash:
                    dirId = gen_file_id(dirHash, dirSize)
                assert file_hash > 0
                assert fileId is not None
                assert uid > 0
                assert file_size is not None
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            yield LogForUser.log_user_download(uid, long(time()), fileId)
            if not is_private:  #public download need fb coin
                user_fb_coins = yield FBCoinManager.get_user_total_fb_coin(uid)
                if user_fb_coins < FBCoinManager.public_resource_download_coin(file_size):
                    ok = json.dumps({"type": 0, "error": "no fb coin"})
                    self.write(ok)
                    self.finish()
                    return
                yield FBCoinManager.add_to_public_download_queue(uid, fileId, dirId)
            version = self.get_argument("version", "1.8")
            res_header = None
            if version < "1.9":
                res_header = yield ResourceStoreManager.get_resource_header(fileId, dirId)
                if "isDir" in res_header and res_header["isDir"]:
                    SocketHandler.send_to_one(uid, json.dumps(
                        {"type": 7, "sticky": 1, "msg": 0, "content": u"您目前的版本不支持文件夹下载，请到官网下载最新版客户端。"}))
                    util.errorHandle(self, 0)
                    self.finish()
                    return
            else:
                res_header = ""
            online_owners = DownloadMedium.get_online_file_owner(uid, fileId, allowV4Download,dirId)
            #print "online_owners:"+str(online_owners)
            download_type = online_owners["download_type"]
            #print "download_type:"+str(download_type)
            if download_type == DownloadMedium.download_type["V4_NAT"]:
                #print "notify_open_file_server"
                nat_users = [owner["uid"] for owner in online_owners["owners"]]
                if len(nat_users) > 0:
                    # TODO FIXME file_hash change to file_id
                    SocketHandler.notify_open_file_server(nat_users, uid, file_hash, file_size)
            elif version < "1.9" and download_type == DownloadMedium.download_type["V4_NOT_ALLOW"]:
                SocketHandler.send_to_one(uid, json.dumps(
                        {"type": 7, "sticky": 1, "msg": 0, "content": u"该资源下载需要到设置里启用V4下载，请到官网下载最新版客户端。"}))
                util.errorHandle(self, 0)
                self.finish()
                return
            ok = json.dumps(
                {"type": 1, "file_info": res_header, "owners": online_owners["owners"], "download_type": download_type})
            self.write(ok)
            self.finish()
        else:
            #print "params error"
            util.errorHandle(self, 0)
            self.finish()


class ResourceDownloadOverHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        dirHash = self.get_argument("dirHash", "")
        dirSize = self.get_argument("dirSize", "")
        rid = self.get_argument("rid", "")
        if self.get_argument("user", "") and self.get_argument("file_hash", ""):
            uid = self.get_argument("user", None)
            file_hash = self.get_argument("file_hash", None)  #default is public
            users_from = self.get_argument("downloadFrom", None)
            file_name = self.get_argument("file_name", None)
            file_size = self.get_argument("file_size", None)
            file_id = None
            dirId = None
            is_subfile = False
            try:
                users_downloaded_from = []
                for u in users_from.split(','):
                    if u:
                        users_downloaded_from.append(long(u))
                file_hash = long(file_hash)
                uid = long(uid)
                assert len(users_downloaded_from) > 0
                for u in users_downloaded_from:
                    assert u > 0
                assert (uid >= 0)
                assert (file_hash > 0)
                if file_size:
                    file_id = gen_file_id(file_hash, file_size)
                else:
                    file_id = yield ResourceStoreManager.file_hash2file_id(file_hash)
                if dirHash:
                    dirId = gen_file_id(dirHash, dirSize)
                    is_subfile = True
            except:
                util.errorHandle(self, 0)
                self.finish()
                return
            owners_cnt = yield ResourceStoreManager.add_owner_when_download_over(file_id, uid, dirId)
            download_num = yield ResourceStoreManager.increase_download_num(file_id, dirId)
            yield FBCoinManager.public_resource_download_ok(uid, file_id, users_downloaded_from, download_num, owners_cnt, dirId)
            ok = json.dumps({"type": 1})
            self.write(ok)
            self.finish()
            if rid:
                yield Reward.user_download_file_over(users_downloaded_from, file_id, rid)
                yield ResourceStoreManager.resource_tobeaudit(file_id)
            #{"file_id": file_id, "file_name": file_name, "uid": uid}
            if not file_name:
                file_name = yield ResourceStoreManager.get_file_name(file_id)
            util.RedisPub.publish(CHANNEL_RES_UPLOAD,
                                  json.dumps({"file_id": file_id, "file_name": file_name, "uid": uid, "is_subfile": is_subfile}))
            yield LogForUser.log_user_download_over(uid, file_id)
            if dirId:
                yield FeedManager.add_feed(dirId, file_name, uid, FeedManager.TYPE_DOWNLOAD, "")
            else:
                yield FeedManager.add_feed(file_id, file_name, uid, FeedManager.TYPE_DOWNLOAD, "")
        else:
            util.errorHandle(self, 0)
            self.finish()


class ResourceDownloadViewHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        """ by file hashes"""
        #user = getUid(self)
        #if not user:
        #    user = self.get_argument("user", "")
        version = self.get_argument("version", "")
        hashes = self.get_argument("file_hashes", "")
        sizes = self.get_argument("file_sizes", "")
        count = self.get_argument("count", "")
        file_hash_list = None
        file_size_list = None
        try:
            count = int(count)
            if count == 0:
                util.write(self, 1, "", [])
                self.finish()
                return
            #user = long(user)
            file_hash_list = [long(file_hash) for file_hash in hashes.split(",")]
            if sizes:
                file_size_list = [long(file_size) for file_size in sizes.split(",")]
            assert len(file_hash_list) > 0
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        resource_list = yield ResourceStoreManager.get_resources_by_file_ids(version, file_hash_list, file_size_list)
        cipher_resource_list(resource_list, version)
        add_download_info_to_resource_list(resource_list)
        util.write(self, 1, "", resource_list)
        self.finish()

    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        """ by file hashes"""
        #user = getUid(self)
        #if not user:
        #    user = self.get_argument("user", "")
        version = self.get_argument("version", "")
        hashes = self.get_argument("file_hashes", "")
        sizes = self.get_argument("file_sizes", "")
        count = self.get_argument("count", "")
        file_hash_list = None
        file_size_list = None
        try:
            count = int(count)
            if count == 0:
                util.write(self, 1, "", [])
                self.finish()
                return
            #user = long(user)
            file_hash_list = [long(file_hash) for file_hash in hashes.split(",")]
            if sizes:
                file_size_list = [long(file_size) for file_size in sizes.split(",")]
            assert len(file_hash_list) > 0
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        resource_list = yield ResourceStoreManager.get_resources_by_file_ids(version, file_hash_list, file_size_list)
        cipher_resource_list(resource_list, version)
        add_download_info_to_resource_list(resource_list)
        util.write(self, 1, "", resource_list)
        self.finish()


class UserResourceViewHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        #user is uid
        friend_uid = self.get_argument("friend", None)
        page = self.get_argument("page", 1)
        sort_by = self.get_argument("sort_by", ResourceStoreManager.res_sort_by["download_num"])
        version = self.get_argument('version', '1.8')
        #user = self.get_argument("uid", "")
        #print user
        try:
            friend_uid = long(friend_uid)
            assert friend_uid > 0
            #uid = long(user)
            #assert uid > 0
            page = int(page)
            assert page >= 0
            sort_by = int(sort_by)
            assert sort_by == ResourceStoreManager.res_sort_by["time"] or sort_by == ResourceStoreManager.res_sort_by[
                "download_num"]
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        #RES_CNT_IN_A_PAGE = 20  #maybe this should be large
        resource_list = yield ResourceStoreManager.get_my_resource(version, friend_uid, page, sort_by, RES_CNT_IN_A_PAGE)
        cipher_resource_list(resource_list, version)
        add_download_info_to_resource_list(resource_list)
        if version >= "1.8":
            size = yield ResourceStoreManager.get_one_resources_count(friend_uid)
            size = util.getPages(size)
            util.write(self, 1, "", {"size": size, "res": resource_list})
        else:
            util.write(self, 1, "", resource_list)
        self.finish()


class Resource404Handler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        user = self.get_argument("user", None)  # mock user since node client has no cookie
        try:
            uid = long(user)
            file_id = self.get_argument("file_id", "")
            assert len(file_id) > 0
        except:
            err = json.dumps({"err": 1, "what": "uid or file_id invalid"})
            self.write(err)
            self.finish()
            return
        yield ResourceStoreManager.remove_owner(file_id, uid)
        ok = json.dumps({"err": 0})
        self.write(ok)
        self.finish()


class NavInfoHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        # TODO FIXME dengbo, maybe should make some changes
        user = self.get_argument("user", None)  # mock user since node client has no cookie
        try:
            uid = long(user)
        except:
            err = json.dumps({"err": 1, "what": "uid invalid"})
            self.write(err)
            self.finish()
            return
        nav_info = yield ResourceStoreManager.get_nav_info()
        ok = json.dumps({"err": 0, "nav_info": nav_info})
        self.write(ok)
        self.finish()


class TipOffResourceHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        user = getUid(self)
        if not user:
            user = self.get_argument("uid", "")
        file_hash = self.get_argument("file_hash", None)  #default is public
        file_size = self.get_argument("file_size", None)
        file_id = None
        try:
            uid = long(user)
            file_hash = long(file_hash)
            assert file_hash > 0
            assert uid > 0
            if file_size:
                file_id = gen_file_id(file_hash, file_size)
            else:
                file_id = yield ResourceStoreManager.file_hash2file_id(file_hash)
            assert file_id is not None
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        yield ResourceStoreManager.tip_off(file_id, uid)
        ok = json.dumps({"type": 1})
        self.write(ok)
        self.finish()


class SocketHandler():
    @classmethod
    def notify_open_file_server(cls, user_ids, for_who, file_hash, file_size):
        assert len(user_ids) > 0
        assert file_hash > 0
        assert for_who >= 0
        OPEN_UDP_SERVER = 1
        for uid in user_ids:
            uid = str(uid)
            # client_uid_user = util.RedisHandle.f_hgetall(CLIENT_UID_USER)
            # if not client_uid_user:
            #     return
            #if uid in SocketHandler.client_uid_user:
            all_token = util.MemCache.get(None, LOGIN_T)
            #if self.current_user in SocketHandler.client_user:
            if str(uid) in all_token:
                try:
                    #user = client_uid_user[uid]
                    msg = {"type": 0, "message_type": OPEN_UDP_SERVER, "file_hash": file_hash,
                           "what": "open udp server", "for": for_who,"file_size": file_size}
                    send = json.dumps({"type": 0, "msg": msg, "uid": uid, "user": ""})
                    util.RedisPub.publish(CHANNEL_INFORM, send)
                    #util.HttpClient.get(MSG_URL+MSG_PORT[int(t)]+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user)
                except:
                    logging.info("Warning: writing open udp server message failed. the user has left." + str(uid))

    @staticmethod
    def send_to_all_s(message):
        #this is for the system information
        send = json.dumps({"type": 3, "msg": message, "uid": "", "user": ""})
        util.RedisPub.publish(CHANNEL_INFORM, send)
        #util.HttpClient.get(MSG_URL+MSG_URL_AUTH+str(MSG_SEND_ALL)+"&msg="+message) 

    @staticmethod
    def send_to_all_r(uid, message):
        #this is for the system information
        #util.HttpClient.get(MSG_URL+MSG_URL_AUTH+str(MSG_SEND_ALL_R)+"&msg="+message+"&user="+user)
        send = json.dumps({"type": 2, "msg": message, "uid": uid, "user": ""})
        util.RedisPub.publish(CHANNEL_INFORM, send)

    @classmethod
    def update_fb(cls, uid, fb):
        print "you shouldn't invoke me(update fb)"
        tell = {"add": 0, "type": 4, "coin": fb}
        uid = str(uid)
        send = json.dumps({"type": 0, "msg": tell, "uid": uid, "user": ""})
        util.RedisPub.publish(CHANNEL_INFORM, send)
        # client_uid_user = util.RedisHandle.f_hgetall(CLIENT_UID_USER)
        # if not client_uid_user:
        #     return
        # if uid in client_uid_user:
        #     user = client_uid_user[uid]
        #     util.HttpClient.get(MSG_URL+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user)

    @staticmethod
    def send_to_one(uid, msg, user=""):
        #print msg
        # try:
        #     util.HttpClient.get(MSG_URL+MSG_URL_AUTH+str(MSG_SEND_ONE)+"&msg="+msg+"&user="+user)
        # except Exception, e:
        #     logging.info(e)
        send = json.dumps({"type": 0, "msg": msg, "uid": uid, "user": user})
        util.RedisPub.publish(CHANNEL_INFORM, send)


def getUid(s):
    return util.g_cookie(s, "fbt_user_id")


def getNickName(s):
    return util.g_cookie(s, "fbt_nick_name")

class FriendsResourceViewHandler(BaseHandler):
    @tokenCheck
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        page = self.get_argument("page", 1)
        user = getUid(self)
        version = self.get_argument("version", "")
        sort = self.get_argument("sort", None)
        which_type = self.get_argument("type", None)
        #print page
        #print user
        if not user:
            user = self.get_argument("user", None)
        try:
            user = long(user)
            page = int(page)
            if which_type:
                which_type = int(which_type)
                assert which_type >= 0 and which_type <= 9
            if sort is not None:
                sort = int(sort)
            sort = ResourceStoreManager.get_sort_item(sort)
            assert page >= 1
            assert user >= 0
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        '''
        RES_CNT_IN_A_PAGE = 20
        friends_list = yield UserManager.get_friend_list(user)
        resource_list = yield ResourceStoreManager.get_private_resources(version, friends_list, page, RES_CNT_IN_A_PAGE)
        '''

        if which_type is not None:
            size, resource_list = yield FileNameSearcher().get_private_resources_by_type(user, which_type, page, RES_CNT_IN_A_PAGE, sort)
        else:
            size, resource_list = yield FileNameSearcher().get_private_resources(user, page, RES_CNT_IN_A_PAGE, sort)
        resource_list = [ResourceStoreManager.extract_resource_from_db(_, version, True) for _ in resource_list]
        cipher_resource_list(resource_list, version)
        add_download_info_to_resource_list(resource_list)
        #print resource_list
        if version >= "1.8":
            # friends_list = yield util.getFriendsById(user)
            # friend_uid_list = []
            # for item in friends_list:
            #     friend_uid_list.append(item["uid"])
            #size = yield ResourceStoreManager.get_one_friend_resources_count(friend_uid_list)
            #util.write(self, 1, "", {"size": util.getPages(size), "res": resource_list})
            util.write(self, 1, "", {"size": util.getPages(size), "res": resource_list})
        else:
            util.write(self, 1, "", resource_list)
        self.finish()


def db_error_handle(user, error):
    util.log("error")
    pass


# t = 0
# def sayhello():
#     #print "hello world"
#     out_token = open("login_token.json","w")
#     out_token.write(json.dumps(login_token))
#     out_token.close()
#     out_user = open("login_user.json","w")
#     out_user.write(json.dumps(login_user))
#     out_user.close()
#     out_user = open("upload_uid.json","w")
#     out_user.write(json.dumps(upload_uid))
#     out_user.close()
#     global t        #Notice: use global variable!
#     t = threading.Timer(1800.0, sayhello)
#     t.start()
def save_cache_to_file(ioloop, later):
    p = str(options.port)
    util.MemCache.save(p)
    UserIPCache.save(p)
    HttpServerInfoCache.save(p)
    ioloop.add_timeout(long(time()) + later, lambda: save_cache_to_file(ioloop, later))


def load_cache_from_file():
    p = str(options.port)
    util.MemCache.load(p)
    UserIPCache.load(p)
    HttpServerInfoCache.load(p)

#init sub
sub_user_on_off = util.RedisSub(CHANNEL_ON_OFF, user_off)
sub_server_info = util.RedisSub(CHANNEL_SERVER_INFO, server_info)


def main():
    global db
    global log_db
    global db_realtime
    access = logging.getLogger("tornado.access")
    access.addHandler(NullHandler())
    access.propagate = False
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    later = 3600
    try:
        load_cache_from_file()
        ioloop = tornado.ioloop.IOLoop.instance()
        # db_client = motor.MotorReplicaSetClient(hosts_or_uri="127.0.0.1:27017",replicaSet='fbt_repl',io_loop=ioloop)
        # db_client.read_preference = ReadPreference.SECONDARY_ONLY
        # db = db_client.fbt
        db_realtime = motorclient.fbt_realtime
        db = motorclient.fbt
        log_db = motorclient.fbt_log
        fbt_reward = motorclient.reward
        Reward.set_db(fbt_reward, db)
        #log_db = db_client.fbt_log
        ResourceStoreManager.set_db(db)
        CommentManager.set_db(db, db_realtime)
        FeedManager.set_db(db, db_realtime)
        FBCoinManager.set_db(db)
        UserManager.set_db(db)
        msg_handle.set_db(db)
        OnlineResources.init(db)
        LogForUser.set_db(log_db)
        #FBCoinManager.set_update_fb_callback(SocketHandler.update_fb)

        ioloop.add_timeout(long(time()) + later, lambda: save_cache_to_file(ioloop, later))

        ioloop.start()
    except Exception, e:
        print e
        print "OK. I will exit..."
    finally:
        save_cache_to_file(tornado.ioloop.IOLoop.instance(), later)
        sub_user_on_off.close()
        sub_server_info.close()


class NullHandler(logging.Handler):
    def __init__(self, level=logging.ERROR):
        logging.Handler.__init__(self, level)

    def emit(self, record):
        pass


if __name__ == "__main__":
    main()
