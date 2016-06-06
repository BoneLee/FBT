__author__ = 'bone-lee'

from fb_rank_manager import FBRankManager
from fb_manager import FBCoinManager
from fb_rank_timer import FBRankTimer
from util import errorHandle
import motorclient

import simplejson as json
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.options

class FBRankHandler(tornado.web.RequestHandler):
    _db = motorclient.fbt

    @classmethod
    def set_db(cls,db):
        assert db is not None
        cls._db=db

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        try:
            type = int(self.get_argument("type",None))
            assert type>=1 and type<=6
        except Exception,e:
            errorHandle(self,0)
            self.finish()
            return
        rank_by={"total_fb_weekly":1,"total_fb_monthly":2,"total_fb":3,
                     "study_fb_weekly":4, "study_fb_monthly":5, "total_study_fb":6}
        if type==rank_by["total_fb_weekly"]:
                fb_rank_data = FBRankManager.get_weekly_top()
        elif type==rank_by["total_fb_monthly"]:
                fb_rank_data = FBRankManager.get_monthly_top()
        elif type==rank_by["total_fb"]:
                fb_rank_data = yield FBCoinManager.get_total_rank()
        elif type==rank_by["study_fb_weekly"]:
                fb_rank_data = FBRankManager.get_weekly_top2()
        elif type==rank_by["study_fb_monthly"]:
                fb_rank_data = FBRankManager.get_monthly_top2()
        elif type==rank_by["total_study_fb"]:
                fb_rank_data = yield FBCoinManager.get_total_rank2()
        else:
                assert False
        ret = []

        for item in fb_rank_data:
            cursor = yield self._db.users.find_one({"uid":item[0]},{"nick_name":1,"icon":1})
            fb_coin =  yield FBCoinManager.get_user_total_fb_coin(item[0])
            if cursor and fb_coin:
                item_data = {}
                item_data["nick_name"] = cursor["nick_name"]
                item_data["icon"] = cursor["icon"]
                if type!=rank_by["total_fb"] or type!=rank_by["total_study_fb"]:
                    item_data["delta"] = item[1]
                item_data["coin"] = fb_coin
                item_data["uid"] = item[0]
                ret.append(item_data)
        result = json.dumps({"type": type,"data":ret})
        self.write(result)
        self.finish()

class FBRankDebugHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        type = int(self.get_argument("type", "1"))
        rank_by={"total_fb_weekly":1,"total_fb_monthly":2,"total_fb":3,
                     "study_fb_weekly":4, "study_fb_monthly":5, "total_study_fb":6}
        if type==rank_by["total_fb_weekly"]:
            fb_rank_data = FBRankManager.get_weekly_top()
        elif type==rank_by["total_fb_monthly"]:
            fb_rank_data = FBRankManager.get_monthly_top()
        elif type==rank_by["total_fb"]:
            fb_rank_data = yield FBCoinManager.get_total_rank()
        elif type==rank_by["study_fb_weekly"]:
            fb_rank_data = FBRankManager.get_weekly_top2()
        elif type==rank_by["study_fb_monthly"]:
            fb_rank_data = FBRankManager.get_monthly_top2()
        elif type==rank_by["total_study_fb"]:
            fb_rank_data = yield FBCoinManager.get_total_rank2()
        else:
            fb_rank_data = []
        self.write(json.dumps(fb_rank_data))
        self.finish()
        # is_weekly = self.get_argument("is_weekly", 1)
        # if is_weekly:
        #     self.write(json.dumps(FBRankManager.sorted_fb_rank(True)))
        # else:
        #     self.write(json.dumps(FBRankManager.sorted_fb_rank(False)))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/fbrank', FBRankHandler),
            (r'/fb_rank', FBRankDebugHandler),
        ]
        settings = dict()
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    http_server.listen(8890)
    db = motorclient.fbt
    FBRankHandler.set_db(db)

    ioloop=tornado.ioloop.IOLoop.instance()

    # FBRankManager.initialize()

    # just test timer with 20 seconds
    # from datetime import datetime
    # date = datetime.now()
    # FBRankTimer.set_test_data(20,date.hour,date.day,date.isoweekday())

    FBRankTimer.set_io_loop(ioloop)
    FBRankTimer.run()

    # from redis_pub_client import RedisPubClient
    # RedisPubClient().publish(json.dumps({123:456}))

    try:
        ioloop.start()
    except:
        FBRankManager.finalize()
        print "OK. Exit..."
