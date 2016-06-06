# -*- coding: utf-8 -*-

__author__ = 'bone-lee'

import tornado.gen
import tornado.testing
from resource_manager import ResourceStoreManager
import motorclient


class NavigateTestCase(tornado.testing.AsyncTestCase):
  def test_download(self):
      @tornado.gen.engine
      def func(callback):
            ResourceStoreManager.set_db(motorclient.fbt_realtime)
            res=yield ResourceStoreManager.navigate_resources(0,1,0,10,"动作","2014","美国")
            print res
            self.assertTrue(len(res)>0)
            nav_info=yield ResourceStoreManager.get_nav_info()
            self.assertTrue(len(nav_info)>0)
            print nav_info
            callback()

      func(callback=self.stop)
      self.wait()

if __name__ == '__main__':
    import unittest
    unittest.main()
