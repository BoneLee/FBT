# -*- coding: utf-8 -*-
import sys
import random
import time as mod_time

from tornado.testing import gen_test, AsyncTestCase
from datetime import datetime, timedelta
from functools import partial

from tornado import gen
from redis._compat import (unichr, u, b, ascii_letters, iteritems, iterkeys,
                           itervalues)

sys.path.append('..')
from asyncRedis import AsyncStrictRedis

SCAN_BUF_SIZE = 200

def f(func, *args, **kwargs):
    return func(*args, **kwargs)
gen.Task = f

class AsyncRedisTestBasic(AsyncTestCase):
    def setUp(self):
        super(AsyncRedisTestBasic, self).setUp()
        self.client = AsyncStrictRedis()
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        yield self.client.flushdb()

    @gen_test
    def test_setget_unicode(self):
        # get and set can't be tested independently of each other
        r = self.client
        res = yield r.get('a')
        self.assertTrue(res is None)
        byte_string = b('value')
        integer = 5
        unicode_string = unichr(3456) + u('abcd') + unichr(3421)
        yield r.set('byte_string', byte_string)
        yield r.set('integer', 5)
        yield r.set('unicode_string', unicode_string)
        res = yield r.get('byte_string')
        self.assertEqual(res, byte_string)
        res = yield r.get('integer')
        self.assertEqual(res, b(str(integer)))
        res = yield r.get('unicode_string')
        self.assertEqual(res.decode('utf-8'), unicode_string)
        self.stop()

    @gen_test
    def test_set(self):
        # basic test
        res = yield gen.Task(self.client.set, 'foo', 'bar')
        self.assertEqual(res, True)

        # test key expiration in milliseconds, pexpire
        res = yield gen.Task(self.client.set, 'foo1', 'bar1', px=10)
        self.assertEqual(res, True)
        #yield gen.Task(self.io_loop.add_timeout, mod_time.time() + 0.015)
        mod_time.sleep(0.015)
        res = yield gen.Task(self.client.get, 'foo1')
        self.assertEqual(res, None)

        # test key expiration in seconds, expire
        res = yield gen.Task(self.client.set, 'foo2', 'bar2', ex=1)
        self.assertEqual(res, True)
        #yield gen.Task(self.io_loop.add_timeout, mod_time.time() + 1.001)
        mod_time.sleep(1.001)
        res = yield gen.Task(self.client.get, 'foo2')
        self.assertEqual(res, None)

        # test set only_if_not_exists, only_if_not_exists
        res = yield gen.Task(self.client.set, 'foo3', 'bar3', nx=True)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'foo3', 'bar3', nx=True)
        #self.assertEqual(res, False)
        self.assertEqual(res, None)

        # test set only_if_exists, only_if_exists
        res = yield gen.Task(self.client.set, 'foo3', 'only_if_exists', xx=True)
        get_res = yield gen.Task(self.client.get, 'foo3')
        self.assertEqual(res, True)
        self.assertEqual(get_res, 'only_if_exists')
        res = yield gen.Task(self.client.set, 'foo4', 'bar4', xx=True)
        #self.assertEqual(res, False)
        self.assertEqual(res, None)

        # test exception in case only_if_exists and only_if_not_exists
        # enabled in same time
        #f = partial(self.client.set, 'f', 'b', xx=True, nx=True)
        # self.assertRaises(ValueError, f)
        f = yield self.client.set('f', 'b', xx=True, nx=True)
        self.assertEqual(None, f)
        self.stop()

    @gen_test
    def test_delete(self):
        yield gen.Task(self.client.mset, {'a': 1, 'b': 2, 'c': 3})
        yield gen.Task(self.client.delete, 'a')
        res = yield gen.Task(self.client.exists, 'a')
        self.assertEqual(res, False)

        yield gen.Task(self.client.delete, 'b', 'c')
        res = yield gen.Task(self.client.exists, 'b')
        self.assertEqual(res, False)
        res = yield gen.Task(self.client.exists, 'c')
        self.assertEqual(res, False)
        self.stop()

    @gen_test
    def test_setex(self):
        res = yield gen.Task(self.client.setex, 'foo', 5, 'bar')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.ttl, 'foo')
        self.assertEqual(res, 5)
        self.stop()

    @gen_test
    def test_setnx(self):
        res = yield gen.Task(self.client.setnx, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.setnx, 'a', 0)
        self.assertEqual(res, False)
        self.stop()

    @gen_test
    def test_get(self):
        res = yield gen.Task(self.client.set, 'foo', 'bar')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(res, 'bar')
        self.stop()

    @gen_test
    def test_randomkey(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'b', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.randomkey)
        self.assertIn(res, ['a', 'b'])
        res = yield gen.Task(self.client.randomkey)
        self.assertIn(res, ['a', 'b'])
        res = yield gen.Task(self.client.randomkey)
        self.assertIn(res, ['a', 'b'])
        self.stop()

    @gen_test
    def test_substr(self):
        res = yield gen.Task(self.client.set, 'foo', 'lorem ipsum')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.substr, 'foo', 2, 4)
        self.assertEqual(res, 'rem')
        self.stop()

    @gen_test
    def test_append(self):
        res = yield gen.Task(self.client.set, 'foo', 'lorem ipsum')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.append, 'foo', ' bar')
        self.assertEqual(res, 15)
        res = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(res, 'lorem ipsum bar')
        self.stop()

    @gen_test
    def test_dbsize(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'b', 2)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.dbsize)
        self.assertEqual(res, 2)
        self.stop()

    @gen_test
    def test_save(self):
        # TODO: Replace it with the TIME command.
        now = datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
        res = yield gen.Task(self.client.save)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lastsave)
        self.assertGreaterEqual(res, now)
        self.stop()

    @gen_test
    def test_keys(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'b', 2)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.keys, '*')
        self.assertEqual(set(res), set(['a', 'b']))
        res = yield gen.Task(self.client.keys, '')
        self.assertEqual(res, [])

        res = yield gen.Task(self.client.set, 'foo_a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'foo_b', 2)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.keys, 'foo_*')
        self.assertEqual(set(res), set(['foo_a', 'foo_b']))
        self.stop()

    @gen_test
    def test_expire(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.expire, 'a', 10)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.ttl, 'a')
        self.assertEqual(res, 10)
        self.stop()

    @gen_test
    def test_expireat(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        t_expire = int(mod_time.time()) + 10
        res = yield gen.Task(self.client.expireat, 'a', t_expire)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.ttl, 'a')
        self.assertIn(res, (9, 10, 11))

        t_expire = datetime.now() + timedelta(seconds=10)
        res = yield gen.Task(self.client.expireat, 'a', t_expire)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.ttl, 'a')
        self.assertIn(res, (9, 10, 11))

        self.stop()

    @gen_test
    def test_pexpire(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.pexpire, 'a', 10)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.pttl, 'a')
        self.assertLessEqual(res, 10)

        res = yield gen.Task(self.client.pexpire, 'a',
                             timedelta(milliseconds=10))
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.pttl, 'a')
        self.assertLessEqual(res, 10)

        self.stop()

    @gen_test
    def test_pexpireat(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        t_expire = (int(mod_time.time()) + 2) * 1000
        res = yield gen.Task(self.client.pexpireat, 'a', t_expire)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.pttl, 'a')
        self.assertLessEqual(res, 2000)
        self.assertGreater(res, 1000)

        t_expire = datetime.now() + timedelta(seconds=1)
        res = yield gen.Task(self.client.pexpireat, 'a', t_expire)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.pttl, 'a')
        self.assertLessEqual(res, 1000)
        self.assertGreater(res, 800)

        self.stop()

    @gen_test
    def test_type(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.type, 'a')
        self.assertEqual(res, 'string')
        res = yield gen.Task(self.client.rpush, 'b', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.rpushx, 'b', 1)
        self.assertTrue(res)
        res = yield gen.Task(self.client.rpushx, 'c', 1)
        self.assertFalse(res)
        res = yield gen.Task(self.client.type, 'b')
        self.assertEqual(res, 'list')
        res = yield gen.Task(self.client.sadd, 'c', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.type, 'c')
        self.assertEqual(res, 'set')
        res = yield gen.Task(self.client.hset, 'd', 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.type, 'd')
        self.assertEqual(res, 'hash')
        res = yield gen.Task(self.client.zadd, 'e', 1, 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.type, 'e')
        self.assertEqual(res, 'zset')
        self.stop()

    @gen_test
    def test_rename(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.rename, 'a', 'b')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'c', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.renamenx, 'c', 'b')
        self.assertEqual(res, False)
        self.stop()

    '''
    @gen_test
    def test_move(self):
        res = yield gen.Task(self.client.select, 8)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.delete, 'a')
        self.assertEqual(res, False)
        res = yield gen.Task(self.client.select, 9)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.move, 'a', 8)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.exists, 'a')
        self.assertEqual(res, False)
        res = yield gen.Task(self.client.select, 8)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.get, 'a')
        self.assertEqual(res, '1')
        res = yield gen.Task(self.client.select, 8)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.delete, 'a')
        self.assertEqual(res, True)
        self.stop()
    '''

    @gen_test
    def test_exists(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.exists, 'a')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.delete, 'a')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.exists, 'a')
        self.assertEqual(res, False)
        self.stop()

    @gen_test
    def test_mset_mget(self):
        res = yield gen.Task(self.client.mset, {'a': 1, 'b': 2})
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.get, 'a')
        self.assertEqual(res, '1')
        res = yield gen.Task(self.client.get, 'b')
        self.assertEqual(res, '2')
        res = yield gen.Task(self.client.mget, ['a', 'b'])
        self.assertEqual(res, ['1', '2'])
        self.stop()

    @gen_test
    def test_msetnx(self):
        res = yield gen.Task(self.client.msetnx, {'a': 1, 'b': 2})
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.msetnx, {'b': 3, 'c': 4})
        self.assertEqual(res, False)
        self.stop()

    @gen_test
    def test_getset(self):
        res = yield gen.Task(self.client.set, 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.getset, 'a', 2)
        self.assertEqual(res, '1')
        res = yield gen.Task(self.client.get, 'a')
        self.assertEqual(res, '2')
        self.stop()

    @gen_test
    def test_hash(self):
        res = yield gen.Task(self.client.hmset, 'foo', {'a': 1, 'b': 2})
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.hgetall, 'foo')
        self.assertEqual(res, {'a': '1', 'b': '2'})
        res = yield gen.Task(self.client.hdel, 'foo', 'a')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.hgetall, 'foo')
        self.assertEqual(res, {'b': '2'})
        res = yield gen.Task(self.client.hget, 'foo', 'a')
        self.assertEqual(res, None)
        res = yield gen.Task(self.client.hget, 'foo', 'b')
        self.assertEqual(res, '2')
        res = yield gen.Task(self.client.hlen, 'foo')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.hincrby, 'foo', 'b', 3)
        self.assertEqual(res, 5)
        res = yield gen.Task(self.client.hkeys, 'foo')
        self.assertEqual(res, ['b'])
        res = yield gen.Task(self.client.hvals, 'foo')
        self.assertEqual(res, ['5'])
        res = yield gen.Task(self.client.hset, 'foo', 'a', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.hmget, 'foo', ['a', 'b'])
        #self.assertEqual(res, {'a': '1', 'b': '5'})
        self.assertEqual(res, ['1', '5'])
        res = yield gen.Task(self.client.hexists, 'foo', 'b')
        self.assertEqual(res, True)
        self.stop()

    @gen_test
    def test_hdel(self):
        res = yield gen.Task(self.client.hmset, 'foo', {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(res, True)
        yield gen.Task(self.client.hdel, 'foo', 'a', 'b')
        res = yield gen.Task(self.client.hkeys, 'foo')
        self.assertEqual(res, ['c'])

        self.stop()

    @gen_test
    def test_hincrbyfloat(self):
        yield gen.Task(self.client.hset, 'mykey', 'field', '10.5')
        res = yield gen.Task(self.client.hincrbyfloat, 'mykey', 'field', '0.1')
        # '10.6'
        self.assertEqual(res, 10.6)
        res = yield gen.Task(self.client.hget, 'mykey', 'field')
        self.assertEqual(res, '10.6')
        self.stop()

    @gen_test
    def test_hsetnx(self):
        res = yield gen.Task(self.client.hsetnx, 'mykey', 'field', 'Hello')
        self.assertTrue(res)
        res = yield gen.Task(self.client.hsetnx, 'mykey', 'field', 'Hello')
        self.assertFalse(res)
        self.stop()

    @gen_test
    def test_incrdecr(self):
        res = yield gen.Task(self.client.incr, 'foo')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.incrby, 'foo', 10)
        self.assertEqual(res, 11)
        res = yield gen.Task(self.client.decr, 'foo')
        self.assertEqual(res, 10)
#        res = yield gen.Task(self.client.decrby, 'foo', 10)
#      self.assertEqual(res, 0)
        res = yield gen.Task(self.client.decr, 'foo')
        self.assertEqual(res, 9)
        self.stop()

    @gen_test
    def test_incrbyfloat(self):
        yield gen.Task(self.client.set, 'mykey', '10.50')
        res = yield gen.Task(self.client.incrbyfloat, 'mykey', '0.1')
        # '10.6'
        self.assertEqual(res, 10.6)
        self.stop()

    @gen_test
    def test_ping(self):
        res = yield gen.Task(self.client.ping)
        self.assertEqual(res, True)
        self.stop()

    @gen_test
    def test_lists(self):
        res = yield gen.Task(self.client.lpush, 'foo', 1)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.lrange, 'foo', 0, -1)
        self.assertEqual(res, ['1'])
        res = yield gen.Task(self.client.rpop, 'foo')
        self.assertEqual(res, '1')
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 0)

        res = yield gen.Task(self.client.lpush, 'foo', 2, 3, 4)
        self.assertEqual(res, 3)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 3)

        res = yield gen.Task(self.client.lrem, 'foo', -1, 2)
        self.assertTrue(res)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 2)

        res = yield gen.Task(self.client.lset, 'foo', 0, 5)
        self.assertTrue(res)
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.lindex, 'foo', 0)
        self.assertEqual(res, '5')

        res = yield gen.Task(self.client.ltrim, 'foo', 0, 0)
        self.assertTrue(res)
        res = yield gen.Task(self.client.lpop, 'foo')
        self.assertEqual(res, '5')
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 0)

        self.stop()

    @gen_test
    def test_lpushx(self):
        res = yield gen.Task(self.client.lpushx, 'foo', 1)
        self.assertFalse(res)
        res = yield gen.Task(self.client.lpush, 'foo', 1)
        self.assertTrue(res)
        res = yield gen.Task(self.client.lpushx, 'foo', 1)
        self.assertEqual(res, 2)

        self.stop()

    '''
    @gen_test
    def test_brpop(self):
        res = yield gen.Task(self.client.lpush, 'foo', 'ab')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lpush, 'bar', 'cd')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.brpop, ['foo', 'bar'], 1)
        #self.assertEqual(res, {'foo': 'ab'})
        self.assertEqual(res, ('foo', 'ab'))
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 0)
        res = yield gen.Task(self.client.llen, 'bar')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.brpop, ['foo', 'bar'], 1)
        self.assertEqual(res, ('bar', 'cd'))

        self.client.brpop('foo', 1, callback=(yield gen.Callback("brpop")))
        c2 = self._new_client()
        yield gen.Task(c2.lpush, 'foo', 'zz')
        res = yield gen.Wait("brpop")
        self.assertEqual(res, {'foo': 'zz'})

        self.stop()

    @gen_test
    def test_rpoplpush(self):
        res = yield gen.Task(self.client.lpush, 'foo', 'ab')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lpush, 'bar', 'cd')
        self.assertEqual(res, True)

        res = yield gen.Task(self.client.rpoplpush, 'foo', 'bar')
        self.assertEqual(res, 'ab')
        res = yield gen.Task(self.client.lpop, 'bar')
        self.assertEqual(res, 'ab')

        self.stop()

    @gen_test
    def test_brpoplpush(self):
        res = yield gen.Task(self.client.lpush, 'foo', 'ab')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lpush, 'bar', 'cd')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lrange, 'foo', 0, -1)
        self.assertEqual(res, ['ab'])
        res = yield gen.Task(self.client.lrange, 'bar', 0, -1)
        self.assertEqual(res, ['cd'])
        res = yield gen.Task(self.client.brpoplpush, 'foo', 'bar')
        self.assertEqual(res, 'ab')
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 0)
        res = yield gen.Task(self.client.lrange, 'bar', 0, -1)
        self.assertEqual(res, ['ab', 'cd'])
        self.stop()

    @gen_test
    def test_blpop(self):
        res = yield gen.Task(self.client.lpush, 'foo', 'ab')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.lpush, 'bar', 'cd')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.blpop, ['foo', 'bar'], 1)
        self.assertEqual(res, ('foo', 'ab'))
        res = yield gen.Task(self.client.llen, 'foo')
        self.assertEqual(res, 0)
        res = yield gen.Task(self.client.llen, 'bar')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.blpop, ['foo', 'bar'], 1)
        self.assertEqual(res, ('bar', 'cd'))

        self.client.blpop('foo', 1, callback=(yield gen.Callback("blpop")))
        c2 = self._new_client()
        yield gen.Task(c2.rpush, 'foo', 'zz')
        res = yield gen.Wait("blpop")
        self.assertEqual(res, {'foo': 'zz'})

        self.stop()
    '''
    @gen_test
    def test_linsert(self):
        yield gen.Task(self.client.rpush, 'mylist', 'Hello')
        yield gen.Task(self.client.rpush, 'mylist', 'World')
        res = yield gen.Task(self.client.linsert, 'mylist', 'BEFORE', 'World', 'There')
        self.assertEqual(res, 3)
        res = yield gen.Task(self.client.lrange, 'mylist', 0, -1)
        self.assertEqual(res, ['Hello', 'There', 'World'])

        self.stop()

    @gen_test
    def test_sets(self):
        res = yield gen.Task(self.client.smembers, 'foo')
        self.assertEqual(res, set())
        res = yield gen.Task(self.client.sadd, 'foo', 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.srandmember, 'foo')
        self.assertIn(res, ['a', 'b', 'c'])
        res = yield gen.Task(self.client.scard, 'foo')
        self.assertEqual(res, 3)
        res = yield gen.Task(self.client.srem, 'foo', 'a')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.smove, 'foo', 'bar', 'b')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.smembers, 'bar')
        self.assertEqual(res, set(['b']))
        res = yield gen.Task(self.client.sismember, 'foo', 'c')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.spop, 'foo')
        self.assertEqual(res, 'c')
        self.stop()

    @gen_test
    def test_sets2(self):
        res = yield gen.Task(self.client.sadd, 'foo', 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'd')
        self.assertEqual(res, 1)

        res = yield gen.Task(self.client.sdiff, ['foo', 'bar'])
        self.assertEqual(res, set(['a']))
        res = yield gen.Task(self.client.sdiff, ['bar', 'foo'])
        self.assertEqual(res, set(['d']))
        res = yield gen.Task(self.client.sinter, ['foo', 'bar'])
        self.assertEqual(res, set(['b', 'c']))
        res = yield gen.Task(self.client.sunion, ['foo', 'bar'])
        self.assertEqual(res, set(['a', 'b', 'c', 'd']))
        self.stop()

    @gen_test
    def test_sets3(self):
        res = yield gen.Task(self.client.sadd, 'foo', 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'foo', 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.sadd, 'bar', 'd')
        self.assertEqual(res, 1)

        #res = yield gen.Task(self.client.sdiffstore, ['foo', 'bar'], 'zar')
        res = yield gen.Task(self.client.sdiffstore, 'zar', ['foo', 'bar'])
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.smembers, 'zar')
        self.assertEqual(res, set(['a']))
        res = yield gen.Task(self.client.delete, 'zar')
        self.assertEqual(res, True)

        res = yield gen.Task(self.client.sinterstore, 'zar', ['foo', 'bar'])
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.smembers, 'zar')
        self.assertEqual(res, set(['b', 'c']))
        res = yield gen.Task(self.client.delete, 'zar')
        self.assertEqual(res, True)

        res = yield gen.Task(self.client.sunionstore, 'zar', ['foo', 'bar'])
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.smembers, 'zar')
        self.assertEqual(res, set(['a', 'b', 'c', 'd']))
        self.stop()

    @gen_test
    def test_zsets(self):
        res = yield gen.Task(self.client.zadd, 'foo', 1, 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'foo', 2.15, 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zscore, 'foo', 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zscore, 'foo', 'b')
        self.assertEqual(res, 2.15)
        res = yield gen.Task(self.client.zrank, 'foo', 'a')
        self.assertEqual(res, 0)
        res = yield gen.Task(self.client.zrank, 'foo', 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zrevrank, 'foo', 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zrevrank, 'foo', 'b')
        self.assertEqual(res, 0)
        res = yield gen.Task(self.client.zincrby, 'foo', 'a', 1)
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zincrby, 'foo', 'b', 1)
        self.assertEqual(res, 3.15)
        res = yield gen.Task(self.client.zscore, 'foo', 'a')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zscore, 'foo', 'b')
        self.assertEqual(res, 3.15)
        res = yield gen.Task(self.client.zrange, 'foo', 0, -1, withscores=True)
        self.assertEqual(res, [('a', 2.0), ('b', 3.15)])
        res = yield gen.Task(self.client.zrange, 'foo', 0, -1, False)
        self.assertEqual(res, ['a', 'b'])
        res = yield gen.Task(self.client.zrevrange, 'foo', 0, -1, True,)
        self.assertEqual(res, [('b', 3.15), ('a', 2.0)])
        res = yield gen.Task(self.client.zrevrange, 'foo', 0, -1, False)
        self.assertEqual(res, ['b', 'a'])
        res = yield gen.Task(self.client.zcard, 'foo')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zadd, 'foo', 3.5, 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zrangebyscore, 'foo', '-inf', '+inf',
                             None, None, False)
        self.assertEqual(res, ['a', 'b', 'c'])
        res = yield gen.Task(self.client.zrevrangebyscore, 'foo',
                             '+inf', '-inf', None, None, False)
        self.assertEqual(res, ['c', 'b', 'a'])
        res = yield gen.Task(self.client.zrangebyscore, 'foo', '2.1', '+inf',
                             None, None, True)
        self.assertEqual(res, [('b', 3.15), ('c', 3.5)])
        res = yield gen.Task(self.client.zrevrangebyscore, 'foo',
                             '+inf', '2.1', None, None, True)
        self.assertEqual(res, [('c', 3.5), ('b', 3.15)])
        res = yield gen.Task(self.client.zrangebyscore, 'foo', '-inf', '3.0',
                             0, 1, False)
        self.assertEqual(res, ['a'])
        res = yield gen.Task(self.client.zrangebyscore, 'foo', '-inf', '+inf',
                             1, 2, False)
        self.assertEqual(res, ['b', 'c'])
        res = yield gen.Task(self.client.zrevrangebyscore, 'foo',
                             '+inf', '-inf', 1, 2, False)
        self.assertEqual(res, ['b', 'a'])

        res = yield gen.Task(self.client.delete, 'foo')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.zadd, 'foo', 1, 'a')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'foo', 2, 'b')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'foo', 3, 'c')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'foo', 4, 'd')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zremrangebyrank, 'foo', 2, 4)
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zremrangebyscore, 'foo', 0, 2)
        self.assertEqual(res, 2)

        res = yield gen.Task(self.client.zadd, 'a', 1, 'a1')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'a', 1, 'a2')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'a', 1, 'a3')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'b', 2, 'a1')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'b', 2, 'a3')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'b', 2, 'a4')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'c', 6, 'a1')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'c', 5, 'a3')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zadd, 'c', 4, 'a4')
        self.assertEqual(res, 1)
        # ZINTERSTORE
        # sum, no weight
        res = yield gen.Task(self.client.zinterstore, 'z', ['a', 'b', 'c'])
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(res, [('a3', 8), ('a1', 9)])
        # max, no weight
        res = yield gen.Task(self.client.zinterstore, 'z', ['a', 'b', 'c'],
                             aggregate='MAX')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(res, [('a3', 5), ('a1', 6)])
        # with weight
        res = yield gen.Task(self.client.zinterstore, 'z',
                             {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(res, [('a3', 20), ('a1', 23)])

        # ZUNIONSTORE
        # sum, no weight
        res = yield gen.Task(self.client.zunionstore, 'z', ['a', 'b', 'c'])
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(dict(res), dict(a1=9, a2=1, a3=8, a4=6))
        # max, no weight
        res = yield gen.Task(self.client.zunionstore, 'z', ['a', 'b', 'c'],
                             aggregate='MAX')
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(dict(res), dict(a1=6, a2=1, a3=5, a4=4))
        # with weight
        res = yield gen.Task(self.client.zunionstore, 'z',
                             {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.zrange, 'z', 0, -1, withscores=True)
        self.assertEqual(dict(res), dict(a1=23, a2=1, a3=20, a4=16))
        self.stop()

    @gen_test
    def test_zset(self):
        NUM = 100
        long_list = list(map(str, range(0, NUM)))
        for i in long_list:
            res = yield gen.Task(self.client.zadd, 'foobar', i, i)
            self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zrange, 'foobar', 0, NUM,
                             withscores=False)
        self.assertEqual(res, long_list)
        self.stop()

    @gen_test
    def test_zrem(self):
        yield gen.Task(self.client.zadd, 'myzset', 1, 'one')
        yield gen.Task(self.client.zadd, 'myzset', 2, 'two')
        yield gen.Task(self.client.zadd, 'myzset', 3, 'three')
        yield gen.Task(self.client.zadd, 'myzset', 4, 'four')
        res = yield gen.Task(self.client.zrem, 'myzset', 'two')
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zrem, 'myzset', 'three', 'four')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zrange, 'myzset', 0, -1, False)
        self.assertEqual(res, ['one'])
        self.stop()

    @gen.coroutine
    def _make_list(self, key, items, callback=None):
        yield gen.Task(self.client.delete, key)
        for i in items:
            yield gen.Task(self.client.rpush, key, i)
        if callback:
            callback(True)

    @gen_test
    def test_sort(self):
        res = yield gen.Task(self.client.sort, 'a')
        self.assertEqual(res, [])
        yield gen.Task(self._make_list, 'a', '3214')
        res = yield gen.Task(self.client.sort, 'a')
        self.assertEqual(res, ['1', '2', '3', '4'])
        res = yield gen.Task(self.client.sort, 'a', start=1, num=2)
        self.assertEqual(res, ['2', '3'])

        res = yield gen.Task(self.client.set, 'score:1', 8)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'score:2', 3)
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'score:3', 5)
        self.assertEqual(res, True)
        yield gen.Task(self._make_list, 'a_values', '123')
        res = yield gen.Task(self.client.sort, 'a_values', by='score:*')
        self.assertEqual(res, ['2', '3', '1'])

        res = yield gen.Task(self.client.set, 'user:1', 'u1')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'user:2', 'u2')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.set, 'user:3', 'u3')
        self.assertEqual(res, True)

        yield gen.Task(self._make_list, 'a', '231')
        res = yield gen.Task(self.client.sort, 'a', get='user:*')
        self.assertEqual(res, ['u1', 'u2', 'u3'])

        yield gen.Task(self._make_list, 'a', '231')
        res = yield gen.Task(self.client.sort, 'a', desc=True)
        self.assertEqual(res, ['3', '2', '1'])

        yield gen.Task(self._make_list, 'a', 'ecdba')
        res = yield gen.Task(self.client.sort, 'a', alpha=True)
        self.assertEqual(res, ['a', 'b', 'c', 'd', 'e'])

        yield gen.Task(self._make_list, 'a', '231')
        res = yield gen.Task(self.client.sort, 'a', store='sorted_values')
        self.assertEqual(res, 3)
        res = yield gen.Task(self.client.lrange, 'sorted_values', 0, -1)
        self.assertEqual(res, ['1', '2', '3'])

        yield gen.Task(self.client.set, 'user:1:username', 'zeus')
        yield gen.Task(self.client.set, 'user:2:username', 'titan')
        yield gen.Task(self.client.set, 'user:3:username', 'hermes')
        yield gen.Task(self.client.set, 'user:4:username', 'hercules')
        yield gen.Task(self.client.set, 'user:5:username', 'apollo')
        yield gen.Task(self.client.set, 'user:6:username', 'athena')
        yield gen.Task(self.client.set, 'user:7:username', 'hades')
        yield gen.Task(self.client.set, 'user:8:username', 'dionysus')
        yield gen.Task(self.client.set, 'user:1:favorite_drink', 'yuengling')
        yield gen.Task(self.client.set, 'user:2:favorite_drink', 'rum')
        yield gen.Task(self.client.set, 'user:3:favorite_drink', 'vodka')
        yield gen.Task(self.client.set, 'user:4:favorite_drink', 'milk')
        yield gen.Task(self.client.set, 'user:5:favorite_drink', 'pinot noir')
        yield gen.Task(self.client.set, 'user:6:favorite_drink', 'water')
        yield gen.Task(self.client.set, 'user:7:favorite_drink', 'gin')
        yield gen.Task(self.client.set, 'user:8:favorite_drink', 'apple juice')

        yield gen.Task(self._make_list, 'gods', '12345678')
        res = yield gen.Task(self.client.sort, 'gods',
                         start=2,
                         num=4,
                         by='user:*:username',
                         get='user:*:favorite_drink',
                         desc=True,
                         alpha=True,
                         store='sorted')
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.lrange, 'sorted', 0, -1)
        self.assertEqual(res, ['vodka', 'milk', 'gin', 'apple juice'])
        self.stop()

    @gen_test
    def test_bit_commands(self):
        key = 'TEST_BIT'
        res = yield gen.Task(self.client.setbit, key, 3, 1)
        self.assertFalse(res)
        res = yield gen.Task(self.client.getbit, key, 0)
        self.assertFalse(res)
        res = yield gen.Task(self.client.getbit, key, 3)
        self.assertTrue(res)
        res = yield gen.Task(self.client.setbit, key, 3, 0)
        self.assertTrue(res)
        res = yield gen.Task(self.client.getbit, key, 1)
        self.assertFalse(res)
        self.stop()

    @gen_test
    def test_bitcount(self):
        yield gen.Task(self.client.set, 'mykey', 'foobar')
        r1 = yield gen.Task(self.client.bitcount, 'mykey')
        self.assertEqual(r1, 26)
        r2 = yield gen.Task(self.client.bitcount, 'mykey', 0, 0)
        self.assertEqual(r2, 4)
        r3 = yield gen.Task(self.client.bitcount, 'mykey', 1, 1)
        self.assertEqual(r3, 6)

        self.stop()

    @gen_test
    def test_bitop(self):
        yield gen.Task(self.client.set, 'key1', 'foobar')
        yield gen.Task(self.client.set, 'key2', 'abcdef')
        yield gen.Task(self.client.bitop, 'AND', 'dest', 'key1', 'key2')
        res = yield gen.Task(self.client.get, 'dest')
        self.assertEqual(res, '`bc`ab')

        self.stop()

    @gen_test
    def test_sync_command_calls(self):
        # In general, one shouldn't execute redis commands this way.
        # Client methods SHOULD be invoked via gen.Task
        # or provided with the callback argument.
        # But it may happen in some cases, and definitely happens
        # in setUp method of this test.
        # So let's make sure a call without callback does not affect things.
        self.client.set('foo', 'bar')
        self.client.set('foo', 'bar3')
        self.client.set('foo', 'bar2')
        c = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(c, 'bar2')
        self.client.set('foo', 'bar3')
        c = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(c, 'bar3')
        self.stop()

    @gen_test
    def test_info(self):
        info = yield gen.Task(self.client.info)
        self.assertTrue(info)
        self.assertIn('redis_version', info)

        self.stop()

        #info_clients = yield gen.Task(self.client.info, section_name='clients')
        info_clients = yield gen.Task(self.client.info)
        self.assertTrue(info_clients)
        self.assertIn('connected_clients', info_clients)
        #self.assertNotIn('redis_version', info_clients)

    @gen_test
    def test_echo(self):
        v = '%08d' % random.randint(1, 1000)
        res = yield gen.Task(self.client.echo, v)
        self.assertEqual(res, v)

        self.stop()

    @gen_test
    def test_time(self):
        unixtime, mics = yield gen.Task(self.client.time)
        self.assertTrue(unixtime)
        self.assertTrue(mics)

        self.stop()

    @gen_test
    def test_getrange(self):
        yield gen.Task(self.client.set, 'mykey', 'This is a string')
        s = yield gen.Task(self.client.getrange, 'mykey', 0, 3)
        self.assertEqual(s, 'This')
        s = yield gen.Task(self.client.getrange, 'mykey', -3, -1)
        self.assertEqual(s, 'ing')
        s = yield gen.Task(self.client.getrange, 'mykey', 0, -1)
        self.assertEqual(s, 'This is a string')
        s = yield gen.Task(self.client.getrange, 'mykey', 10, 100)
        self.assertEqual(s, 'string')

        self.stop()

    @gen_test
    def test_object(self):
        r = self.client
        yield r.set('a', 'foo')
        res = yield r.object('refcount', 'a')
        self.assertTrue(isinstance(res, int))
        res = yield r.object('idletime', 'a')
        self.assertTrue(isinstance(res, int))
        res = yield r.object('encoding', 'a')
        self.assertEqual(res, b('embstr'))
        res = yield r.object('idletime', 'invalid-key')
        self.assertTrue(res is None)
        self.stop()

    @gen_test
    def test_persist(self):
        res = yield gen.Task(self.client.setex, 'foo', 5, 'bar')
        self.assertEqual(res, True)
        res = yield gen.Task(self.client.ttl, 'foo')
        self.assertEqual(res, 5)
        yield gen.Task(self.client.persist, 'foo')
        res = yield gen.Task(self.client.ttl, 'foo')
        # None
        self.assertEqual(res, -1L)
        res = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(res, 'bar')

        self.stop()

    @gen_test
    def test_scan(self):
        r = self.client
        yield r.set('a', 1)
        yield r.set('b', 2)
        yield r.set('c', 3)
        cursor, keys = yield r.scan()
        self.assertEqual(cursor, 0)
        self.assertEqual(set(keys), set([b('a'), b('b'), b('c')]))
        _, keys = yield r.scan(match='a')
        self.assertEqual(set(keys), set([b('a')]))

        self.stop()

    @gen_test
    def test_sscan(self):
        yield self.client.sadd('a', 1, 2, 3)
        cursor, members = yield self.client.sscan('a')
        self.assertEqual(cursor, 0)
        self.assertEqual(set(members), set([b('1'), b('2'), b('3')]))
        _, members = yield self.client.sscan('a', match=b('1'))
        self.assertEqual(set(members), set([b('1')]))

        self.stop()

    @gen_test
    def test_hscan(self):
        r = self.client
        yield r.hmset('a', {'a': 1, 'b': 2, 'c': 3})
        cursor, dic = yield r.hscan('a')
        self.assertEqual(cursor, 0)
        self.assertEqual(dic, {b('a'): b('1'), b('b'): b('2'), b('c'): b('3')})
        _, dic = yield r.hscan('a', match='a')
        self.assertEqual(dic, {b('a'): b('1')})

        self.stop()

    @gen_test
    def test_zscan(self):
        yield self.client.zadd('a', 1, 'a', 2, 'b', 3, 'c')
        cursor, pairs = yield self.client.zscan('a')
        self.assertEqual(cursor, 0)
        self.assertEqual(set(pairs), set([(b('a'), 1), (b('b'), 2), (b('c'), 3)]))
        _, pairs = yield self.client.zscan('a', match='a')
        self.assertEqual(set(pairs), set([(b('a'), 1)]))

        self.stop()

    @gen_test
    def test_v2_2(self):
        res = yield gen.Task(self.client.rpush, 'mylist', 1, 2, 3, 4, 5)
        self.assertEqual(res, 5)
        res = yield gen.Task(self.client.lrange, 'mylist', 0, -1)
        self.assertEqual(res, ['1', '2', '3', '4', '5'])

        res = yield gen.Task(self.client.lrange, 'mylist', 0, -1)
        self.assertEqual(res, ['1', '2', '3', '4', '5'])

        res = yield gen.Task(self.client.sadd, 'myset', 1, 2, 3, 4)
        self.assertEqual(res, 4)
        res = yield gen.Task(self.client.sismember, 'myset', 3)
        self.assertTrue(res)

        res = yield gen.Task(self.client.srem, 'myset', 2, 3)
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.scard, 'myset')
        self.assertEqual(res, 2)

        yield gen.Task(self.client.set, 'key1', 'Hello World')
        res = yield gen.Task(self.client.setrange, 'key1', 6, 'Redis')
        self.assertEqual(res, 11)
        res = yield gen.Task(self.client.get, 'key1')
        self.assertEqual(res, 'Hello Redis')

        res = yield gen.Task(self.client.strlen, 'key1')
        self.assertEqual(res, 11)

        res = yield gen.Task(self.client.zadd, 'myzset', 0, 'one', 1, 'two')
        self.assertEqual(res, 2)
        res = yield gen.Task(self.client.zrange, 'myzset', 0, -1, False)
        self.assertEqual(res, ['one', 'two'])
        res = yield gen.Task(self.client.zcount, 'myzset', 1, 5)
        self.assertEqual(res, 1)
        res = yield gen.Task(self.client.zcount, 'myzset', 0, 2)
        self.assertEqual(res, 2)

        self.stop()

    @gen_test
    def test_v2_6(self):
        vals = [1, 2, 3, 4]
        yield gen.Task(self.client.sadd, 'myset', *vals)
        res = yield gen.Task(self.client.srandmember, 'myset', 2)
        self.assertEqual(len(res), 2)
        self.assertIn(int(res[0]), vals)
        self.assertIn(int(res[1]), vals)

        self.stop()

if __name__ == '__main__':
    import unittest
    unittest.main()