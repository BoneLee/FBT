# -*- coding: UTF-8 -*-
"""
https://pypi.python.org/pypi/redis
https://github.com/andymccurdy/redis-py/blob/master/redis/connection.py

You can create your own Connection subclasses as well. This may be useful if you want to control the socket behavior within an async framework. 
To instantiate a client class using your own connection, you need to create a connection pool, passing your class to the connection_class argument. 
Other keyword parameters you pass to the pool will be passed to the class specified during initialization.
>>> pool = redis.ConnectionPool(connection_class=YourConnectionClass,
                                your_arg='...', ...)

class ConnectionPool(object):
    "Generic connection pool"

    def __init__(self, connection_class=Connection, max_connections=None,
                 **connection_kwargs):
        Create a connection pool. If max_connections is set, then this
        object raises redis.ConnectionError when the pool's limit is reached.

        By default, TCP connections are created connection_class is specified.
        Use redis.UnixDomainSocketConnection for unix sockets.

        Any additional keyword arguments are passed to the constructor of
        connection_class.

class Sentinel(object):
    Redis Sentinel cluster client

    >>> from redis.sentinel import Sentinel
    >>> sentinel = Sentinel([('localhost', 26379)], socket_timeout=0.1)
    >>> master = sentinel.master_for('mymaster', socket_timeout=0.1)
    >>> master.set('foo', 'bar')
    >>> slave = sentinel.slave_for('mymaster', socket_timeout=0.1)
    >>> slave.get('foo')
    'bar'

    ``sentinels`` is a list of sentinel nodes. Each node is represented by
    a pair (hostname, port).

    ``min_other_sentinels`` defined a minimum number of peers for a sentinel.
    When querying a sentinel, if it doesn't meet this threshold, responses
    from that sentinel won't be considered valid.

    ``sentinel_kwargs`` is a dictionary of connection arguments used when
    connecting to sentinel instances. Any argument that can be passed to
    a normal Redis connection can be specified here. If ``sentinel_kwargs`` is
    not specified, any socket_timeout and socket_keepalive options specified
    in ``connection_kwargs`` will be used.

    ``connection_kwargs`` are keyword arguments that will be used when
    establishing a connection to a Redis server.

    def __init__(self, sentinels, min_other_sentinels=0, sentinel_kwargs=None,
                 **connection_kwargs):
        # if sentinel_kwargs isn't defined, use the socket_* options from
        # connection_kwargs

    def master_for(self, service_name, redis_class=StrictRedis,
                   connection_pool_class=SentinelConnectionPool, **kwargs):
        Returns a redis client instance for the ``service_name`` master.

        A SentinelConnectionPool class is used to retrive the master's
        address before establishing a new connection.

        NOTE: If the master's address has changed, any cached connections to
        the old master are closed.

        By default clients will be a redis.StrictRedis instance. Specify a
        different class to the ``redis_class`` argument if you desire
        something different.

        The ``connection_pool_class`` specifies the connection pool to use.
        The SentinelConnectionPool will be used by default.

        All other keyword arguments are merged with any connection_kwargs
        passed to this class and passed to the connection pool as keyword
        arguments to be used to initialize Redis connections.

    def slave_for(self, service_name, redis_class=StrictRedis,
                  connection_pool_class=SentinelConnectionPool, **kwargs):
        Returns redis client instance for the ``service_name`` slave(s).

        A SentinelConnectionPool class is used to retrive the slave's
        address before establishing a new connection.

        By default clients will be a redis.StrictRedis instance. Specify a
        different class to the ``redis_class`` argument if you desire
        something different.

        The ``connection_pool_class`` specifies the connection pool to use.
        The SentinelConnectionPool will be used by default.

        All other keyword arguments are merged with any connection_kwargs
        passed to this class and passed to the connection pool as keyword
        arguments to be used to initialize Redis connections.

        return redis_class(connection_pool=connection_pool_class(
            service_name, self, **connection_kwargs))
"""

"""
test on redis-py 2.10.3 and tornado 3.2
"""
__author__ = 'spark'

import sys
import functools
import socket
import time

from motor import MotorSocket, motor_sock_method, callback_type_error
from redis.connection import Connection, ConnectionPool
from redis.client import StrictRedis, BasePipeline
from tornado import ioloop, gen, stack_context
from tornado.iostream import IOStream
from tornado.concurrent import Future, TracebackFuture
from redis._compat import iteritems
import greenlet
import inspect

def motor_sock_method_for_recv_into(method):
    """Wrap a MotorSocket method to pause the current greenlet and arrange
       for the greenlet to be resumed when non-blocking I/O has completed.
    """
    @functools.wraps(method)
    def _motor_sock_method(self, *args, **kwargs):
        child_gr = greenlet.getcurrent()
        main = child_gr.parent
        assert main is not None, "Should be on child greenlet"

        timeout_object = None

        if self.timeout:
            def timeout_err():
                # Running on the main greenlet. If a timeout error is thrown,
                # we raise the exception on the child greenlet. Closing the
                # IOStream removes callback() from the IOLoop so it isn't
                # called.
                self.stream.set_close_callback(None)
                self.stream.close()
                child_gr.throw(socket.timeout("timed out"))

            timeout_object = self.stream.io_loop.add_timeout(
                time.time() + self.timeout, timeout_err)

        # This is run by IOLoop on the main greenlet when operation
        # completes; switch back to child to continue processing
        def callback(result=None):
            self.stream.set_close_callback(None)
            if timeout_object:
                self.stream.io_loop.remove_timeout(timeout_object)
            buffer = args[0]
            #print '>>>>', result, 'result<<<'
            if len(result) >= len(buffer):
                buffer[:] = result
            else:
                buffer[:len(result)] = result
            child_gr.switch(len(result))

        # Run on main greenlet
        def closed():
            if timeout_object:
                self.stream.io_loop.remove_timeout(timeout_object)

            # The child greenlet might have died, e.g.:
            # - An operation raised an error within PyMongo
            # - PyMongo closed the MotorSocket in response
            # - MotorSocket.close() closed the IOStream
            # - IOStream scheduled this closed() function on the loop
            # - PyMongo operation completed (with or without error) and
            #       its greenlet terminated
            # - IOLoop runs this function
            if not child_gr.dead:
                child_gr.throw(socket.error("error"))

        self.stream.set_close_callback(closed)

        try:
            kwargs['callback'] = callback

            # method is MotorSocket.open(), recv(), etc. method() begins a
            # non-blocking operation on an IOStream and arranges for
            # callback() to be executed on the main greenlet once the
            # operation has completed.
            method(self, *args, **kwargs)

            # Pause child greenlet until resumed by main greenlet, which
            # will pass the result of the socket operation (data for recv,
            # number of bytes written for sendall) to us.
            return main.switch()
        except socket.error:
            raise
        except IOError as e:
            # If IOStream raises generic IOError (e.g., if operation
            # attempted on closed IOStream), then substitute socket.error,
            # since socket.error is what PyMongo's built to handle. For
            # example, PyMongo will catch socket.error, close the socket,
            # and raise AutoReconnect.
            raise socket.error(str(e))

    return _motor_sock_method

class ModIOStream(IOStream):
    def read_bytes(self, num_bytes, callback=None, streaming_callback=None, partial=False):
        self._read_partial = partial
        super(ModIOStream, self).read_bytes(num_bytes, callback, streaming_callback)

    def _read_from_buffer(self):
        res = super(ModIOStream, self)._read_from_buffer()
        if not res and self._streaming_callback is not None and self._read_partial:
            self._read_callback = None
            self._read_partial = False
            self._read_bytes = None
            #self._streaming_callback = None
            return True
        else:
            return res

class ModSSLIOStream(IOStream):
    def read_bytes(self, num_bytes, callback=None, streaming_callback=None, partial=False):
        self._read_partial = partial
        super(ModSSLIOStream, self).read_bytes(num_bytes, callback, streaming_callback)

    def _read_from_buffer(self):
        res = super(ModSSLIOStream, self)._read_from_buffer()
        if not res and self._streaming_callback is not None and self._read_buffer_size and self._read_partial:
            self._read_callback = None
            self._streaming_callback = None
            self._read_bytes = None
            self._read_partial = False
            return True
        else:
            return res

def getcallargs(func, *positional, **named):
    """
    Simple implementation of inspect.getcallargs function in
    the Python 2.7 standard library.

    Takes a function and the position and keyword arguments and
    returns a dictionary with the appropriate named arguments.
    Raises an exception if invalid arguments are passed.
    """
    args, varargs, varkw, defaults = inspect.getargspec(func)
    # pop self
    args.pop(0)
    final_kwargs = {}

    if named:
        final_kwargs.update(named)
    else:
        for i, value in enumerate(positional):
            arg_key = None
            try:
                arg_key = args[i]
            except IndexError:
                if not varargs:
                    raise TypeError("Too many positional arguments")
            if arg_key:
                final_kwargs[arg_key] = value
    if defaults:
        for kwarg, default in zip(args[-len(defaults):], defaults):
            final_kwargs.setdefault(kwarg, default)
    return final_kwargs

class AsyncSocket(MotorSocket):
    """Replace socket with a class that yields from the current greenlet, if
    we're on a child greenlet, when making blocking calls, and uses Tornado
    IOLoop to schedule child greenlet for resumption when I/O is ready.

    We only implement those socket methods actually used by pymongo.
    """
    def __init__(self, sock, io_loop, use_ssl,
            certfile, keyfile, ca_certs, cert_reqs):
        super(AsyncSocket, self).__init__(sock, io_loop, use_ssl, certfile, keyfile, ca_certs, cert_reqs)
        if self.use_ssl:
                        # In Python 3, Tornado's ssl_options_to_context fails if
            # any options are None.
            ssl_options = {}
            if certfile:
                ssl_options['certfile'] = certfile

            if keyfile:
                ssl_options['keyfile'] = keyfile

            if ca_certs:
                ssl_options['ca_certs'] = ca_certs

            if cert_reqs:
                ssl_options['cert_reqs'] = cert_reqs
            self.stream = ModSSLIOStream(
                sock, ssl_options=ssl_options, io_loop=io_loop)
        else:
            self.stream = ModIOStream(sock, io_loop=io_loop)

    @motor_sock_method
    def recv(self, num_bytes, callback):
        '''
        for tornado 4.0
        self.stream.read_bytes(num_bytes, callback, partial=True)
        too ineffiently
        self.stream.read_until_regex("\r\n", callback)
        for tornado 3.2, it's hard to hack
        '''
        def cb(arg):
            pass
        self.stream.read_bytes(num_bytes, cb, callback, True)

    @motor_sock_method_for_recv_into
    def recv_into(self, buffer, callback):
        def cb(arg):
            pass
        #print len(buffer), 'len'
        self.stream.read_bytes(len(buffer), cb, callback, True)

# mimic Motor
class DelegateBase(object):
    def __eq__(self, other):
        if (isinstance(other, self.__class__)
                and hasattr(self, 'delegate')
                and hasattr(other, 'delegate')):
            return self.delegate == other.delegate
        return NotImplemented

    def __init__(self, delegate):
        self.delegate = delegate

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.delegate)

def asynchronize(sync_method, doc=None):
    """Decorate `sync_method` so it accepts a callback or returns a Future.

    The method runs on a child greenlet and calls the callback or resolves
    the Future when the greenlet completes.

    :Parameters:
     - `motor_class`:       Motor class being created, e.g. MotorClient.
     - `sync_method`:       Unbound method of pymongo Collection, Database,
                            MongoClient, or Cursor
     - `doc`:               Optionally override sync_method's docstring
     创建类的异步函数！好奇怪的用法，返回一个用sync_method函数信息装饰的类成员函数
    """
    @functools.wraps(sync_method)
    def method(self, *args, **kwargs):
        #loop = self.get_io_loop()
        loop = ioloop.IOLoop.current()
        callback = kwargs.pop('callback', None)

        if callback:
            if not callable(callback):
                raise callback_type_error
            future = None
        else:
            future = TracebackFuture()

        def call_method():
            # Runs on child greenlet.
            try:
                result = sync_method(self, *args, **kwargs)    #   用fun传对象调用方法
                if callback:
                    # Schedule callback(result, None) on main greenlet.
                    loop.add_callback(functools.partial(
                        callback, result, None))
                else:
                    # Schedule future to be resolved on main greenlet.
                    loop.add_callback(functools.partial(
                        future.set_result, result))
            except Exception as e:
                if callback:
                    loop.add_callback(functools.partial(
                        callback, None, e))
                else:
                    loop.add_callback(functools.partial(
                        future.set_exc_info, sys.exc_info()))

        # Start running the operation on a greenlet.
        greenlet.greenlet(call_method).switch()
        return future

    # This is for the benefit of motor_extensions.py, which needs this info to
    # generate documentation with Sphinx.
    name = sync_method.__name__
    if doc is not None:
        method.__doc__ = doc

    return method

class AsyncConnection(Connection):
    "Manages TCP communication to and from a Redis server"
    description_format = "Connection<host=%(host)s,port=%(port)s,db=%(db)s>"

    def _connect(self):
        "Create a TCP socket connection"
        # we want to mimic what socket.create_connection does to support
        # ipv4/ipv6, but we want to set options prior to calling
        # socket.connect()
        err = None
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            family, socktype, proto, canonname, socket_address = res
            sock = None
            try:
                sock = socket.socket(family, socktype, proto)
                # TCP_NODELAY
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                # TCP_KEEPALIVE
                if self.socket_keepalive:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    for k, v in iteritems(self.socket_keepalive_options):
                        sock.setsockopt(socket.SOL_TCP, k, v)
                motor_sock = AsyncSocket(sock, ioloop.IOLoop.current(), None, None, None, None, None)
                # set the socket_connect_timeout before we connect
                motor_sock.settimeout(self.socket_connect_timeout)

                # connect
                motor_sock.connect(socket_address)

                # set the socket_timeout now that we're connected
                motor_sock.settimeout(self.socket_timeout)
                return motor_sock

            except socket.error as _:
                err = _
                if sock is not None:
                    sock.close()

        if err is not None:
            raise err
        raise socket.error("socket.getaddrinfo returned an empty list")

    def disconnect(self):
        "Disconnects from the Redis server"
        self._parser.on_disconnect()
        if self._sock is None:
            return
        try:
            self._sock.close()
        except socket.error:
            pass
        self._sock = None

    """
    ONLY used by pubsub, not in my concern
    def can_read(self, timeout=0):
        "Poll the socket to see if there's data that can be read."
        sock = self._sock
        if not sock:
            self.connect()
            sock = self._sock
        return self._parser.can_read() or \
            bool(select([sock], [], [], timeout)[0])
    """

class AsyncConnectionPool(DelegateBase):
    __delegate_class__ = ConnectionPool
    def __init__(self, *args, **kwargs):
        if 'connection_class' not in kwargs:
            kwargs['connection_class'] = AsyncConnection
        delegate = self.__delegate_class__(*args, **kwargs)
        super(AsyncConnectionPool, self).__init__(delegate)

    def __getattr__(self, name):
        return getattr(self.delegate, name)


class AsyncStrictRedis(StrictRedis):
    def __init__(self, *args, **kwargs):
        all_kwargs = getcallargs(StrictRedis.__init__, *args, **kwargs)
        if not all_kwargs['connection_pool']:
            k_list = (['db','password','socket_timeout','encoding','encoding_errors','decode_responses',
                           'retry_on_timeout','host','port','socket_connect_timeout','socket_keepalive',
                           'socket_keepalive_options'])
            _kwargs = {}
            for k in k_list:
                if k in all_kwargs:
                    _kwargs[k] = all_kwargs[k]
            kwargs['connection_pool'] = AsyncConnectionPool(**_kwargs)
        super(AsyncStrictRedis, self).__init__(*args, **kwargs)

    def pipeline(self, transaction=True, shard_hint=None):
        """
        Return a new pipeline object that can queue multiple commands for
        later execution. ``transaction`` indicates whether all commands
        should be executed atomically. Apart from making a group of operations
        atomic, pipelines are useful for reducing the back-and-forth overhead
        between the client and server.
        """
        return AsyncStrictPipeline(
            self.connection_pool,
            self.response_callbacks,
            transaction,
            shard_hint)

    execute_command = asynchronize(StrictRedis.execute_command)

class AsyncStrictPipeline(BasePipeline, AsyncStrictRedis):
    "Pipeline for the AsyncStrictRedis class"
    execute = asynchronize(BasePipeline.execute)
    immediate_execute_command = asynchronize(BasePipeline.immediate_execute_command)
'''
redis.sentinel.__dict__['StrictRedis'] = AsyncStrictRedis
redis.sentinel.__dict__['ConnectionPool'] = AsyncConnectionPool
redis.sentinel.__dict__['Connection'] = AsyncConnection

class AsyncSentinel(redis.sentinel.Sentinel):
    pass
'''
