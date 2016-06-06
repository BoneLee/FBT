#!/usr/bin/python

import tornado.web
from tornado.ioloop import IOLoop
from tornado import gen 
import time


@gen.coroutine
def async_sleep(seconds):
    yield gen.Task(IOLoop.instance().add_timeout, time.time() + seconds)


class TestHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        yield async_sleep(1)
        self.write(str(22))
        self.finish()


application = tornado.web.Application([
    (r"/", TestHandler),
    ])  

application.listen(9999)
IOLoop.instance().start()