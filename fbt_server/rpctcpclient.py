from tornado.ioloop import IOLoop
from tornado.iostream import IOStream
from tornado.concurrent import return_future
from tornado import gen
#from tcpclient import TCPClient
import functools
from struct import *
from json import dumps, loads
import socket
import time

__author__ = 'spark'

MESSAGE_BYTES = 4

'''
types:0 for error, 1 for fine
'''
def write(obj, types, error, result):
    msg = {}
    msg["type"] = types
    msg["error"] = error
    msg["result"] = result
    msg = dumps(msg)
    obj.set_header("Content-Type","application/json")
    obj.write(msg)
    obj.finish()

'''
0 for param error, 1 for db error
'''
def errorHandle(obj, num):
    print 'errorHandle'
    if num == 0:
        write(obj, 0, "400", {})
    elif num == 1:
        write(obj, 0, "sorry", {})

class TCPClient(object):
    def __init__(self, io_loop=None):
        self.io_loop = self.io_loop = io_loop or IOLoop.current()

        #self.shutdown = False
        self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.sock_fd.settimeout(0.5)
        self.stream = IOStream(self.sock_fd)
        #self.stream.set_close_callback(self.on_close)

    def connect(self, host, port):
        #self.stream.connect((self.host, self.port), self.send_message)
        self.stream.connect((host, port))
        return self.stream

    @return_future
    def connect_server(self, host, port, callback=None):
        self.stream.connect((host, port), callback=callback)

    def on_close(self):
        if self.shutdown:
            self.io_loop.stop()

    def set_shutdown(self):
        self.shutdown = True

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

@singleton
class RPCClient(object):
    """docstring for RPCClient"""
    def __init__(self):
        #super(RPCClient, self).__init__()
        self.id_handler_dict = dict()
        self._iostream = None
        self._wait_to_read_num = 0

    def check_iostream(self):
        if self._iostream is None:
            return False
        try:
            self._iostream._check_closed()
        except Exception, e:
            self._iostream = None
            return False
        else:
            return True

    def handle_iostream_close(self):
        self._iostream = None
        for handler in self.id_handler_dict.values():
            errorHandle(handler, 0)
        self.id_handler_dict.clear()
        self._wait_to_read_num = 0

    def set_iostream(self, iostream):
        self._iostream = iostream

    def is_iostream_setted(self):
        return self._iostream is None

    def read_message(self, data):
        bytes = unpack('!I', data)[0]
        #print 'bytes', bytes
        if self.check_iostream():
            self._iostream.read_bytes(bytes, self.handle_request)
        else:
            self.handle_iostream_close()
            #return

    def handle_request(self, data):
        info_dict = loads(data)
        #print info_dict
        rq_id = info_dict["id"]
        result = info_dict["res"]
        #print rq_id, result
        if rq_id in self.id_handler_dict:
            handler = self.id_handler_dict[rq_id]
            self.id_handler_dict.pop(rq_id)
            handler.finish(dumps(result))
            self._wait_to_read_num -= 1
        self.wait_result(False)

    def wait_result(self, need_add=True):
        if need_add :
            #print 'need_add', self._wait_to_read_num
            self._wait_to_read_num += 1
            if 1 == self._wait_to_read_num:
                if self.check_iostream():
                    self._iostream.read_bytes(MESSAGE_BYTES, self.read_message)
                else:
                    self.handle_iostream_close()
                    #return
        else :
            #print 'need_add_not', self._wait_to_read_num
            if self._wait_to_read_num >= 1:
                if self.check_iostream():
                    self._iostream.read_bytes(MESSAGE_BYTES, self.read_message)
                else:
                    self.handle_iostream_close()
                    #return

    def handle_connect_timeout(self, data):
        if self._iostream is None or self._iostream._connecting:
            self.handle_iostream_close()
        else:
            self._iostream.write(data, self.wait_result)

    def add_request(self, handler, method, **params):
        self.id_handler_dict[id(handler)] = handler
        info_dict = {"id": id(handler), "method": method, "params": params}
        req = dumps(info_dict)
        bytes = pack('!I', len(req))
        if self.check_iostream():
            if self._iostream._connecting:
                IOLoop.current().add_timeout(time.time() + 0.8, functools.partial(self.handle_connect_timeout, bytes + req))
            else :
                self._iostream.write(bytes + req, self.wait_result)
        else:
            self.handle_iostream_close()
            #return


@singleton
class FutureRPCClient(object):
    """docstring for RPCClient"""
    def __init__(self):
        #super(RPCClient, self).__init__()
        self.id_handler_dict = dict()
        self._iostream = None
        self._wait_to_read_num = 0

    def check_iostream(self):
        if self._iostream is None:
            return False
        try:
            self._iostream._check_closed()
        except Exception, e:
            self._iostream = None
            return False
        else:
            return True

    def handle_iostream_close(self):
        self._iostream = None
        for handler in self.id_handler_dict.values():
            errorHandle(handler, 0)
        self.id_handler_dict.clear()
        self._wait_to_read_num = 0

    def set_iostream(self, iostream):
        self._iostream = iostream

    @gen.coroutine
    def connect(self, host, port):
        tcp_client = TCPClient()
        yield tcp_client.connect_server(host, port)
        self.set_iostream(tcp_client.stream)

    def is_iostream_setted(self):
        return self._iostream is None

    def handle_request(self, data):
        info_dict = loads(data)
        #print info_dict
        rq_id = info_dict["id"]
        result = info_dict["res"]
        #print rq_id, result
        if rq_id in self.id_handler_dict:
            handler = self.id_handler_dict[rq_id]
            self.id_handler_dict.pop(rq_id)
            handler.finish(dumps(result))

    @gen.coroutine
    def wait_result(self):
        if self.check_iostream():
            data = yield return_future(self._iostream.read_bytes)(MESSAGE_BYTES)
            bytes = unpack('!I', data)[0]
            response = yield return_future(self._iostream.read_bytes)(bytes)
            self.handle_request(response)
        else:
            self.handle_iostream_close()

    @gen.coroutine
    def add_request(self, handler, method, **params):
        self.id_handler_dict[id(handler)] = handler
        info_dict = {"id": id(handler), "method": method, "params": params}
        req = dumps(info_dict)
        bytes = pack('!I', len(req))
        if self.check_iostream():
            yield return_future(self._iostream.write)(bytes + req)
            yield self.wait_result()
        else:
            self.handle_iostream_close()