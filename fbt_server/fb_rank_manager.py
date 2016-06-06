__author__ = 'bone-lee'

from redis_pub_sub_client import RedisSubscribeClient
from redis_cache_client import RedisCacheClient
from constant import CHANNEL_STUDY_COIN_VARY, FB_WEEKLY_CACHE, FB_MONTHLY_CACHE, STUDY_FB_WEEKLY_CACHE ,STUDY_FB_MONTHLY_CACHE
import simplejson as json

class FBRankManager(object):
    # _fb_vary_detector=None
    # _study_fb_vary_detector=None
    # _redis_cache = None
    _redis_cache = RedisCacheClient().get_instance()

    _FB_WEEKLY_CACHE = FB_WEEKLY_CACHE
    _FB_MONTHLY_CACHE = FB_MONTHLY_CACHE
    _STUDY_FB_WEEKLY_CACHE = STUDY_FB_WEEKLY_CACHE
    _STUDY_FB_MONTHLY_CACHE = STUDY_FB_MONTHLY_CACHE

    @classmethod
    def set_cache(cls, cache):
        cls._redis_cache = cache

    # @classmethod
    # def fb_vary_processor(cls,msg):
    #     fb_vary=json.loads(msg)
    #     # if len(fb_vary)<100:
    #     #     print "warning msg too few..."
    #     # print "receive coin vary:",msg
    #     pipe =  cls._redis_cache.pipeline()
    #     for uid,delta_fb in fb_vary.iteritems():
    #         # pipe.hsetnx(cls._FB_WEEKLY_CACHE,uid,0)
    #         # pipe.hsetnx(cls._FB_MONTHLY_CACHE,uid,0)
    #         pipe.hincrbyfloat(cls._FB_WEEKLY_CACHE,uid,delta_fb)
    #         pipe.hincrbyfloat(cls._FB_MONTHLY_CACHE,uid,delta_fb)
    #     pipe.execute()
    #
    # @classmethod
    # def study_fb_vary_processor(cls,msg):
    #     fb_vary=json.loads(msg)
    #     pipe =  cls._redis_cache.pipeline()
    #     for uid,delta_fb in fb_vary.iteritems():
    #         # cls._redis_cache.hsetnx(cls._STUDY_FB_WEEKLY_CACHE,uid,0)
    #         # cls._redis_cache.hsetnx(cls._STUDY_FB_MONTHLY_CACHE,uid,0)
    #         pipe.hincrby(cls._STUDY_FB_WEEKLY_CACHE,uid,delta_fb)
    #         pipe.hincrby(cls._STUDY_FB_MONTHLY_CACHE,uid,delta_fb)
    #     pipe.execute()

    @classmethod
    def initialize(cls, need_clear_fb_cache=False):
        pass
        # cls._fb_vary_detector=RedisSubscribeClient(cls.fb_vary_processor)
        # cls._study_fb_vary_detector=RedisSubscribeClient(cls.study_fb_vary_processor, CHANNEL_STUDY_COIN_VARY)
        # if need_clear_fb_cache:
        #     cls.reset_weekly_fb()
        #     cls.reset_monthly_fb()

    @classmethod
    def get_monthly_top(cls):
        return cls._get_top_helper(False)

    @classmethod
    def get_weekly_top(cls):
        return cls._get_top_helper(True)

    @classmethod
    def get_weekly_top2(cls):
        return cls._get_top_helper(True, True)

    @classmethod
    def get_monthly_top2(cls):
        return cls._get_top_helper(False, True)

    @classmethod
    def fb_vary_cmp(cls,x,y):
       if x[1]==y[1]: return cmp(y[0],x[0])
       else: return cmp(y[1],x[1])

    @classmethod
    def sorted_fb_rank(cls, is_weekly, is_by_study=False):
        if is_by_study:
            if is_weekly:
                fb_var = cls._redis_cache.hgetall(cls._STUDY_FB_WEEKLY_CACHE)
            else:
                fb_var = cls._redis_cache.hgetall(cls._STUDY_FB_MONTHLY_CACHE)
        else:
            if is_weekly:
                fb_var = cls._redis_cache.hgetall(cls._FB_WEEKLY_CACHE)
            else:
                fb_var = cls._redis_cache.hgetall(cls._FB_MONTHLY_CACHE)
        fb_var2 = [(int(uid), int(float(fb))) for uid, fb in fb_var.iteritems() if int(float(fb)) > 0]
        sorted_fb = sorted(fb_var2, cmp=cls.fb_vary_cmp)
        return sorted_fb

    @classmethod
    def _get_top_helper(cls, is_weekly = True, is_by_study=False):
        sorted_fb = cls.sorted_fb_rank(is_weekly, is_by_study)
        # return fb_var2.sort(cls.fb_vary_cmp)
        return sorted_fb[:100]

    @classmethod
    def reset_weekly_fb(cls):
        for k in (cls._FB_WEEKLY_CACHE, cls._STUDY_FB_WEEKLY_CACHE):
            keys=cls._redis_cache.hkeys(k)
            if len(keys)>0:
                cls._redis_cache.hdel(k,*keys)

    @classmethod
    def reset_monthly_fb(cls):
        for k in (cls._FB_MONTHLY_CACHE, cls._STUDY_FB_MONTHLY_CACHE):
            keys=cls._redis_cache.hkeys(k)
            if len(keys)>0:
                cls._redis_cache.hdel(k,*keys)

    @classmethod
    def finalize(cls):
        pass
        # if cls._fb_vary_detector:
        #     cls._fb_vary_detector.close()
