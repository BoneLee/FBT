# coding: utf-8
__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

# import constant
# constant.PUB_SUB_HOST = 'localhost'
# constant.PUB_SUB_PORT = 6379
# constant.PUB_SUB_PWD = None
from redis_pub_sub_client import RedisSubscribeClient, RedisPubClient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import mock

msg_list=list()

def redis_sub_callback(body):
    msg_list.append(body)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("message list:"+str(msg_list))

# redis_sub_client = FBCoinSubscribeClient(CHANNEL_COIN_VARY)

class WebApp(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/get', MainHandler),
        ]
        tornado.web.Application.__init__( self, handlers )

@mock.patch("redis_pub_sub_client.constant.PUB_SUB_HOST", 'localhost')
@mock.patch("redis_pub_sub_client.constant.PUB_SUB_PWD", None)
@mock.patch("redis_pub_sub_client.constant.PUB_SUB_PORT", 6379)
def main():
    application = WebApp()
    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.listen(8890)
    ioloop=tornado.ioloop.IOLoop.instance()
    redis_sub_client= RedisSubscribeClient(redis_sub_callback)

    import simplejson as json

    RedisPubClient().publish(json.dumps({123:456}))

    try:
        ioloop.start()
    except:
        redis_sub_client.close()
        print "OK. Exit..."

if __name__ == '__main__':
    main()
