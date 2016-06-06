#-*- coding:utf-8 -*-

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

import pprint
import uuid
from datetime import datetime

import msg_handle


pp = pprint.PrettyPrinter(indent=4)

def main():
    pp.pprint(msg_handle.getAllMsg('z695129822@qq.com'))
    
    print msg_handle.isMsgExist('z695129822@qq.com', 'xjw0423@foxmail.com')

    msg = {}
    msg["type"] = 0
    uid = msg["id"] = str(uuid.uuid1().int)
    msg["sender"] = "0"
    msg["nick"] = "0"
    msg["content"] = u"test"
    msg["time"] = datetime.now().strftime('%Y-%m-%d %H:%M')

    msg_handle.addMsg('z695129822@qq.com', msg, "", "", "")
    
    msg_handle.ReadMsg('z695129822@qq.com', uid)
    pp.pprint(msg_handle.getAllMsg('z695129822@qq.com'))

    msg_handle.ReadAllMsg('z695129822@qq.com')
    pp.pprint(msg_handle.getAllMsg('z695129822@qq.com'))

    pp.pprint(msg_handle.getAllShuo('test@test.com'))
    msg_handle.addShuo('test@test.com', 'test', "", "", "")
    msg_handle.addShuo('test@test.com', 'test2', "", "", "")
    pp.pprint(msg_handle.getAllShuo('test@test.com'))

    msg_handle.delShuo('test@test.com', '318624798772209059310732276757981078828', "", "", "")
    pp.pprint(msg_handle.getAllShuo('test@test.com'))

if __name__ == "__main__":
    main()