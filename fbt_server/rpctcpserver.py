from tornado.tcpserver import TCPServer    
from tornado import gen
from struct import *
import functools
from json import dumps, loads
from tornado.concurrent import Future

__author__ = 'spark'

MESSAGE_BYTES = 4

def is_future(x):
    return isinstance(x, Future)

class Connection(object):    
    clients = set()    
    def __init__(self, RPC_TCP_server, stream, address):   
        Connection.clients.add(self)
        self._server = RPC_TCP_server
        self._stream = stream
        self._address = address
        self._stream.set_close_callback(self.on_close)
        self.read_message_bytes()
        
    def read_message_bytes(self):
        self._stream.read_bytes(MESSAGE_BYTES, self.read_message)    
    
    def read_message(self, data):
        bytes = unpack('!I', data)[0]
        #print 'bytes', bytes
        self._stream.read_bytes(bytes, self.handle_request) 

    def _done_callback(self, rq_id, f):
        #print '-----------', f.result()
        res = dumps({"id": rq_id, "res": f.result()})
        bytes = pack('!I', len(res))
        self.send_result(bytes+res)

    def handle_request(self, data):
        info_dict = loads(data)
        rq_id = info_dict["id"]
        method = info_dict["method"]
        params = info_dict["params"]
        future = self._server.dispatch(method, params)
        future.add_done_callback(functools.partial(
                self._done_callback, rq_id))
        self.read_message_bytes()

    def send_result(self, data):    
        self._stream.write(data)
            
    def on_close(self):
        print "A user has left the chat room.", self._address  
        #Connection.clients.remove(self) 

class RPCTCPServer(TCPServer):    
    def handle_stream(self, stream, address):
        print "New connection :", address, stream
        Connection(self, stream, address)
        print "connection num is:", len(Connection.clients)

    @gen.coroutine
    def dispatch(self, method_name, params):
        method = getattr(self, method_name, None)
        if not callable(method):
            # Not callable, so not a method
            raise gen.Return('method_not_found')
        try:
            response = method(**params)
        except Exception:
            raise gen.Return('internal_error')
        
        if is_future(response) :
            res = yield response
            raise gen.Return(res)
        else:
            # Synchronous result -- we call result manually.
            raise gen.Return(response)