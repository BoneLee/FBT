__author__ = 'bone-lee'

from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

import tornado.ioloop
import tornado.web
import time


EXECUTOR = ThreadPoolExecutor(max_workers=4)


def unblock(f):

    @tornado.web.asynchronous
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]

        def callback(future):
            self.write(future.result())
            self.finish()

        EXECUTOR.submit(
            partial(f, *args, **kwargs)
        ).add_done_callback(
            lambda future: tornado.ioloop.IOLoop.instance().add_callback(
                partial(callback, future)))

    return wrapper


class SleepHandler(tornado.web.RequestHandler):

    @unblock
    def get(self, n):
        time.sleep(float(n))
        return "Awake! %s" % time.time()



class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello, world %s" % time.time())


# class SleepHandler(tornado.web.RequestHandler):
#
#     def get(self, n):
#         time.sleep(float(n))
#         self.write("Awake! %s" % time.time())


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/sleep/(\d+)", SleepHandler),
])


class Temp(object):
    @classmethod
    def is_prime(cls, n):
      print "num:"+str(n)
      import math
      if n % 2 == 0:
        print "False"
        return False

      sqrt_n = int(math.floor(math.sqrt(n)))
      for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            print "False"
            return False
      print "True"
      return True

    @classmethod
    def do(cls):
        with ThreadPoolExecutor(max_workers=4) as e:
            result=e.submit(cls.is_prime,112272535095293)
            # def done():
            #     print "result:",str(result.result())
            # result.add_done_callback(done)


if __name__ == "__main__":
    # application.listen(8888)
    # tornado.ioloop.IOLoop.instance().start()
    Temp.do()


