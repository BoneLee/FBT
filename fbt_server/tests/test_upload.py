__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from user_ip_cache import UserIPCache
from resource_manager import ResourceStoreManager
from http_server_info_cache import HttpServerInfoCache
from download_medium import DownloadMedium

import tornado.gen
import tornado.testing
import motorclient

def mock_hash(file_name):
    return abs(hash(file_name))

class DownloadTestCase(tornado.testing.AsyncTestCase):
  def test_download(self):
      @tornado.gen.engine
      def func(callback):
            ResourceStoreManager.set_db(motorclient.fbt_test)
            yield ResourceStoreManager.clear_db()

            # user 2,3 uploaded the same file
            yield ResourceStoreManager.user_upload_resource(2,"user2",mock_hash("file_hash2"),"test2.txt",1023,1,["tag1","tag2"],0,1,3,"user2 uploaded file",None)
            yield ResourceStoreManager.user_upload_resource(3,"user3",mock_hash("file_hash2"),"test2.txt",1023,1,["tag1","tag2"],0,1,3,"user3 uploaded file",None)

            #test mutiple v6 ip
            cnt=yield ResourceStoreManager._db.all_resources.find().count()
            self.assertEqual(cnt, 1)

            # user 2 uploaded the "" file_name
            yield ResourceStoreManager.user_upload_resource(2,"user2",mock_hash("file_hash2"),"",1023,1,["tag1","tag2"],0,1,3,"user2 uploaded file",None)

            #test mutiple v6 ip
            cnt=yield ResourceStoreManager._db.all_resources.find().count()
            self.assertEqual(cnt, 1)

            # user 2 uploaded the null file_name
            yield ResourceStoreManager.user_upload_resource(2,"user2",mock_hash("file_hash2"),"",1023,1,["tag1","tag2"],0,1,3,"user2 uploaded file",None)

            #test mutiple v6 ip
            cnt=yield ResourceStoreManager._db.all_resources.find().count()
            self.assertEqual(cnt, 1)
            callback()

      func(callback=self.stop)
      self.wait()

if __name__ == '__main__':
    import unittest
    unittest.main()