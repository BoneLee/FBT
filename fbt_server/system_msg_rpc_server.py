from rpctcpserver import RPCTCPServer
from tornado import gen

# TODO move to constant
RPC_HOST = "127.0.0.1"
RPC_PORT = 8888


class SystemMessageRPCServer(RPCTCPServer):
    def __init__(self, msg_man):
        super(SystemMessageRPCServer, self).__init__()
        self.msg_man = msg_man

    def send_system_msg(self, user_to, message):
        self.msg_man.new_system_message(message, user_to)
