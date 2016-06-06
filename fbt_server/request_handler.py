import find_password

import tornado.web
import simplejson as json
import tornado.gen
from tornado.options import options

class ResetPwdHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_argument("key", ""):
            self.render("reset_pwd.html")
        else:
            self.write(json.dumps({"type": 0}))

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        if self.get_argument("user", "") and self.get_argument("token", "") and self.get_argument("pwd", ""):
            token = self.get_argument("token")
            user = self.get_argument("user")
            pwd = self.get_argument("pwd")
            ret = yield find_password.confirm_reset(token, user, pwd)
            if ret:
                self.write(json.dumps({"type": 1}))
                self.finish()
            else:
                self.write(json.dumps({"type": 0}))
                self.finish()
        else:
            self.write(json.dumps({"type": 0}))
            self.finish()

class SendResetEmailHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("user", ""):
            where = self.get_argument("from", "browser")
            if where == "client":
                ret = yield find_password.reset(self.get_argument("user"))
            else:
                ret = yield find_password.reset(self.get_argument("user"), options.port)
            if ret:
                self.write(json.dumps({"type": 1}))
                self.finish()
            else:
                self.write(json.dumps({"type": 0}))
                self.finish()
        else:
            self.write(json.dumps({"type": 0}))
            self.finish()