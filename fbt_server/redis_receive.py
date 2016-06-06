# coding: utf-8
__author__ = 'bone-lee'

# from constant import CHANNEL_COIN_VARY
from redis_pub_sub_client import RedisSubscribeClient, RedisPubClient
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen

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

if __name__ == '__main__':
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
