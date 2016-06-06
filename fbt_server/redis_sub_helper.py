__author__ = 'bone'

from consistent_hash import ConsistentHashRing
from constant import TORNADO_HOSTS
from ip_address import get_lan_ip
from ip_address import is_valid_ipv4_address
from singleton import singleton
import time
import simplejson as json

def now():
    return str(time.time())

@singleton
class RedisSubHelper(object):
    def __init__(self):
        self._init_with_hosts(TORNADO_HOSTS)

    def _init_with_hosts(self, hosts):
        self._cycle_hash_ring = ConsistentHashRing(100)
        for host in hosts:
            assert is_valid_ipv4_address(host)
            self._cycle_hash_ring[host]=host
        print "redis sub helper initialized Ok. lan ip:"+get_lan_ip()+" hosts:"+str(hosts)

    def set_hosts(self, hosts):
        self._init_with_hosts(hosts)

    def get_located_server(self, key):
        return self._cycle_hash_ring[key]

    def is_located_myself(self, key=None):
        if key is None:
            key = now()
        return get_lan_ip() == self.get_located_server(key)

if __name__ == "__main__":
    """
    Just a test.
    """
    TORNADO_HOSTS = [get_lan_ip()]
    r = RedisSubHelper()

    print "key located on server list:"
    # for i in range(10):
    #     key=now()
    #     print key, "==>", r.get_located_server(key)
    #     time.sleep(1)

    r2 = RedisSubHelper()
    assert r2 == r and r2 is r
    r.set_hosts([get_lan_ip(),])

    assert r.is_located_myself("hello just a test key")
    assert r.is_located_myself(json.dumps({"is_subfile": False, "file_id": "3082528472_4670893950", "uid": 14297084819535}))
    assert RedisSubHelper().is_located_myself(json.dumps({"is_subfile": False, "file_id": "3082528472_4670893950", "uid": 14297084819535}))
    print "test passed"
