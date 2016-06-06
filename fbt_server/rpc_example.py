# -*- coding: utf-8 -*-
__author__ = 'spark'

import motor
from rpctcpserver import RPCTCPServer
from rpctcpclient import RPCClient, TCPClient, FutureRPCClient
from tornado import gen
from tornado.ioloop import IOLoop 
import tornado.web

class RPCServerHandler(RPCTCPServer):
    db = motor.MotorClient().test

    def add(self, a, b):
        a = int(a)
        b = int(b)
        return a + b

    @gen.coroutine
    def find(self, table_name):
        res = None
        if table_name:
            res = yield self.db[table_name].find_one({}, {'_id': 0})
        raise gen.Return(res)


class RPCClientHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    #@gen.coroutine
    def get(self, func_name):
        if func_name:
            args = dict()
            if func_name == 'add':
                for arg in ("a", "b"):
                    val = self.get_argument(arg, None)
                    if val :
                        args[arg] = val
            elif func_name == 'find':
                args = {'table_name': self.get_argument('table_name', '')}
            RPC_client = RPCClient()
            if RPC_client.is_iostream_setted():
                tcp_client = TCPClient()
                RPC_iostream = tcp_client.connect('127.0.0.1', 8890)
                RPC_client.set_iostream(RPC_iostream)
            RPC_client.add_request(self, func_name, **args)


class FutureRPCClientHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, func_name):
        if func_name:
            args = dict()
            if func_name == 'add':
                for arg in ("a", "b"):
                    val = self.get_argument(arg, None)
                    if val :
                        args[arg] = val
            elif func_name == 'find':
                args = {'table_name': self.get_argument('table_name', '')}
            RPC_client = FutureRPCClient()
            yield RPC_client.connect('127.0.0.1', 8890)
            yield RPC_client.add_request(self, func_name, **args)


if __name__ == "__main__":
    server_app = tornado.web.Application([
            (r'/f/(.*)', FutureRPCClientHandler),
            (r'/(.*)', RPCClientHandler)
            ])

    print 'Listening on http://localhost:8889'
    server_app.listen(8889)
    server = RPCServerHandler()    
    server.listen(8890)   
    IOLoop.instance().start()
