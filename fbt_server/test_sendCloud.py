# -*- coding:utf-8 -*-                                                          

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate, formataddr
from email import encoders

import base64, time, os, json
from datetime import datetime, date

HOST = 'smtpcloud.sohu.com'
PORT = 25
API_USER = 'friendsbt'
API_KEY = 'AAV36hVJiwO8A7Fx'

def send(mail_from, ffrom, rcpt_to, subject, content):                                                                  
    ret = {}

    s = SMTP('%s:%d' % (HOST, PORT))
    s.login(API_USER, API_KEY)

    msg = MIMEMultipart('alternative')
    msg['subject'] = subject
    msg['from'] = ffrom
    msg['to'] = rcpt_to

    part = MIMEText(content, 'html', 'utf8')
    msg.attach(part)

    s.mail(mail_from)
    s.rcpt(rcpt_to)
    print s.data(msg.as_string())
    s.rset()
    s.quit()

def main():
    # send email one by one
    send("fbt@mail.friendsbt.com", "fbt_service", "459545754@qq.com", "test", "adfjhk很快就好")

if __name__ == '__main__':                                                      
    main()