# -*- coding: utf-8 -*-
__author__ = 'bone'

import os
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import simplejson as json
import tornado.escape
import tornado.gen

class BaseHandler(tornado.web.RequestHandler):
    @property
    def study_resource_manager(self):
        return self.application.study_resource_manager

    @property
    def redis_db_manager(self):
        return self.application.redis_db_manager
   
    def get_current_user(self):
        # print "data:"+str(self.get_secure_cookie("user"))
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    ERR = {"NONE":0, "ARGUMENT_ERR":1}
    # @tornado.web.asynchronous
    # @tornado.gen.coroutine
    def get(self):
        # TODO add redis cache here
        # all_resource = yield self.study_resource_manager.get_resource_overview()
        #self.render("home.html", all_resources=None)
        #self.render("index.html")        
        #self.redirect("/statics/index.html")
        with open("static/home.html") as f:
            self.write(f.read())
        self.finish()

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/statics/(.*)", tornado.web.StaticFileHandler, {"path":os.path.join(os.path.dirname(__file__), "static")}),
             ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            #static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            login_url="/login",
            debug=True, # TODO REMOVE
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # dependency across all handlers


from tornado.options import define,options,parse_command_line
define('port',default=9999, help='run on the port', type=int)
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()

