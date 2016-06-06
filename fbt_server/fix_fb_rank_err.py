from redis_cache_client import RedisCacheClient
import mongoclient
db=mongoclient.fbt

cache = RedisCacheClient().get_instance()
_FB_WEEKLY_CACHE = "fb:cache:weekly"
_FB_MONTHLY_CACHE = "fb:cache:monthly"

def fix_rank(key):
    fb_var=cache.hgetall( key)
    def fb_vary_cmp(x,y):
        if x[1]==y[1]: 
            return cmp(y[0],x[0])
        else: 
            return cmp(y[1],x[1])

    fb_var2 = [(int(uid), int(float(fb))) for uid, fb in fb_var.iteritems() if int(float(fb)) > 0]
    sorted_fb = sorted(fb_var2, cmp=fb_vary_cmp)      
    fb_user=sorted_fb #[:1000]

    for uid, coin in fb_user:
        c = db.coins_of_user.find_one({"uid": uid}, {"total_coins":1})
        if c and "total_coins" in c:
           if c["total_coins"] < coin:
               cache.hset(key, uid, int(c["total_coins"])-1)
               #print "hset ....."

fix_rank(_FB_WEEKLY_CACHE)
print "Ok week"
fix_rank(_FB_MONTHLY_CACHE)
print "Ok month"
