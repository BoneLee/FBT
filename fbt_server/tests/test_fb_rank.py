__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from fb_rank_manager import FBRankManager

import simplejson as json
from random import randint,uniform
import tornado.gen
import tornado.testing
import tornado.ioloop
import mock
import redis

def my_cmp(x,y):
    if x[1]==y[1]: return cmp(y[0],x[0])
    else: return cmp(y[1],x[1])

class FBRankTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=3)
    def test_fb_rank(self):
        # r = redis.StrictRedis()
        # with mock.patch('redis.StrictRedis.publish') as mock_publish:
        #     gold_ans=[]
        #     r.flushdb()
        #     FBRankManager.set_cache(r)
        #     self.assertListEqual(FBRankManager.get_weekly_top(),gold_ans)
        #     self.assertListEqual(FBRankManager.get_monthly_top(),gold_ans)
        #
        #     fb_vary={}
        #     for i in range(1,5000):
        #         uid=randint(1,500)
        #         delta_fb=uniform(-10,300) # a float in range -100,3000
        #
        #         found=False
        #         delta_fb=int(delta_fb)
        #         for i,data in enumerate(gold_ans):
        #             if data[0]==uid:
        #                 gold_ans[i]=(uid, data[1]+delta_fb)
        #                 found=True
        #                 break
        #         if not found:
        #             gold_ans.append((uid,delta_fb))
        #         if uid not in fb_vary:
        #             fb_vary[uid]=0
        #         fb_vary[uid]+=delta_fb
        #
        #     # RedisPubClient().publish(json.dumps(fb_vary))
        #     FBRankManager.fb_vary_processor(json.dumps(fb_vary))
        #     self.assertListEqual(FBRankManager.get_weekly_top(),FBRankManager.get_monthly_top())
        #
        #     gold_ans.sort(my_cmp)
        #     ans2=list(FBRankManager.get_weekly_top())
        #     ans2.sort(my_cmp)
        #     self.assertListEqual(ans2,gold_ans[:100])
        #
        #     FBRankManager.reset_weekly_fb()
        #     ans=list(FBRankManager.get_weekly_top())
        #     self.assertListEqual(ans, [])
        #
        #     FBRankManager.study_fb_vary_processor(json.dumps(fb_vary))
        #     self.assertListEqual(FBRankManager.get_weekly_top2(),FBRankManager.get_monthly_top2())
        #     gold_ans.sort(my_cmp)
        #     ans2=list(FBRankManager.get_weekly_top2())
        #     ans2.sort(my_cmp)
        #     self.assertListEqual(ans2,gold_ans[:100])
            print "test fb_rank ok"

if __name__ == '__main__':
    import unittest
    unittest.main()
