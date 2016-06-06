# -*- coding: utf-8 -*-

__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

import tornado.gen
import tornado.testing
from resource_manager import ResourceStoreManager
import motorclient


class NavigateTestCase(tornado.testing.AsyncTestCase):
  def test_download(self):
      @tornado.gen.engine
      def func(callback):
            ResourceStoreManager.set_db(motorclient.fbt_realtime)
            # yield ResourceStoreManager._db.all_resources.update({"download_num": {"$gt":200}},{"$set":{"sticky":1}},{"upsert": True, "multi": True})
            res=yield ResourceStoreManager.get_resources_overview(0,1,1,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            print "len res:",str(len(res))
            self.assertTrue(len(res)>0)
            print "cnt:",str(cnt),"total:",len(res)

            res=yield ResourceStoreManager.get_resources_overview(0,11,1,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            self.assertTrue(len(res)>0)
            print "cnt:",str(cnt),"total:",len(res)

            res=yield ResourceStoreManager.get_resources_overview(0,21,1,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            self.assertTrue(len(res)>0)
            print "cnt:",str(cnt),"total:",len(res)

            res=yield ResourceStoreManager.get_resources_overview(0,24,1,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            self.assertTrue(len(res)>0)
            print "cnt:",str(cnt),"total:",len(res)

            res=yield ResourceStoreManager.get_resources_overview(0,2,1,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            self.assertTrue(cnt==0)
            print "cnt:",str(cnt),"total:",len(res)

            # test resource sort by time
            res=yield ResourceStoreManager.get_resources_overview(0,1,0,20)
            cnt=0
            for r in res:
                if "sticky" in r and r["sticky"]>0:
                    cnt+=1
                    print "found sticky resource",r["file_name"]
            self.assertTrue(cnt==0)
            print "cnt:",str(cnt),"total:",len(res)
            callback()

      func(callback=self.stop)
      self.wait()

if __name__ == '__main__':
    import unittest
    unittest.main()
