__author__ = 'sg90'

from online_resources import OnlineResources
import tornado.gen
import tornado.testing
import motor
import redis
from random import randint

class OnlineResourcesTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=5)
    def test_online_resources(self):
        db = motor.MotorClient().fbt_test
        redis_db = redis.StrictRedis()
        redis_db.flushdb()
        OnlineResources.set_db_and_redis(db, redis_db)
        main_type = 0
        for i in range(100):
            OnlineResources.increase_online_owners("file_id"+str(randint(0,10)), randint(0,i), main_type)
        online_cnt = OnlineResources.get_online_cnt(0, -1, main_type)
        self.assertTrue(len(online_cnt) > 0)
        print online_cnt
        online_cnt = OnlineResources.get_online_cnt(10, 11, main_type)
        print online_cnt
        # print OnlineResources.get_online_resources_count(main_type)

if __name__ == '__main__':
    import unittest
    unittest.main()