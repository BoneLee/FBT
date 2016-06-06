# coding: utf-8
from redis_pub_sub_client import RedisPubClient

__author__ = 'bone-lee'

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import simplejson as json
import tornadoredis

class PostHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        RedisPubClient().publish(self.get_argument("msg",json.dumps({"321": 123})))
        self.write("send OK. go to localhost:8890/get to see message list.")
        self.finish()

class WebApp(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/post', PostHandler),
        ]
        tornado.web.Application.__init__( self, handlers )

if __name__ == '__main__':
    application = WebApp()
    httpServer = tornado.httpserver.HTTPServer(application)
    httpServer.listen(8889)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        print "OK. Exit..."
