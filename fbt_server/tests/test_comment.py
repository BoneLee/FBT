import motorclient
from tornado import gen, testing
from comment import CommentManager

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
        CommentManager.set_db(self.db)
        yield CommentManager.addComment("1", "nick", "12", "nick", "nick", "twat")
        yield CommentManager.addComment("1", "nick", "12", "nick", "nick", "twat1")
        yield CommentManager.addComment("2", "nick", "12", "nick", "nick", "twat2")
        yield CommentManager.addComment("1", "nick", "2", "nick", "nick", "twat3")
        document = yield CommentManager.getComment('1')
        print document

if __name__ == '__main__':
    import unittest
    unittest.main()