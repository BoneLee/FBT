#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
from pymongo import MongoClient

from redis_lru_scheduler import RedisDelegate, CoinsOfUser, AllResources, Fblog

__author__ = 'spark'

def test_coins_of_user(redis_delegator):
    uid_list = [14104944395835,14104947769291,14104978985238,14104995015493,14105018325306,14105027983269,
                      14105030388393,14105120451974,14105136689145,14105143732386,14105174326288,14105177723674,
                      14105181089908,14105181776344,14105187806035,14105195902239,14105202978718,14105209784823,
                      14105211893120,14105215165951]
    for uid in uid_list:
        coins_user = redis_delegator.coins_of_user(uid)
        #print redis_delegator.coins_of_user.find(uid, ['total_coins', 'public_download_queue'])
        if uid % 2:
            #print coins_user.public_download_queue.get_all_items()
            coins_user.public_download_queue.sadd(7)
            print coins_user.public_download_queue.get_all_items()
        else:
            coins_user.total_coins = -22
            print coins_user.total_coins
        #print redis_delegator.coins_of_user.find(uid, ['total_coins', 'public_download_queue'])

def test_all_resources(redis_delegator):
    res_list = ['29784195_1034944512', '2092091362_15437226']
    for res in res_list:
        all_resources = redis_delegator.all_resources(res)

        print all_resources.find(res, ['owner', 'file_name'])
        print 'file_name', all_resources.file_name
        print 'file_size', all_resources.file_size

        print all_resources.tags.get_all_items()
        print all_resources.comments.get_all_items()
        print all_resources.scores.get_all_items()
        print all_resources.exp_info.get_all_items()
        print all_resources.owner.get_all_items()
        all_resources.owner.zadd(111, 1, 222, 0)
        print all_resources.owner.get_all_items()
        print all_resources.owner.zcard()
        print all_resources.owner.zscore(111)
        all_resources.owner.zrem(111)
        print all_resources.owner.get_all_items()

def test_fblog(redis_delegator):
    uid_list = [14104944395835,14104947769291,14104978985238,14104995015493,14105018325306,14105027983269,
                  14105030388393,14105120451974,14105136689145,14105143732386,14105174326288,14105177723674,
                  14105181089908,14105181776344,14105187806035,14105195902239,14105202978718,14105209784823,
                  14105211893120,14105215165951]
    for uid in uid_list:
        fl = redis_delegator.fblog(uid)
        fl.online_time = 111
        fl.log = [{'a': 1, 'uid': uid}]
        #print fl.log.get_all_items()

def main():
    sync_db = MongoClient('localhost', 27017).fbt
    redis_conn = redis.StrictRedis()
    redis_delegator = RedisDelegate(redis_conn, sync_db)
    
    coins_of_user = CoinsOfUser()
    #redis_delegator.add_collection(coins_of_user)
    all_resources = AllResources()
    fblog = Fblog()
    redis_delegator.add_collection(fblog)
    redis_delegator.add_collection(coins_of_user)
    redis_delegator.add_collection(all_resources)

    #test_all_resources(redis_delegator)
    test_fblog(redis_delegator)

if __name__ == "__main__":
    main()