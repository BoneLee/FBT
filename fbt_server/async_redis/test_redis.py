import tornado.ioloop
import tornado.web
from random import randint
import redis
import tornadoredis
import tornado.gen
from asyncRedis import AsyncStrictRedis
from asyncSentinel import AsyncSentinel
from redis.sentinel import Sentinel

#print lru_sentinel2.discover_master('cache-redis')
#master = lru_sentinel.master_for('cache-redis', socket_timeout=0.1)
#slave = lru_sentinel.slave_for('cache-redis', socket_timeout=0.1)

def test_redis_write():
    r = redis.StrictRedis()
    for i in range(1,10000):
        r.set("key"+str(i), i)
        #r.incr("key"+str(i))

def test_redis_read():
    r = redis.StrictRedis()
    for i in range(1,10000):
        r.get("key"+str(i))

class RedisReadHandler(tornado.web.RequestHandler):
    def get(self):
        test_redis_read()
        self.write("Hello, redis read test!")

class RedisWriteHandler(tornado.web.RequestHandler):
    def get(self):
        test_redis_write()
        self.write("Hello, redis write test!")

class MainHandler(tornado.web.RequestHandler):
        def get(self):
            self.write("Hello, world.")

class RedisReadWriteHandler(tornado.web.RequestHandler):
        def get(self):
            r = redis.StrictRedis()
            i = randint(1, 1000)
            r.set("key"+str(i), i)
            r.get("key"+str(i))
            self.finish("Hello, redis read write test!")

class TornadoRedisReadWriteHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        c = tornadoredis.Client()
        c.connect()
        i = randint(1, 1000)
        yield tornado.gen.Task(c.set, 'key2'+str(i),i)
        val = yield tornado.gen.Task(c.get, 'key2'+str(i))
        self.write("Hello, redis read write test!")
        self.finish()

class AsyncRedisReadWriteHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        ar = AsyncStrictRedis()
        i = randint(1, 1000)
        #v = yield ar.get('key2628')
        #print 'v', v
        #v = yield ar.execute_command('GET', 'key2628')
        #print 'v', v
        print 'i', i
        yield ar.set('key2'+str(i),i)
        print "seted!"
        val = yield ar.get('key2'+str(i))
        print val
        yield ar.zadd('zsettest', i, 'key2' + str(i))
        res = yield ar.zrange('zsettest', 0, -1)
        print res

        p = ar.pipeline()
        p.get('key2' + str(i))
        p.zrange('zsettest', 0, -1)
        res2 = yield p.execute()
        print res2
        self.write("Hello, redis read write test!")
        self.finish()

class AsyncSentinelReadWriteHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        ar = AsyncStrictRedis()
        lru_sentinel = AsyncSentinel([('127.0.0.1', 26385)], password='123-fbt-lru-cache-!@#')
        #lru_sentinel2 = Sentinel([('127.0.0.1', 26385)], password='123-fbt-lru-cache-!@#')
        dm = yield lru_sentinel.discover_master('cache-redis')
        print 'discover_master', dm
        ds = yield lru_sentinel.discover_slaves('cache-redis')
        print ds
        master = lru_sentinel.master_for('cache-redis')
        print master
        slave = lru_sentinel.slave_for('cache-redis')
        print slave
        i = randint(1, 1000)
        print 'i', i
        yield master.set('test' + str(i), i)
        res = yield slave.get('test' + str(i))
        print res
        self.write("Hello, redis read write test!")
        self.finish()

application = tornado.web.Application([
(r"/", MainHandler),
(r"/read", RedisReadHandler),
(r"/write", RedisWriteHandler),
(r"/read_write", RedisReadWriteHandler),
(r"/read_write2", TornadoRedisReadWriteHandler),
(r"/read_write3", AsyncRedisReadWriteHandler),
(r"/ac", AsyncSentinelReadWriteHandler)
])

if __name__ == "__main__":
    application.listen(8000)
    tornado.ioloop.IOLoop.instance().start()