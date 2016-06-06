import sys
from tornado import gen
import redis
from tornado.testing import gen_test, AsyncTestCase
from tornado.stack_context import ExceptionStackContext
from redis._compat import (unichr, u, b, ascii_letters, iteritems, iterkeys,
                           itervalues)

sys.path.append('..')
from asyncRedis import AsyncStrictRedis

def f(func, *args, **kwargs):
    return func(*args, **kwargs)
gen.Task = f

class PipelineTestCase(AsyncTestCase):
    def setUp(self):
        super(PipelineTestCase, self).setUp()
        self.client = AsyncStrictRedis()
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        yield self.client.flushdb()

    @gen_test
    def test_pipe_simple(self):
        pipe = self.client.pipeline()
        pipe.set('foo', '123')
        pipe.set('bar', '456')
        pipe.mget(('foo', 'bar'))

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [True, True, ['123', '456', ]])
        self.stop()

    @gen_test
    def test_pipe_multi(self):
        pipe = self.client.pipeline(transaction=True)
        pipe.set('foo', '123')
        pipe.set('bar', '456')
        pipe.mget(('foo', 'bar'))

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [True, True, ['123', '456', ]])
        self.stop()

    @gen_test
    def test_pipe_error(self):
        pipe = self.client.pipeline()
        pipe.sadd('foo', 1)
        pipe.sadd('foo', 2)
        #pipe.rpop('foo')

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [1, 1])
        #self.assertIsInstance(res[2], ResponseError)
        self.stop()

    @gen_test
    def test_two_pipes(self):
        pipe = self.client.pipeline()

        pipe.rpush('foo', '1')
        pipe.rpush('foo', '2')
        pipe.lrange('foo', 0, -1)
        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [True, 2, ['1', '2']])

        pipe.sadd('bar', '3')
        pipe.sadd('bar', '4')
        pipe.smembers('bar')
        pipe.scard('bar')
        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [1, 1, set(['3', '4']), 2])

        self.stop()

    @gen_test
    def test_mix_with_pipe(self):
        pipe = self.client.pipeline()

        res = yield gen.Task(self.client.set, 'foo', '123')
        self.assertTrue(res)
        yield gen.Task(self.client.hmset, 'bar', {'zar': 'gza'},)

        pipe.get('foo')
        res = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(res, '123')

        pipe.hgetall('bar')

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, ['123', {'zar': 'gza'}])
        self.stop()

    @gen_test
    def test_mix_with_pipe_multi(self):
        pipe = self.client.pipeline(transaction=True)

        res = yield gen.Task(self.client.set, 'foo', '123')
        self.assertTrue(res)
        yield gen.Task(self.client.hmset, 'bar', {'zar': 'gza'},)

        pipe.get('foo')
        res = yield gen.Task(self.client.get, 'foo')
        self.assertEqual(res, '123')

        pipe.hgetall('bar')

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, ['123', {'zar': 'gza'}])

        self.stop()

    @gen_test
    def test_pipeline_no_transaction(self):
        with self.client.pipeline(transaction=False) as pipe:
            pipe.set('a', 'a1').set('b', 'b1').set('c', 'c1')
            res = yield pipe.execute()
            self.assertEqual(res, [True, True, True])
            res = yield self.client.get('a')
            self.assertEqual(res, b('a1'))
            res = yield self.client.get('b')
            self.assertEqual(res, b('b1'))
            res = yield self.client.get('c')
            self.assertEqual(res, b('c1'))

    @gen_test
    def test_pipeline_no_transaction_watch(self):
        yield self.client.set('a', 0)
        with self.client.pipeline(transaction=False) as pipe:
            yield pipe.watch('a')
            a = yield pipe.get('a')

            pipe.multi()
            pipe.set('a', int(a) + 1)
            res = yield pipe.execute()
            self.assertEqual(res, [True])

    @gen_test
    def test_pipeline_no_transaction_watch_failure(self):
        def handle_exception(typ, value, tb):
            self.stop()
            return True
        yield self.client.set('a', 0)

        with self.client.pipeline(transaction=False) as pipe:
            yield pipe.watch('a')
            a = yield pipe.get('a')

            yield self.client.set('a', 'bad')

            pipe.multi()
            pipe.set('a', int(a) + 1)

            try:
                yield pipe.execute()
            except redis.exceptions.WatchError as e:
                pass

            a = yield self.client.get('a')
            self.assertEqual(a, b('bad'))

    @gen_test
    def test_watch_succeed(self):
        yield self.client.set('a', 1)
        yield self.client.set('b', 2)

        with self.client.pipeline() as pipe:
            yield pipe.watch('a', 'b')
            self.assertTrue(pipe.watching)
            a_value = yield pipe.get('a')
            b_value = yield pipe.get('b')
            self.assertEqual(a_value, b('1'))
            self.assertEqual(b_value, b('2'))
            pipe.multi()

            pipe.set('c', 3)
            res = yield pipe.execute()
            self.assertEqual(res, [True])
            self.assertFalse(pipe.watching)

    @gen_test
    def test_watch_failure(self):
        yield self.client.set('a', 1)
        yield self.client.set('b', 2)
        self.failure = None
        def handle_exception(typ, value, tb):
            self.failure = value
            self.stop()
            return True
        with self.client.pipeline() as pipe:
            yield pipe.watch('a', 'b')
            yield self.client.set('b', 3)

            pipe.multi()
            pipe.get('b')
            try:
                yield pipe.execute()
            except redis.exceptions.WatchError as e:
                pass
            self.assertFalse(pipe.watching)
            '''
            with ExceptionStackContext(handle_exception):
                yield pipe.execute()
            if self.failure:
                raise self.failure
            self.assertFalse(pipe.watching)
            '''

    @gen_test
    def test_unwatch(self):
        yield self.client.set('a', 1)
        yield self.client.set('b', 2)

        with self.client.pipeline() as pipe:
            yield pipe.watch('a', 'b')
            yield self.client.set('b', 3)
            yield pipe.unwatch()
            self.assertFalse(pipe.watching)
            pipe.get('a')
            res = yield pipe.execute()
            self.assertEqual(res, [b('1')])

    '''
    @gen_test
    def test_transaction_callable(self):
        yield self.client.set('a', 1)
        yield self.client.set('b', 2)
        has_run = []

        def my_transaction(pipe):
            a_value = yield pipe.get('a')
            self.assertTrue(a_value in (b('1'), b('2')))
            b_value = yield pipe.get('b')
            self.assertTrue(b_value == b('2'))

            # silly run-once code... incr's "a" so WatchError should be raised
            # forcing this all to run again. this should incr "a" once to "2"
            if not has_run:
                yield self.client.incr('a')
                has_run.append('it has')

            pipe.multi()
            pipe.set('c', int(a_value) + int(b_value))

        result = yield self.client.transaction(my_transaction, 'a', 'b')
        self.assertEqual(result, [True])
        res = yield self.client.get('c')
        self.assertEqual(res, b('4'))
    '''
    @gen_test
    def test_exec_error_in_no_transaction_pipeline(self):
        yield self.client.set('a', 1)
        with self.client.pipeline(transaction=False) as pipe:
            pipe.llen('a')
            pipe.expire('a', 100)

            try :
                yield pipe.execute()
            except redis.ResponseError as ex:
                self.assertTrue(unicode(ex).startswith('Command # 1 (LLEN a) of pipeline caused error'))

        res = yield self.client.get('a')
        self.assertEqual(res, b('1'))

    @gen_test
    def test_exec_error_in_no_transaction_pipeline_unicode_command(self):
        key = unichr(3456) + u('abcd') + unichr(3421)
        yield self.client.set(key, 1)
        with self.client.pipeline(transaction=False) as pipe:
            pipe.llen(key)
            pipe.expire(key, 100)

            expected = unicode('Command # 1 (LLEN %s) of pipeline caused '
                               'error: ') % key
            try :
                yield pipe.execute()
            except redis.ResponseError as ex:
                self.assertTrue(unicode(ex).startswith(expected))

        res = yield self.client.get(key)
        self.assertEqual(res, b('1'))

    @gen_test
    def test_pipe_zsets(self):
        pipe = self.client.pipeline(transaction=True)

        pipe.zadd('foo', 1, 'a')
        pipe.zadd('foo', 2, 'b')
        pipe.zscore('foo', 'a')
        pipe.zscore('foo', 'b')
        pipe.zrank('foo', 'a',)
        pipe.zrank('foo', 'b',)

        pipe.zrange('foo', 0, -1, withscores=True)
        pipe.zrange('foo', 0, -1, withscores=False)

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [
            1, 1,
            1.0, 2.0,
            0, 1,
            [('a', 1.0), ('b', 2.0)],
            ['a', 'b'],
        ])
        self.stop()

    @gen_test
    def test_pipe_zsets2(self):
        pipe = self.client.pipeline(transaction=False)

        pipe.zadd('foo', 1, 'a')
        pipe.zadd('foo', 2, 'b')
        pipe.zscore('foo', 'a')
        pipe.zscore('foo', 'b')
        pipe.zrank('foo', 'a',)
        pipe.zrank('foo', 'b',)

        pipe.zrange('foo', 0, -1, withscores=True)
        pipe.zrange('foo', 0, -1, withscores=False)

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [
            1, 1,
            1.0, 2.0,
            0, 1,
            [('a', 1.0), ('b', 2.0)],
            ['a', 'b'],
        ])
        self.stop()

    @gen_test
    def test_pipe_hsets(self):
        pipe = self.client.pipeline(transaction=True)
        pipe.hset('foo', 'bar', 'aaa')
        pipe.hset('foo', 'zar', 'bbb')
        pipe.hgetall('foo')

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [
            True,
            True,
            {'bar': 'aaa', 'zar': 'bbb'}
        ])
        self.stop()

    @gen_test
    def test_pipe_hsets2(self):
        pipe = self.client.pipeline(transaction=False)
        pipe.hset('foo', 'bar', 'aaa')
        pipe.hset('foo', 'zar', 'bbb')
        pipe.hgetall('foo')

        res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [
            True,
            True,
            {'bar': 'aaa', 'zar': 'bbb'}
        ])
        self.stop()

    @gen_test
    def test_with(self):
        with self.client.pipeline() as pipe:
            pipe.set('foo', '123')
            pipe.set('bar', '456')
            pipe.mget(('foo', 'bar'))

            res = yield gen.Task(pipe.execute)
        self.assertEqual(res, [True, True, ['123', '456', ]])
        self.stop()

if __name__ == '__main__':
    import unittest
    unittest.main()