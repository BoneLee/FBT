__author__ = 'bone-lee'

import constant
from singleton import singleton
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import tornadoredis
import logging
import redis

class RedisSubscribeClient(object):
    def __init__(self,msg_process_callback, channel=constant.CHANNEL_COIN_VARY):
        assert hasattr(msg_process_callback, '__call__')
        self.sub_client = tornadoredis.Client(host=constant.PUB_SUB_HOST, password=constant.PUB_SUB_PWD,port=constant.PUB_SUB_PORT)
        assert self.sub_client._io_loop != None
        self.msg_process_callback = msg_process_callback
        # import simplejson as json
        # self.msg_process_callback(json.dumps({1:2}))
        # print "msg sended"
        self.channel = channel
        # self.subscribe()
        self.sub_client._io_loop.add_future(self.subscribe(), lambda future: self.sub_client.listen(self.on_redis_message))

    @tornado.gen.coroutine
    def subscribe(self):
        try:
            self.sub_client.connect()
        except tornadoredis.ConnectionError as e:
            logging.error("error in connecting to redis sub client. maybe the server not open")
            raise tornado.gen.Return(False)
        yield tornado.gen.Task(self.sub_client.subscribe, self.channel)
        raise tornado.gen.Return(True)
        # self.sub_client.listen(self.on_redis_message)

    def on_redis_message(self, message):
        # print "receive msg:",message
        # logging.info("Redis message received: "+str(message.body))
        kind, body = message.kind, message.body
        if kind == 'message':
            self.msg_process_callback(body)
        if kind == 'disconnect':
            self.close()

    def close(self):
        if self.sub_client.subscribed:
            self.sub_client.unsubscribe(self.channel)
            self.sub_client.disconnect()

@singleton
class RedisPubClient(object):
    def __init__(self):
        self._pub_client = redis.StrictRedis(host=constant.PUB_SUB_HOST, password=constant.PUB_SUB_PWD,port=constant.PUB_SUB_PORT)
        #tornadoredis.Client(password="123-fbt-pub-sub-!@#",port=6380)
        # assert self._pub_client._io_loop!=None

    def publish(self, msg = "hello,world", channel = constant.CHANNEL_COIN_VARY):
        # print "msg:",msg
        # logging.info("Redis message send: "+msg)
        self._pub_client.publish(channel, msg)
