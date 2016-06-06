import sys
import functools
import socket

from motor import MotorSocket, motor_sock_method, callback_type_error
from motor import callback_type_error
from redis.connection import Connection, ConnectionPool
from redis.client import StrictRedis, BasePipeline
from tornado import ioloop, iostream, gen, stack_context
from tornado.concurrent import Future, TracebackFuture
import greenlet
import inspect

__version__ = '0.0.1'
VERSION = tuple(map(int, __version__.split('.')))