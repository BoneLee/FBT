__author__ = 'bone-lee'

import mock
import tornado.testing


class MockConstantTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=1)
    def test_mock(self):
        with mock.patch("constant.PUB_SUB_PORT", 9999) as what_ever:
            from constant import PUB_SUB_PORT
            self.assertEqual(PUB_SUB_PORT, 9999)

if __name__ == '__main__':
    import unittest
    unittest.main()
