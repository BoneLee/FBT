# -*- coding: utf-8 -*-

import json

import tornado.ioloop
import tornado.web
from tornado.gen import coroutine

from tornadoes import ESConnection
from constant import ES_HOST, ES_PORT


class SearchHandler(tornado.web.RequestHandler):

    es_connection = ESConnection(ES_HOST, ES_PORT)

    @tornado.web.asynchronous
    @coroutine
    def get(self, indice="index", tipo="user"):
        query = {"query": {"match_all": {}}}
        response = yield self.es_connection.search(index=indice,
                                  type=tipo,
                                  source=query)
        #print response
        self.write(json.loads(response.body))
        self.finish()

application = tornado.web.Application([
    (r"/", SearchHandler),
])

if __name__ == "__main__":
    application.listen(9988)
    tornado.ioloop.IOLoop.instance().start()
