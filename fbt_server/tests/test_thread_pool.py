__author__ = 'bone'

from concurrent.futures import ThreadPoolExecutor
import tornado.ioloop
import tornado.gen

# Good thread pool has return result
def is_prime(n):
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

thread_pool = ThreadPoolExecutor(4)
@tornado.gen.coroutine
def call_blocking():
    res = yield [thread_pool.submit(is_prime, 112272535095293),thread_pool.submit(is_prime, 112272535095294)]
    print "res:"+str(res)
    raise tornado.gen.Return(res)

tornado.ioloop.IOLoop.instance().run_sync(call_blocking)