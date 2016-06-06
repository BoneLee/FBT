__author__ = 'bone-lee'

def make_generator():
    yield 0
    yield 1

g=make_generator()
while True:
    try:
        # i=g.next()
        i=g.send(None)
        print(i)
    except StopIteration:
        break

def make_generator2():
    ret=yield 0
    print "got " ,ret
    ret=yield 1
    print "got ", ret

print "*" * 30
g=make_generator2()
i=g.send(None)
while True:
    try:
        print(i)
        i=g.send(i+10) #yield xxx is g.send's return
    except StopIteration:
        break

from tornado import gen
from tornado.httpclient import AsyncHTTPClient
@gen.coroutine
def f():
    print "hi"
    client=AsyncHTTPClient()
    print "hello"
    res=yield client.fetch('http://gfsoso.com')
    print "world"
    print(res)

f()
