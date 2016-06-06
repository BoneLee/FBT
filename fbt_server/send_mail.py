# -*- coding: utf-8 -*-
import smtplib
import uuid 
import random
import hashlib
import os
from time import time
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart
import codecs
import mongoclient

def send_intro_mail(to_list):
    me="fbt_service@friendsbt.com"
    if os.path.isfile("introMail"):
        content = ''.join(codecs.open('introMail',"r",'utf-8').readlines())
        #msg = MIMEText(content,_subtype='plain',_charset='utf-8') 
        msg = MIMEMultipart('alternative') 
        msg['Subject'] = "[FBT]FBT 1.9.0全心发布"  
        msg['From'] = me  
        msg['To'] = to_list #";".join(to_list)
        part2 = MIMEText(content, 'html',_charset='utf-8')
        msg.attach(part2)
        try:
            server = smtplib.SMTP("localhost")  
            server.sendmail(me, to_list, msg.as_string())  
            server.quit()    
        except Exception, e:  
            print e   
    else:
        print "intro email not exist"

if __name__ == "__main__":
    db = mongoclient.fbt
    all_users = db.users.find({}, {"user":1})
    for item in all_users:
        send_intro_mail(item["user"])