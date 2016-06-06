from motor import MotorClient
from tornado import gen, testing

class MyTestCase(testing.AsyncTestCase):
    def setUp(self):
        # super().setUp()
        super(MyTestCase, self).setUp()
        self.client = MotorClient()
        # self.setup_coro()
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        collection = self.client.test.collection

        # Clean up from prior runs:
        yield collection.remove()

        yield collection.insert({'_id': 0})
        yield collection.insert({'_id': 1, 'key': 'value'})
        yield collection.insert({'_id': 2})

    @testing.gen_test
    def test_find_one(self):
        collection = self.client.test.collection
        document = yield collection.find_one({'_id': 1})
        self.assertEqual({'_id': 1, 'key': 'value'}, document)

if __name__ == '__main__':
    import unittest
    unittest.main()