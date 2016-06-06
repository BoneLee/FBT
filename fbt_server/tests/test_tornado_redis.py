__author__ = 'bone'

import tornado.ioloop
import tornado.web
import tornado.gen
import tornadoredis

@tornado.gen.coroutine
def test():
    r = tornadoredis.Client()
    yield tornado.gen.Task(r.set,"name","bonelee")
    name = yield tornado.gen.Task(r.get, "name")
    print name

future = test()
loop = tornado.ioloop.IOLoop.instance()

def callback(arg):
    print "over:"+str(arg.result())
    loop.stop()

loop.add_future(future, callback)
loop.start()

# tornado.ioloop.IOLoop.instance().run_sync(test)