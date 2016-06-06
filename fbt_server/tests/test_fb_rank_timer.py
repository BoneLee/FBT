__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from fb_rank_timer import FBRankTimer
from fb_rank_manager import FBRankManager
from tornado import testing
import mock
import redis
import os
from time import time

class FBRankTimerTestCase(testing.AsyncTestCase):
    @testing.gen_test
    def test_weekly_backup(self):
        r = redis.StrictRedis()
        with mock.patch('fb_rank_timer.FBRankTimer.ONE_HOUR', 0.1) as mock_publish:
            with mock.patch('fb_rank_timer.FBRankTimer._is_monday', return_value=True) as w:
                self.assertTrue(FBRankTimer._is_monday())
                r.flushdb()
                FBRankManager.set_cache(r)
                FBRankTimer.set_io_loop(self.io_loop)
                FBRankTimer.run()

                def test_func():
                    self.assertTrue(os.path.isfile(FBRankTimer.get_name('weekly-rank')))
                    self.assertTrue(os.path.isfile(FBRankTimer.get_name('study-weekly-rank')))
                    self.stop()

                self.io_loop.add_timeout(time() + FBRankTimer.ONE_HOUR * 2, test_func)
                self.wait()
        print "test weekly backup rank ok"

    @testing.gen_test
    def test_monthly_backup(self):
        r = redis.StrictRedis()
        with mock.patch('fb_rank_timer.FBRankTimer.ONE_HOUR', 0.1) as mock_publish:
            with mock.patch('fb_rank_timer.FBRankTimer._is_first_day_of_month', return_value=True) as w:
                self.assertTrue(FBRankTimer._is_first_day_of_month())
                r.flushdb()
                FBRankManager.set_cache(r)
                FBRankTimer.set_io_loop(self.io_loop)
                FBRankTimer.run()

                def test_func():
                    self.assertTrue(os.path.isfile(FBRankTimer.get_name('monthly-rank')))
                    self.assertTrue(os.path.isfile(FBRankTimer.get_name('study-monthly-rank')))
                    self.stop()

                self.io_loop.add_timeout(time() + FBRankTimer.ONE_HOUR * 2, test_func)
                self.wait()
        print "test monthly backup rank ok"


if __name__ == '__main__':
    import unittest

    unittest.main()
