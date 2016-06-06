__author__ = 'bone'

import mock
import os
import psutil
import redis
from motor import MotorClient
from pymongo import MongoClient
from es_search import ESSearch


def check_callable(f):
    if callable(f):
        return str(f())
    else:
        return str(f)

def is_process_on(process_name):
    for proc in psutil.process_iter():
        if process_name in check_callable(proc.cmdline) or process_name in check_callable(proc.name):
            return True
    return False

def run():
    mock_redis = redis.StrictRedis()
    sync_db = MongoClient()
    db = MotorClient()
    mock_mapping = {
        "settings": {"refresh_interval": "5s",
                     "number_of_shards": 2,
                     "number_of_replicas": 1},
        "mappings": {
            "_default_": {
                "_all": {"enabled": False}
            },
        }
    }
    # CAUTION: local search disabled!!!
    es = ESSearch(host="localhost", port=9200, index_name="test_index", type_name="test_type",
                  index_mapping=mock_mapping, analyze_fields=[], none_analyze_fields=[])
    with mock.patch('redis_handler.RedisHandler.redis_client', return_value=mock_redis) as whate_ever:
        with mock.patch('redis_cluster_proxy.Redis', return_value=mock_redis) as whate_ever1:
            with mock.patch("pymongo.MongoReplicaSetClient", return_value=sync_db) as what_ever2:
                with mock.patch("motor.MotorReplicaSetClient", return_value=db) as what_ever3:
                    with mock.patch("es_search.ESSearch", return_value=es) as what_ever4:
                        from fbt_http import main
                        main()

if __name__ == "__main__":
    print "Please run bash pre_run to install required library."

    # check that redis-server and mongodb is open
    redis_server_process = "redis-server"
    mongodb_server_process = "mongod"

    # start redis
    if not is_process_on(redis_server_process):
        os.system('redis-server > /dev/null &')
    # start elastic search
    assert is_process_on(redis_server_process), "redis-server not on"
    assert is_process_on(mongodb_server_process), "mongodb is not on"
    os.environ["DEBUG_ENV"]="1"
    run()
