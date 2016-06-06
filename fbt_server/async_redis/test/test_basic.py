#from __future__ import absolute_import
import sys
from tornado.testing import gen_test, AsyncTestCase
from tornado import gen
from redis._compat import (unichr, u, b, ascii_letters, iteritems, iterkeys, itervalues)

sys.path.append('..')
from asyncRedis import AsyncStrictRedis

class AsyncRedisTestBasic(AsyncTestCase):
    def setUp(self):
        super(AsyncRedisTestBasic, self).setUp()
        self.r = AsyncStrictRedis()
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        yield self.r.flushdb()

    @gen_test
    def test_get_and_set(self):
        # get and set can't be tested independently of each other
        r = self.r
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

    @gen_test
    def test_bitcount(self):
        r = self.r
        yield r.setbit('a', 5, True)
        res = yield r.bitcount('a')
        self.assertEqual(res, 1)
        yield r.setbit('a', 6, True)
        res = yield r.bitcount('a')
        self.assertEqual(res, 2)
        yield r.setbit('a', 5, False)
        res = yield r.bitcount('a')
        self.assertEqual(res, 1)
        yield r.setbit('a', 9, True)
        yield r.setbit('a', 17, True)
        yield r.setbit('a', 25, True)
        yield r.setbit('a', 33, True)
        res = yield r.bitcount('a')
        self.assertEqual(res, 5)
        res = yield r.bitcount('a', 0, -1)
        self.assertEqual(res, 5)
        res = yield r.bitcount('a', 2, 3)
        self.assertEqual(res, 2)
        res = yield r.bitcount('a', 2, -1)
        self.assertEqual(res, 3)
        res = yield r.bitcount('a', -2, -1)
        self.assertEqual(res, 2)
        res = yield r.bitcount('a', 1, 1)
        self.assertEqual(res, 1)

if __name__ == '__main__':
    import unittest
    unittest.main()
