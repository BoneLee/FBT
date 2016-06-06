# coding: utf-8
import os
from constant import DEBUG_ENV

if DEBUG_ENV:
    # 使用内网地址
    mongo_machines = [
        "10.10.70.32:27017",
        "10.10.77.42:27017",
        "10.10.67.179:27017",
    ]
    REPLICASET_NAME = 'udb-d1vxxu'
else:
    # 使用内网地址
    mongo_machines = [
        "10.10.89.13:27017",
        "10.10.82.231:27017",
        "10.10.84.250:27017",
    ]
    REPLICASET_NAME = 'udb-w2a3cy'

FBT_USER = "fbt"
FBT_PASSWD = "welcome2fbtFBT"

PROJ_HOME = os.path.dirname(os.path.abspath(__file__))
COURSE_FILE = os.path.join(PROJ_HOME, 'static/json/course.json')
COURSE_FILE_BAK = os.path.join(PROJ_HOME, 'static/json/course.json.bak')
