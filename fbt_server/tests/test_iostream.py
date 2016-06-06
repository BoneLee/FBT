__author__ = 'bone'

import tornado.ioloop
import tornado.iostream
import socket

def send_request():
    stream.write(b"GET / HTTP/1.0\r\nHost: friendfeed.com\r\n\r\n")
    stream.read_until(b"\r\n\r\n", on_headers)

def on_headers(data):
    headers = {}
    for line in data.split(b"\r\n"):
       parts = line.split(b":")
       if len(parts) == 2:
           headers[parts[0].strip()] = parts[1].strip()
    stream.read_bytes(int(headers[b"Content-Length"]), on_body)

def on_body(data):
    print(data)
    stream.close()
    tornado.ioloop.IOLoop.current().stop()

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    stream = tornado.iostream.IOStream(s)
    stream.connect(("friendfeed.com", 80), send_request)
    tornado.ioloop.IOLoop.current().start()
