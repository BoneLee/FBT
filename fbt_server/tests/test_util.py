__author__ = 'bone'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

import util
from tornado import testing

class UserManagerTestCase(testing.AsyncTestCase):
    def test_gen_pkey(self):
        uid_set = set()
        for i in range(10000):
            sid = util.generate_pkey()
            self.assertTrue(sid not in uid_set)
            uid_set.add(sid)

if __name__ == '__main__':
    import unittest
    unittest.main()