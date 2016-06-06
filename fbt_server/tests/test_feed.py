import motorclient
from tornado import gen, testing
from feed import FeedManager

class MyTestCase(testing.AsyncTestCase):
    def setUp(self):
        # super().setUp()
        super(MyTestCase, self).setUp()
        self.db = motorclient.fbt
        # self.setup_coro()
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        pass
        #collection = self.client.fbt.all_comments

        # Clean up from prior runs:
        #yield collection.remove()

        #yield collection.insert({'_id': 1, 'key': 'value'})
        #yield collection.insert({'_id': 2})

    @testing.gen_test
    def test_find_one(self):
        FeedManager.set_db(self.db)
        yield FeedManager.add_feed("1", "nick", 14105018325306, FeedManager.TYPE_UPLOAD, "nick")
        yield FeedManager.add_feed("1", "nick", 14105018325306, FeedManager.TYPE_UPLOAD, "nick")
        document = yield FeedManager.get_feed(14105018325306)
        print document

if __name__ == '__main__':
    import unittest
    unittest.main()