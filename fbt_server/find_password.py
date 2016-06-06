# -*- coding: UTF-8 -*-
from users_manager import UserManager
import smtplib
import uuid  
import random
import hashlib 
import os
from time import time
from tornado import gen
from mail_utils import template_send, common_send
#from email.mime.text import MIMEText  
#from email.mime.multipart import MIMEMultipart
import codecs
import motorclient
from constant import OUR_WEB_URL

from concurrent.futures import ThreadPoolExecutor
# mail_host="smtp.exmail.qq.com"  #设置服务器
# mail_user="fbt_reset_password@friendsbt.com"    #用户名
# mail_user1="fbt_reset_password1@friendsbt.com"
# mail_user_s="fbt_service@friendsbt.com"    #用户名
# mail_user_s1="fbt_service1@friendsbt.com"    #用户名
# mail_user_s2="fbt_service2@friendsbt.com"    #用户名
# mail_user_r="fbt_registration@friendsbt.com"
# mail_user_r1="fbt_registration1@friendsbt.com"
# mail_user_r2="fbt_registration2@friendsbt.com"
# mail_pass="welcome2fbt"   #口令
# mail_postfix="friendsbt.com"  #发件箱的后缀
db = motorclient.fbt
dbRealTime = motorclient.fbt_realtime

executor = ThreadPoolExecutor(max_workers=20)
 
def send_invitation_mail_helper(to_list, from_nick, to_nick, content, url):
    me="fbt_service@mail.friendsbt.com"
    sub_vars = {
       'to': [to_list],
       'sub': {
           '%from_nick%': [from_nick],
           '%to_nick%': [to_nick],
           '%content%': [content],
           '%url%': [url]
       }
    }
    template_send(me,"fbt_service","invitation_answer",sub_vars)

#@to_list the mail addr will recieve this mail
#@from_nick who post this invitation
#@to_nick who get this invitation
#@content the content of the question
#@url the link of the question(you should give the "http://xxx")
def send_invitation_mail(to_list, from_nick, to_nick, content, url):
    future = executor.submit(send_invitation_mail_helper, to_list, from_nick, to_nick, content, url)
    # future.add_done_callback(callback)
    # return future.result()
    return True

def send_bind_mail_helper(to_list, nick, url):
    me="fbt_service@mail.friendsbt.com"
    sub_vars = {
       'to': [to_list],
       'sub': {
           '%user_nick%': [nick],
           '%user_email%': [to_list],
           '%user_url%': [url]
       }
    }
    template_send(me,"fbt_service","bind_email",sub_vars)

def send_bind_mail(user, nick, url):
    future = executor.submit(send_bind_mail_helper, user, nick, url)
    # future.add_done_callback(callback)
    # return future.result()
    return True

#@to_list the mail addr will recieve this mail
#@nick user's nick_name
#@token token about user 
def send_reset_mail_helper(to_list,nick,token, port=8888):
    me="fbt_service@mail.friendsbt.com"
    if port == 8888:
        url = 'http://www.friendsbt.com:8888/do_reset_password?key='+token
        who = 'FBT'
    else:
        url = OUR_WEB_URL + '/do_reset_password?key=' + token
        who = u'校园星空'
    sub_vars = {
       'to': [to_list],
       'sub': {
           '%nick%': [nick],
           '%who%': [who],
           '%url%': [url]
       }
    }
    template_send(me,"fbt_service","reset_pwd",sub_vars)

def send_reset_mail(to_list,nick,token, port=8888):
    future = executor.submit(send_reset_mail_helper, to_list, nick, token, port)
    # future.add_done_callback(callback)
    # return future.result()
    return True

def send_registry_mail_helper(to_list,nick,token):
    me="fbt_service@mail.friendsbt.com"
    sub_vars = {
       'to': [to_list],
       'sub': {
           '%nick%': [nick],
           '%token%': [token],
           '%to_list%': [to_list]
       }
    }
    template_send(me,"fbt_service","registry",sub_vars)

def send_registry_mail(to_list,nick, token):
    future = executor.submit(send_registry_mail_helper, to_list, nick, token)
    return True

#@to_list [] the list will recieve this mail
def send_intro_mail_helper(to_list):
    me="fbt_service@mail.friendsbt.com"
    sub_vars = {
       'to': [to_list]
    }
    template_send(me,"fbt_service","introduction",sub_vars)

def send_intro_mail(to_list):
    future = executor.submit(send_intro_mail_helper, to_list)
    return True

@gen.coroutine
def reset(user, port=8888):
    cursor = yield dbRealTime.users.find_one({"user":user}, {"_id": 0})
    if cursor:
        token = str(uuid.uuid1().int)
        random.seed(token)
        r = random.randint(1, len(token)-1)
        tmp = token[:r]+"_"+token[r:]
        md5 = hashlib.md5()
        md5.update(user)
        m = md5.hexdigest()
        item = {"token":token, "user":user, "p_user":m, "time":long(time())}
        yield db.password.insert(item)
        #to_list = [user]
        ret = send_reset_mail(user, cursor["nick_name"], tmp, port)
        raise gen.Return(ret)
    else:
        raise gen.Return(False)

# It is ugly. Because this is not OOP.
user_manager = UserManager()

@gen.coroutine
def confirm_reset(token, user, pwd):
    token = token.replace('_','')
    cursor = yield db.password.find_one({"token":token, "p_user":user}, {"_id": 0})
    if cursor:
        old_time = cursor["time"]
        cur_time = long(time())
        if cur_time - old_time > 24*60*60:
            raise gen.Return(False)
        o_user = cursor["user"]
        random.seed(hash(o_user))
        r = random.randint(1, 10000)
        if r == 10000:
            r = 9999
        elif r < 10:
            r = "000" + str(r)
        elif r < 100:
            r = "00" + str(r)
        elif r < 1000:
            r = "0" + str(r)
        salted_passwd = pwd+str(r)
        result = yield dbRealTime.users.update({'user': o_user}, {'$set':{"password":salted_passwd}})
        user_manager.update_password_of_user_cache(o_user, salted_passwd)
        yield db.password.remove({"token":token, "p_user":user})
        if ("nModified" in result and result["nModified"] == 1) \
            or ("updatedExisting" in result and result["updatedExisting"] == True) \
            or ("ok" in result and result["ok"] == 1):
            if not ("writeConcernError" in result):
                raise gen.Return(True)
            else:
                raise gen.Return(False)
        else:
            raise gen.Return(False)
    else:
        raise gen.Return(False)
