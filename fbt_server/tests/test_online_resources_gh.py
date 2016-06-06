import unittest
from online_resources import OnlineResources
from resource_online_num import ResourceOnlineNum

import pymongo
from tornado.ioloop import IOLoop
import tornado.gen
import tornado.testing
from pprint import pprint

from constant import CHANNEL_ON_OFF
from constant import CHANNEL_RES_UPLOAD
from constant import CHANNEL_RES_DEL
import tornadoredis
pub_client = tornadoredis.Client()

conn=pymongo.Connection("localhost",27017)
db=conn.fbt

class OnlineResourcesTestCase(tornado.testing.AsyncTestCase):
    def setUp(self):
        self.online_resources = OnlineResources()
        self.resource_online_num=ResourceOnlineNum()
    def tearDown(self):
        self.online_resources = None
        self.resource_online_num = None
    def testInit(self):
        self.online_resources.initialize(pymongo.Connection("localhost",27017).fbt,IOLoop.instance())
        self.assertEqual(db,self.online_resources._db)
        self.assertEqual(IOLoop.instance(),self.online_resources._io_loop)

        self.resource_online_num.initialize(pymongo.Connection("localhost",27017).fbt,
            self.online_resources.on_resource_online_num_delta)

    def testSetdb(self):
        self.online_resources.set_db(pymongo.Connection("localhost",27017).fbt)
        self.assertEqual(db,self.online_resources._db)
    def testSetioloop(self):
        self.online_resources.set_io_loop(IOLoop.instance())
        self.assertEqual(IOLoop.instance(),self.online_resources._io_loop)

    def testOnOffLineEtc(self):
        # pub_client.publish(CHANNEL_ON_OFF, '{"type":0, "uid": 123}')
        self.assertTrue(len(self.resource_online_num.get_resource_of_user(123))==0)
        self.assertTrue(len(self.resource_online_num.get_resource_of_user(14202111659810))>0)
        
        self.resource_online_num.on_user_online_offline('{"type":0, "uid": 14202111659810}')
        self.assertTrue(len(self.resource_online_num._online_users)>0)
        self.assertTrue(self.resource_online_num.get_online_user_num>0)
        online_num=self.resource_online_num.get_resource_online_num("2251655146_635376105")
        self.assertTrue(online_num>0)

        self.resource_online_num.on_user_online_offline('{"type":1, "uid": 14202111659810}')
        self.assertTrue(len(self.resource_online_num._online_users)==0)
        self.assertTrue(self.resource_online_num.get_online_user_num()==0)
        self.assertTrue(self.resource_online_num.get_resource_online_num("2251655146_635376105")==online_num-1)

        # pub_client.publish(CHANNEL_RES_UPLOAD, '{"file_id": 12_34, "file_name": "test", "uid": 123}')
        # pub_client.publish(CHANNEL_RES_DEL, '{"file_id": 12_34, "uid": 123}')
        self.resource_online_num.on_resource_add('{"file_id": "12_34", "file_name": "test", "uid": 123}')
        self.assertTrue(len(self.resource_online_num.get_resource_of_user(123))>0)
        self.resource_online_num.on_resource_del('{"file_id": "12_34", "uid": 123}')
        self.assertTrue(len(self.resource_online_num.get_resource_of_user(123))==0)

    def testZRes(self):
        
        @tornado.gen.engine
        def func(callback):
            self.online_resources.set_db(pymongo.Connection("localhost",27017).fbt)
            self.online_resources.set_io_loop(IOLoop.instance())
            self.online_resources.on_resource_online_num_delta("1078896638_1114200576",2)
            self.resource_online_num.on_user_online_offline('{"type":0, "uid": 14202111659810}')
            # pprint(self.online_resources._resource_online_num_delta)

            self.online_resources.reset_online_resources()

            print len(self.online_resources._resource_online_num_delta),
            pprint(self.online_resources._resource_online_num_delta)
            print len(self.online_resources._resource_by_online_num),
            pprint(self.online_resources._resource_by_online_num)
            print len(self.online_resources._online_num_of_resource),
            pprint(self.online_resources._online_num_of_resource)

            list1=yield self.online_resources.get_online_resources_by_type(1,1,20)
            # pprint(list1)
            print "len is %d" % len(list1)
            # self.assertTrue(len(list1)>0)

            cnt=self.online_resources.get_online_resources_count(1)
            print "cnt is %d" % cnt
            # self.assertTrue(cnt>0)
            self.resource_online_num.on_user_online_offline('{"type":1, "uid": 14202111659810}')

            callback()

        func(callback=self.stop)
        self.wait()


if __name__=="__main__":
    unittest.main()