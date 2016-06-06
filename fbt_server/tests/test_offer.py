# -*- coding: utf-8 -*-

import tornado.gen
import tornado.testing
import motor
from offer_reward import Reward

def mock_hash(file_name):
    return abs(hash(file_name))

class RewardTestCase(tornado.testing.AsyncTestCase):
  def test_reward(self):
      @tornado.gen.engine
      def func(callback):
            fbt_reward = motor.MotorClient('localhost', 27017, io_loop=self.io_loop).fbt_reward
            fbt = motor.MotorClient('localhost', 27017, io_loop=self.io_loop).fbt
            Reward.set_db(fbt_reward, fbt)
            # yield Reward.user_offer_reward("14104947769291", "desc", "上山打老虎", 100, 0, 2005, "china")
            # yield Reward.user_offer_reward("14118101115545", "desc", "上山打老虎1", 200, 0, 2005, "ch2ina")
            # yield Reward.user_offer_reward("14104947769291", "desc", "上山打老虎2", 300, 1, 2015, "ch1ina中")
            # ret = yield Reward.get_all_reward_by_type(1, 20, 0)
            # print ret
            # ret = yield Reward.get_all_reward_by_type(1, 20, 1)
            # print ret
            # ret = yield Reward.get_all_reward_by_type(1, 20, 0, 0)
            # print ret
            # ret = yield Reward.get_all_reward_by_type(1, 20, 1, 0)
            # print ret
            # ret = yield Reward.get_my_reward_by_type("14104947769291", 1, 20)
            # print ret
            # ret = yield Reward.get_my_reward_by_type("14104947769291", 2, 20)
            # print ret
            # ret = yield Reward.get_my_reward_by_type("14104947769291", 1, 20, 0)
            # print ret 
            yield Reward.user_append_reward("14124352842458", 200, "14104947769291_1429952288912")
            yield Reward.user_upload_file(14124352842458, "29784195_1034944512", "14104947769291_1429952288912")
            yield Reward.user_download_file_over([14124352842458], "29784195_1034944512", "14104947769291_1429952288912")
            callback()

      func(callback=self.stop)
      self.wait()

if __name__ == '__main__':
    import unittest
    unittest.main()
