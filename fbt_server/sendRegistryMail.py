# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart
from tornado import gen
from pymongo import DESCENDING

class sendRegistryMail(object):
    _db = None

    @classmethod
    def set_db(cls, db):
        cls._db = db

    @classmethod
    def send_registry_mail(cls, to_list,nick,token):  
        me="fbt_service@friendsbt.com"
        content = u'<html><head><title>FBT注册</title></head><body><h2>Hi, <span style="color:#1abc9c">'+nick
        content += u'</span></h2><p>&nbsp;&nbsp;&nbsp;&nbsp;您好！您的FBT账号已经创建成功，请验证您的邮箱：<a href="'
        content += u'http://www.friendsbt.com:8888/registry_confirm?key='+token+'&user='+to_list
        content += u'">点击验证邮箱</a></p><p>&nbsp;&nbsp;&nbsp;&nbsp;FBT采用P2P技术，在线人数越多，资源下载越高速流畅。多下载热门资源并保持较长时间在线'
        content += u'，有助于您迅速赚F币；自己上传的资源，在审核通过后尽量保持在线，以便他人可以成功下载，给您F币奖励。FBT服务器不保存用户上传资源，只保存资源索引信息</p></body></html>'  
        msg = MIMEMultipart('alternative') 
        msg['Subject'] = "[FBT]Welcome to FBT, Email Validation"  
        msg['From'] = me  
        msg['To'] = to_list #";".join(to_list)
        part2 = MIMEText(content, 'html',_charset='utf-8')
        msg.attach(part2)
        try:  
            server = smtplib.SMTP("localhost")  
            server.sendmail(me, to_list, msg.as_string())  
            server.quit()
            return True    
        except Exception, e:  
            print e
            return False
    @classmethod
    def send_reset_mail(cls,to_list,nick,token):  
        me="fbt_service@friendsbt.com"
        content = u'<html><head><title>FBT注册</title></head><body><h2>Hi, <span style="color:#1abc9c">'+nick
        content += u'</span></h2><p>&nbsp;&nbsp;你好！FBT已经收到了你的密码重置请求，请在24小时内点击下面的链接重置密码。</p><a href="'
        content += u'http://www.friendsbt.com:8888/reset_password?key='+token
        content += u'">点击重置密码</a><p>如果你没有请求密码重置，请忽略该邮件。</p></body></html>'  
        msg = MIMEMultipart('alternative') 
        msg['Subject'] = "[FBT]Password Reset E-mail"  
        msg['From'] = me  
        msg['To'] = to_list #";".join(to_list)
        part2 = MIMEText(content, 'html',_charset='utf-8')
        msg.attach(part2)
        try:  
            server = smtplib.SMTP("localhost")  
            server.sendmail(me, to_list, msg.as_string())  
            server.quit() 
            return True   
        except Exception, e:  
            print e
            return False

    @classmethod
    @gen.coroutine
    def sendmail(cls, user):
        u = yield cls._db.tmp_users.find_one({"user":user}, {"nick_name":1, "token":1})
        if u and "nick_name" in u:
            cls.send_registry_mail(user, u["nick_name"], u["token"])

    @classmethod
    @gen.coroutine
    def send_resetmail(cls, user):
        u = yield cls._db.users.find_one({"user":user}, {"nick_name":1})
        if u:
            nick_name = u["nick_name"]
            cursor = cls._db.password.find({"user":user}, {"token":1}).limit(1).sort("time", DESCENDING)
            while (yield cursor.fetch_next):
                item = cursor.next_object()
                token = item["token"]
                tmp = token[:5]+"_"+token[5:]
                cls.send_reset_mail(user,nick_name,tmp)
                break



