# -*- coding: utf-8 -*-
from resource_manager import ResourceStoreManager
from resource_info import ResourceInfo
from online_resources import OnlineResources
import motorclient

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado import gen
from tornado.options import define, options
import tornado.websocket
import util
import mongoclient
from redis_cache_client import RedisCacheClient
import simplejson as json

define("port", default=8892, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/res/online', ResourceHandler),
            (r'/online_uid_list', OnlineUidHandler),
            (r'/online/owners', OnlineOwnersHandler),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)

class OnlineUidHandler(tornado.web.RequestHandler):
    def get(self):
        uids=OnlineResources.get_online_uids()
        self.write(json.dumps({"uids":list(uids),"len":len(uids)}))


class OnlineOwnersHandler(tornado.web.RequestHandler):
    def get(self):
        fid = self.get_argument("file_id", None)
        if fid:
            self.write(json.dumps({"uids":list(OnlineResources.get_online_uids_of_resource(fid))}))
        else:
            self.write(json.dumps({"err":"file_id err"}))

class ResourceHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        yield self.get_res_list()

    @gen.coroutine
    def get_res_list(self):
        # user = self.get_argument("user", None)
        page = self.get_argument("page", 1)
        sort_by = self.get_argument("sort_by", ResourceStoreManager.res_sort_by["online_num"])
        res_type = self.get_argument("res_type", ResourceInfo.get_main_index_by_type("电影"))
        try:
            page = int(page)
            assert page>=0
            sort_by = int(sort_by)
            assert sort_by == ResourceStoreManager.res_sort_by["online_num"]
            res_type = int(res_type)
            assert ResourceInfo.is_valid_main_type(res_type)
        except:
            util.errorHandle(self, 0)
            self.finish()
            return
        cache_key="fb:online:type:"+str(res_type)+":page:"+str(page)
        redis_cache=RedisCacheClient().get_instance()

        RES_CNT_IN_A_PAGE = 20
        msg = {}
        msg["type"] = 1
        msg["error"] = ""
        resource_list = redis_cache.get(cache_key)
        if resource_list:
            resource_list=json.loads(resource_list)
        else:
            resource_list = yield OnlineResources.get_online_resources_by_type(res_type, page, RES_CNT_IN_A_PAGE)
            redis_cache.set(cache_key, json.dumps(resource_list))
            ONE_MINUTES=1 * 60
            redis_cache.expire(cache_key,ONE_MINUTES)
        if self.get_argument("version", "") >= "1.8":
            size = OnlineResources.get_online_resources_count(res_type)
            util.write(self, 1, "", {"size": (size+RES_CNT_IN_A_PAGE-1)/RES_CNT_IN_A_PAGE, "res":resource_list})
        else:
            util.write(self, 1, "", resource_list)
        self.finish()


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(options.port)
    try:
        ioloop=tornado.ioloop.IOLoop.instance()
        sync_db = mongoclient.fbt
        async_db = motorclient.fbt
        OnlineResources.initialize(sync_db, async_db)
        ioloop.start()
    except Exception,e:
        print e
        print "OK. I will exit..."
    finally:
        OnlineResources.finalize()

if __name__ == "__main__":
    main()
