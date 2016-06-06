__author__ = 'bone-lee'

from datetime import date
import json

class FBRanker(object):
    '''
    user's contributed fb>0 is record into the memory.
    pass consuming user who just use fb.
    '''

    def __init__(self, max_fb_vary_range, backup_file_name):
        assert max_fb_vary_range>500
        assert len(backup_file_name)>0
        self._MAX_FB_VARY_CHANGE = max_fb_vary_range #5000
        self._NOT_INITIALIZED = 0
        self._delta_fb_array = [set() for i in range(0,self._MAX_FB_VARY_CHANGE)]
        self._users_delta_fb_last_time = dict()
        self._current_max_delta_fb=0
        self._backup_file_name=backup_file_name

    def _backup_rank(self):
        today=date.today().strftime("%Y-%m-%d")
        with open(self._backup_file_name+'-'+today+'.txt', 'w') as outfile:
            json.dump(self.get_top(20), outfile)

    def get_backup_info(self):
        info=dict()
        info["_MAX_FB_VARY_CHANGE"]=self._MAX_FB_VARY_CHANGE
        info["_NOT_INITIALIZED"]=self._NOT_INITIALIZED
        info["_users_delta_fb_last_time"]=self._users_delta_fb_last_time
        info["_current_max_delta_fb"]=self._current_max_delta_fb
        info["_delta_fb_array"]=self._delta_fb_array
        return info

    def restore_from_backup_info(self,info):
        self._MAX_FB_VARY_CHANGE=info["_MAX_FB_VARY_CHANGE"]
        self._NOT_INITIALIZED=info["_NOT_INITIALIZED"]
        self._users_delta_fb_last_time=info["_users_delta_fb_last_time"]
        self._current_max_delta_fb=info["_current_max_delta_fb"]
        self._delta_fb_array=info["_delta_fb_array"]

    def reset(self):
        self._backup_rank()
        for i in range(0, self._MAX_FB_VARY_CHANGE):
            self._delta_fb_array[i] = set()

    def _expand(self):
        self._MAX_FB_VARY_CHANGE*=2
        expanded_delta_fb_array = [set() for i in range(0,self._MAX_FB_VARY_CHANGE)]
        for i,users in enumerate(self._delta_fb_array):
            expanded_delta_fb_array[i]=users
        self._delta_fb_array=expanded_delta_fb_array

    def update_fb(self, uid, delta_fb):
        assert uid > 0
        delta_fb=int(delta_fb)
        # assert delta_fb!=0
        # CAUTION: may be delta_fb <0
        if (uid not in self._users_delta_fb_last_time):
            if (delta_fb > 0):
                self._users_delta_fb_last_time[uid] = 0
                # will update the user's fb later
            else:
                # will not record the user's fb
                return

        delta_fb_last_time = self._users_delta_fb_last_time[uid]
        assert delta_fb_last_time>=0
        current_delat_fb = delta_fb_last_time + delta_fb
        if current_delat_fb >= self._MAX_FB_VARY_CHANGE:
            #print "WARNING: delta fb out of range. I will expand the array."
            # automatically expand the array by double size
            self._expand()

        if current_delat_fb > 0:
            assert delta_fb_last_time<self._MAX_FB_VARY_CHANGE
            assert current_delat_fb<self._MAX_FB_VARY_CHANGE
            if uid in self._delta_fb_array[delta_fb_last_time]:
                self._delta_fb_array[delta_fb_last_time].remove(uid)
            self._delta_fb_array[current_delat_fb].add(uid)
            self._users_delta_fb_last_time[uid]=current_delat_fb
            if self._current_max_delta_fb < current_delat_fb:
                self._current_max_delta_fb=current_delat_fb
        else:
            if uid in self._delta_fb_array[delta_fb_last_time]:
                self._delta_fb_array[delta_fb_last_time].remove(uid)
            if uid in self._users_delta_fb_last_time:
                del self._users_delta_fb_last_time[uid]
            # print "user ran out of delta fb. pass user:", str(uid),"coin:",str(delta_fb)

    def get_top(self, how_many):
        assert how_many>0
        ans=[]
        i=0
        k=self._current_max_delta_fb
        while k>=0 and i<how_many:
            for uid in self._delta_fb_array[k]:
                ans.append((uid,self._users_delta_fb_last_time[uid]))
            i+=len(self._delta_fb_array[k])
            k-=1
        return ans[:how_many]
