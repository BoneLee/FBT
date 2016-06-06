__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from redis_pub_sub_client import RedisSubscribeClient, RedisPubClient
from tornado import testing
import mock

# just mock local redis
import constant
constant.PUB_SUB_HOST = "127.0.0.1"
constant.PUB_SUB_PWD = ""
constant.PUB_SUB_PORT = 6379

class RedisSubscribeClientTestCase(testing.AsyncTestCase):
    # def tearDown(self):
    #     pass

    @testing.gen_test
    def test_pub_sub(self):
        redis_sub_callback = mock.Mock()
        msg = {123: 456}
        def redis_sub_OK():
            redis_sub_callback.assert_called_once_with(json.dumps(msg))
            print "test redis pub sub Ok"
            self.stop()

        RedisSubscribeClient(redis_sub_callback)
        import simplejson as json
        from time import time
        self.io_loop.add_timeout(time() + 1, lambda: RedisPubClient().publish(json.dumps(msg)))
        self.io_loop.add_timeout(time() + 2, redis_sub_OK)
        self.wait()

if __name__ == '__main__':
    import unittest
    unittest.main()
