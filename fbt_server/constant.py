#-*- coding:utf-8 -*-

DEBUG_ENV = True

CDN_URL = "//test.friendsbt.com/"

RES_CNT_IN_A_PAGE = 20
REWARD_CNT_IN_A_PAGE = 10
NICKINFO = "nickinfo"
FRIENDINFO = "friendinfo"
USERINFO = "userinfo"
UID2ICON = "uid2icon"
GENDERKEY = "genderkey"
SCHOOLKEY = "schoolkey"
WEEKLY_TOP = "weekly_top"
MONTHLY_TOP = "monthly_top"
TOTAL_RANK = "total_rank"
RES_MAIN_180 = "res_main_180"
RES_MAIN_179 = "res_main_179"
LOGIN_U = "login_user"
LOGIN_T = "login_token"
CLIENT_SOCKET = "client_socket"
CLIENT_USER = "client_user"
CLIENT_UID_USER = "client_uid_user"
CLIENT_USER_UID = "client_user_uid"
CLIENT_USER_HEART = "client_user_heart"
CLIENT_USER_TORNADO = "client_user_tornado"
USER_ONLINE_AT = "user_online_at"
USER_IP_LIST = "user_ip_list"

USER_IP_CACHE_HASH_KEY = "user_ip_cache_hash_key"
USER_IP_CACHE_SET_KEY = "user_ip_cache_set_key"

HTTP_SERVER_INFO = "http_server_info"
MSG_PORT = ["8000", "8001", "8002", "8003"]
MSG_URL = "http://211.149.223.98:8004"
MSG_URL_AUTH = "/redirect_socket?auth_user=fbt2socket&auth_pwd=fbt2socket&msg_type="
MSG_AUTH = "fbt2socket"
MSG_SOCKET_CLOSE = 0
MSG_SEND_ONE = 1
MSG_SEND_ALL = 2
MSG_SEND_ALL_R = 3
CHANNEL_INFORM = "fbt:user:infrom"
CHANNEL_LOGIN = "fbt:user:login"
CHANNEL_ON_OFF = "fbt:user:on-off-line"
CHANNEL_COIN_VARY = "fbt:coin:vary"
CHANNEL_STUDY_COIN_VARY = "fbt:study-coin:vary"
CHANNEL_RES_UPLOAD = "fbt:resource:upload"
CHANNEL_RES_DEL = "fbt:resource:delete"
CHANNEL_RES_CLEAR = "fbt:resource:clear"
CHANNEL_RES_PASS = "fbt:resource:pass-audit"
CHANNEL_RES_HIDDEN = "fbt:resource:hidden"
CHANNEL_RES_REVEALED = "fbt:resource:revealed"
CHANNEL_SERVER_INFO = "fbt:server:ip_info"
CACHE_RESOURCE_ONLINE_NUM = 'resource_online_num'
CACHE_ONLINE_RESOURCE = 'online_resource'
CACHE_ONLINE_USER = 'online_user'
CACHE_RESOURCE_OF_USER = 'resource_of_user'
CACHE_OWNER_OF_RESOURCE = 'online-users:'
CACHE_OWNER_CNT_OF_RESOURCE = 'online-users-cnt:'
SEARCH_RPC_SERVER_PORT = 8893

FB_WEEKLY_CACHE = "fb:cache:weekly2"
FB_MONTHLY_CACHE = "fb:cache:monthly2"
STUDY_FB_WEEKLY_CACHE = "study-fb:cache:weekly2"
STUDY_FB_MONTHLY_CACHE = "study-fb:cache:monthly2"

USER_RES_CACHE_KEY = "user-res-cache-key:"

CACHE_PWD = "123-fbt-all-cache-!@#"
SESSION_PWD = "123-fbt-session-cache-!@#"
SEARCH_PWD = "123-fbt-search-cache-!@#"
MSG_PWD = "123-fbt-msg-cache-!@#"
LRU_PWD = "123-fbt-lru-cache-!@#"
DB_PWD = "123-fbt-db-cache-!@#"
REDIS_PWD = (CACHE_PWD, SESSION_PWD, SEARCH_PWD, MSG_PWD, LRU_PWD, DB_PWD)
REDIS_PORT = (6381, 6382, 6383, 6384, 6385, 6386)

# sentinels
MASTER_NAME = "cache-redis"

if DEBUG_ENV:
    # pub_sub redis info
    PUB_SUB_HOST = '10.10.88.106'
    PUB_SUB_PWD = '123-fbt-pub-sub-!@#'
    PUB_SUB_PORT = 6380
    TORNADO_HOSTS = ['10.10.79.163']
    REDIS_MASTER_HOST = '10.10.88.106'
    REDIS_CACHE_HOST_PORTS = [("10.10.173.244", 6379, "10.10.183.118", 6379)]
    REDIS_DB_HOST_PORTS = [("10.10.173.244", 6379, "10.10.183.118", 6379)]
else:
    # pub_sub redis info
    PUB_SUB_HOST = '10.10.95.244'
    PUB_SUB_PWD = '123-fbt-pub-sub-!@#'
    PUB_SUB_PORT = 6380
    TORNADO_HOSTS = ['10.10.56.138',]
    REDIS_MASTER_HOST = '10.10.95.244'
    REDIS_CACHE_HOST_PORTS = [("10.10.185.244", 6379, "10.10.187.229", 6379)]
    REDIS_DB_HOST_PORTS = [("10.10.42.144", 6379, "10.10.92.15", 6379)]

TAG_CLASS = {u"考研": 1, u"考证": 2, u"留学": 3, u"就业": 4, u"校园": 5, u"实习": 6}
STAR_CLASS = {u"考研": "is_postgraduate_star", u"考证": "is_certificate_star", u"留学": "is_USA_star", u"就业": "is_work_star", u"校园": "is_campus_star", u"实习": "is_internship_star"}
CLASS_STAR = {"is_postgraduate_star": u"研", "is_certificate_star": u"证", "is_USA_star": u"学", "is_work_star": u"业", "is_campus_star": u"校", "is_internship_star": u"习"}
STAR_THUMB_NUM_THRESHOLD = 66
STAR_POSTS_THRESHOLD = 10
TOKEN_SECRET = 'FU2PL7qn0cIe9urFVj8OYMW61el_okaprnFmRry-7r0='

if DEBUG_ENV:
    OUR_WEB_URL = "http://test.friendsbt.com"
else:
    OUR_WEB_URL = "http://study.friendsbt.com"

import random
if DEBUG_ENV:
    ES_CLUSTER_HOSTS = ['10.10.79.163',]
else:
    ES_CLUSTER_HOSTS = ['10.10.66.118',]
ES_PORT = 9200
ES_HOST = ES_CLUSTER_HOSTS[random.randint(0, len(ES_CLUSTER_HOSTS)-1)]

CHAT_PORT = 9876
if DEBUG_ENV:
    CHAT_HOST = "http://127.0.0.1:%d/message/proxy" % CHAT_PORT
else:
    CHAT_HOST = "http://127.0.0.1:%d/message/proxy" % CHAT_PORT

MAX_PREVIEW_SIZE = 10 * 1024 * 1024  # 10 MB
