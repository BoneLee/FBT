__author__ = 'bone-lee'

from fb_rank_manager import FBRankManager
from time import time
from datetime import datetime
from datetime import date
import simplejson as json

class FBRankTimer(object):
    _io_loop = None
    ONE_HOUR= 1*3600
    _HOUR_AT_2 = 2
    _FIRST_DAY_OF_MONTH = 1
    _MONDAY = 1

    @classmethod
    def set_test_data(cls,two_hour_time,hour_at_two,first_day_of_month,monday):
        assert hour_at_two>0 and first_day_of_month>0 and two_hour_time>0 and monday>0
        cls._MONDAY=monday
        cls.ONE_HOUR=two_hour_time
        cls._HOUR_AT_2=hour_at_two
        cls._FIRST_DAY_OF_MONTH=first_day_of_month

    @classmethod
    def set_io_loop(cls, ioloop):
        cls._io_loop = ioloop

    @classmethod
    def run(cls):
        assert (cls._io_loop is not None)  # must set io loop
        #print "run...."
        cls._io_loop.add_timeout(time() + cls.ONE_HOUR, lambda: cls._reset_fb_rank())

    @classmethod
    def _reset_fb_rank(cls):
        # print "time up...."
        if cls._is_monday():
            # print "weekly time up...."
            cls._backup_rank(file_name='weekly-rank',is_weekly=True)
            cls._backup_rank(file_name='study-weekly-rank',is_weekly=True, is_by_study=True)
            FBRankManager.reset_weekly_fb()
        if cls._is_first_day_of_month():
            # print "monthly time up...."
            cls._backup_rank(file_name='monthly-rank',is_weekly=False)
            cls._backup_rank(file_name='study-monthly-rank',is_weekly=False, is_by_study=True)
            FBRankManager.reset_monthly_fb()

        # next tick
        cls._io_loop.add_timeout(time() + cls.ONE_HOUR, lambda: cls._reset_fb_rank())

    @classmethod
    def _is_monday(cls):
        '''
        if it is time to monday 2:00
        '''
        date2 = datetime.now()
        # check if weekday is monday
        #print date
        #print "weekday:",str(date.isoweekday())," hour:",str(date.hour)
        if date2.isoweekday() == cls._MONDAY and date2.hour == cls._HOUR_AT_2:
            return True
        else:
            return False

    @classmethod
    def _is_first_day_of_month(cls):
        '''
        if it is time to first day of month at 2:00
        '''
        date2 = datetime.now()
        #print date
        #print "day:",str(date.day)," hour:",str(date.hour)
        if date2.day == cls._FIRST_DAY_OF_MONTH and date2.hour == cls._HOUR_AT_2:
            return True
        else:
            return False

    @classmethod
    def get_name(cls, file_name):
        today=date.today().strftime("%Y-%m-%d")
        return file_name+'-'+today+'.txt'

    @classmethod
    def _backup_rank(cls,file_name,is_weekly=True, is_by_study=False):
        with open(cls.get_name(file_name), 'w') as outfile:
            if is_by_study:
                if is_weekly:
                   json.dump(FBRankManager.get_weekly_top(), outfile)
                else:
                    json.dump(FBRankManager.get_monthly_top(), outfile)
            else:
                if is_weekly:
                    json.dump(FBRankManager.get_weekly_top2(), outfile)
                else:
                    json.dump(FBRankManager.get_monthly_top2(), outfile)
