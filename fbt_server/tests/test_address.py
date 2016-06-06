__author__ = 'bone-lee'

import sys
sys.path.append('..')
from http_server_info_cache import Address

import tornado.gen
import tornado.testing

class DownloadTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test
    def test_addr(self):
        s = set()
        addr1 = Address('1.1.1.1', 8000)
        s.add(addr1)
        self.assertEqual(len(s), 1)

        addr1 = Address('1.1.1.1', 8000)
        s.add(addr1)
        self.assertEqual(len(s), 1)

        addr1 = Address('1.1.1.1', 8001)
        s.add(addr1)
        self.assertEqual(len(s), 2)

        addr1 = Address('1.1.1.2', 8001)
        s.add(addr1)
        self.assertEqual(len(s), 3)

        d = dict()
        addr2 = Address('1.1.1.1', 8000)
        d[addr2] = 1
        self.assertEqual(len(d), 1)

        addr2 = Address('1.1.1.1', 8000)
        d[addr2] = 10
        self.assertEqual(len(d), 1)

        addr2 = Address('1.1.1.1', 8001)
        d[addr2] = 10
        self.assertEqual(len(d), 2)

        addr2 = Address('1.1.1.2', 8001)
        d[addr2] = 10
        self.assertEqual(len(d), 3)

        addr2 = Address('1.2.1.1', 8000)
        d[addr2] = 10
        self.assertEqual(len(d), 4)

if __name__ == '__main__':
    import unittest
    unittest.main()
