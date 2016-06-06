# -*- coding: UTF-8 -*-

from constant import *

from redis import StrictRedis

__author__ = 'SG'


class RedisHandler(object):
    _check_client = 1
    _clients = None
    type_token = 0
    type_cache = 1
    type_search = 2
    type_msg = 3
    type_lru = 4
    type_db = 5
    is_master_slave = False
    commands_readonly = set(['zcard','zscore','zrevrangebylex','replconf','getbit','select','bgrewriteaof','type','substr','zcount','zrange','hexists','hget','zrevrangebyscore','zlexcount','psync','zrevrank','ttl','zrevrange','hmget','smembers','zrangebyscore','dbsize','lastsave','scan','zrank','monitor','randomkey','ping','pubsub','wait','object','pfselftest','hgetall','cluster','sismember','zrangebylex','llen','save','auth','sscan','bgsave','sunion','sync','exists','hkeys','lindex','unsubscribe','mget','publish','time','latency','dump','1','readonly','srandmember','bitpos','psubscribe','config','lrange','keys','asking','client','echo','pttl','hlen','multi','sdiff','info','hscan','sinter','strlen','discard','shutdown','hvals','zscan','get','getrange','scard','script','unwatch','subscribe','slowlog','bitcount','punsubscribe','watch','pfcount','command','readwrite'])

    @staticmethod
    def init():
        if not RedisHandler._clients:
            # 每个tornado读取本地的redis，存到redis集群的master
            if RedisHandler.is_master_slave:
                RedisHandler._clients = [
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[1], password=REDIS_PWD[1]),
                     'slave': StrictRedis(port=REDIS_PORT[1], password=SESSION_PWD)},
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[0], password=REDIS_PWD[0]),
                     'slave': StrictRedis(port=REDIS_PORT[0], password=CACHE_PWD)},
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[2], password=REDIS_PWD[2]),
                     'slave': StrictRedis(port=REDIS_PORT[2], password=SEARCH_PWD)},
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[3], password=REDIS_PWD[3]),
                     'slave': StrictRedis(port=REDIS_PORT[3], password=MSG_PWD)},
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[4], password=REDIS_PWD[4]),
                     'slave': StrictRedis(port=REDIS_PORT[4], password=LRU_PWD)},
                    {'master': StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[5], password=REDIS_PWD[5]),
                     'slave': StrictRedis(port=REDIS_PORT[5], password=DB_PWD)}]
            else:
                RedisHandler._clients = [
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[1], password=REDIS_PWD[1]),
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[0], password=REDIS_PWD[0]),
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[2], password=REDIS_PWD[2]),
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[3], password=REDIS_PWD[3]),
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[4], password=REDIS_PWD[4]),
                    StrictRedis(host=REDIS_MASTER_HOST, port=REDIS_PORT[5], password=REDIS_PWD[5])]

    @staticmethod
    def redis_client(tp, service):
        if RedisHandler.is_master_slave:
            return RedisHandler._clients[tp][service]
        else:
            return RedisHandler._clients[tp]

    @staticmethod
    def f_get(key, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'slave').get(key)
    
    @staticmethod
    def master_get(key, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').get(key)

    #@ex the expire time in ex seconds
    @staticmethod
    def f_set(key,value,ex=None, tp=type_cache):
        RedisHandler.init()
        if ex:
            RedisHandler.redis_client(tp, 'master').setex(key, ex, value)
        else:
            RedisHandler.redis_client(tp, 'master').set(key, value)

    #@ex the expire time in ex seconds
    @staticmethod
    def f_mset(mapping, ex=None, tp=type_cache):
        RedisHandler.init()
        if ex:
            pipe = RedisHandler.redis_client(tp, 'master').pipeline()
            for (k,v) in mapping:
                pipe.setex(k, ex, v)
            pipe.execute()
        else:
            RedisHandler.redis_client(tp, 'master').mset(mapping)

    @staticmethod
    def f_delete(tp=type_cache, *names):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').delete(*names)

    @staticmethod
    def f_exists(name, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'slave').exists(name)

    #Return the value of key within the hash name
    @staticmethod
    def f_hget(name, key, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'slave').hget(name, key)

    #Return dict within the hash name
    @staticmethod
    def f_hgetall(name, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'slave').hgetall(name)

    #Set key to value within hash name
    @staticmethod
    def f_hset(name, key, value, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').hset(name, key, value)

    #Increment the value of key in hash name by amount
    @staticmethod
    def f_hincrease(name, key, amount=1, tp=type_cache):
        RedisHandler.init()
        RedisHandler.redis_client(tp, 'master').hincrby(name, key, amount)

    #Add value(s) to set name
    @staticmethod
    def f_sadd(name, tp=type_cache, *values):
        RedisHandler.init()
        RedisHandler.redis_client(tp, 'master').sadd(name, *values)

    #Remove values from set name
    @staticmethod
    def f_sremove(name, tp=type_cache, *values):
        RedisHandler.init()
        RedisHandler.redis_client(tp, 'master').srem(name, *values)

    #Return all members of the set name
    @staticmethod
    def f_smembers(name, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'slave').smembers(name)

    #Set mapping within hash name
    @staticmethod
    def f_hmset(name, mapping, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').hmset(name, mapping)

    #delete keys from hash name
    @staticmethod
    def f_hdel(name, tp=type_cache, *keys):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').hdel(name, *keys)

    #Returns a boolean indicating if key exists
    @staticmethod
    def f_hexists(name, key, tp=type_cache):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').hexists(name, key)

    @staticmethod
    def f_append(name, tp=type_cache, *value):
        RedisHandler.init()
        return RedisHandler.redis_client(tp, 'master').rpush(name, *value)

    @staticmethod
    def f_save():
        RedisHandler.init()
        for item in RedisHandler._clients:
            if RedisHandler.is_master_slave:
                item['master'].bgsave()
            else:
                item.bgsave()

    def __getattr__(self, command):
        RedisHandler.init()
        if command in RedisHandler.commands_readonly:
            return getattr(RedisHandler.redis_client(self.type_option, 'slave'), command)
        else:
            return getattr(RedisHandler.redis_client(self.type_option, 'master'), command)

    def __init__(self, tp=type_cache):
        self.type_option = tp
    
    @staticmethod
    def get_slave(tp=type_cache):
        return RedisHandler.redis_client(tp, 'slave')

if __name__ == '__main__':
    print 'start...'

    for tp in range(6):
        redis_client = RedisHandler(tp)
        print redis_client.set('tx', 'text1')
        print redis_client.get('tx')
        print redis_client.set('tx', 'text2')
        print redis_client.get('tx')
        print RedisHandler.master_get('tx', tp)
        print redis_client.set('tx', 'text3')
        print RedisHandler.get_slave(tp).get('tx')
        print redis_client.delete('tx')

	print 'f_get, f_set'
	RedisHandler.f_set('tx', 'text4', tp=tp)
	print RedisHandler.f_get('tx', tp)

        print tp, ' end...'

