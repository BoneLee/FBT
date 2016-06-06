from tornado import gen
import tornado.ioloop
import tornado.gen
import tornadoredis
import logging
from redis_sub_helper import RedisSubHelper

class RedisSubClient(object):
    def __init__(self,channel, host, port, passwd = None):
        self.sub_client = tornadoredis.Client(password=passwd, port = port, host = host)
        self.channel = channel
        # self.subscribe()
        self.sub_client._io_loop.add_future(self.subscribe(), lambda future: self.sub_client.listen(self.on_redis_message))

    @gen.coroutine
    def subscribe(self):
        self.sub_client.connect()
        yield tornado.gen.Task(self.sub_client.subscribe, self.channel)
        # self.sub_client.listen(self.on_redis_message)

    def msgHandler(self, msg) :
        raise NotImplementedError()

    def on_redis_message(self, message):
        logging.info("Redis message received: " + str(message.body))
        kind, body = message.kind, message.body
        # print body
        if kind == 'message':
            if RedisSubHelper().is_located_myself(message.body):
                self.msgHandler(body)
        elif kind == 'disconnect':
            self.close()

    def close(self):
        if self.sub_client.subscribed:
            self.sub_client.unsubscribe(self.channel)
            self.sub_client.disconnect()