__author__ = 'bone-lee'

from tornado import gen
from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
from motor import MotorClient
from tornado.concurrent import Future

@gen.coroutine
def f():
    client=AsyncHTTPClient()
    res=yield client.fetch('http://0.0.0.0:8080')
    print(res.body)

@gen.coroutine
def test_db():
    db = MotorClient().fbt_test
    yield db.users.insert({"name":"bone","age":100})
    user = yield db.users.find_one({"name":"bone","age":100})
    print user
    assert user


# tornado.ioloop.IOLoop.instance().run_sync(f)
print type(test_db())
assert isinstance(test_db(), Future)
tornado.ioloop.IOLoop.instance().run_sync(test_db)
