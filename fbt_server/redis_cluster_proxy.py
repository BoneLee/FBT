__author__ = 'bone'

from consistent_hash import ConsistentHashRing
from constant import REDIS_CACHE_HOST_PORTS, DEBUG_ENV, REDIS_DB_HOST_PORTS
import redis
import logging


class RedisWrapper(object):
    """
    Redis wrapper for ucloud redis.
    """
    def __init__(self, master_host, master_port, slave_host, slave_port):
        self._master = {"redis": redis.StrictRedis(master_host, master_port), "host": master_host, "port": master_port}
        self._slave = {"redis": redis.StrictRedis(slave_host, slave_port), "host": slave_host, "port": slave_port}
        self._current = self._master

    def current_working(self):
        return self._current

    def switch2other(self):
        if self._current is self._master:
            self._current = self._slave
        else:
            self._current = self._master


class ProxyCall(object):
    def __init__(self, proxy, methodname):
        self._proxy = proxy
        self._method = methodname

    def __call__(self, *args, **kwargs):
        if not args:
            key = None
        else:
            key = args[0]
        redis_wrapper = self._proxy.locate_at(key)
        redis_info = redis_wrapper.current_working()
        try:
            if self._method == "pipeline":
                kwargs["transaction"] = False
                if DEBUG_ENV:
                    print "ucloud redis does not support transaction. use transaction false."
            if DEBUG_ENV:
                print "redis key '", key, "' located on host:", redis_info["host"], " port:", redis_info["port"]
            return getattr(redis_info["redis"], self._method)(*args, **kwargs)
        except redis.exceptions.ConnectionError, e:
            logging.error("Error: redis dead. host=%s port=%s" % (redis_info["host"], redis_info["port"]))
            redis_wrapper.switch2other()
            return None


class UcloudRedisClusterProxy(object):
    def __init__(self, host_ports):
        self._init_with_hosts(host_ports)

    def _init_with_hosts(self, host_ports):
        self._cycle_hash_ring = ConsistentHashRing(100)
        for host, port, host2, port2 in host_ports:
            self._cycle_hash_ring[host] = RedisWrapper(host, port, host2, port2)

    def locate_at(self, key):
        if key is None:
            return self._cycle_hash_ring["None"]
        else:
            return self._cycle_hash_ring[key]

    def __getattr__(self, name):
        return ProxyCall(self, name)


class Redis(object):
    FOR_CACHE, FOR_DB = 1, 2

    def __init__(self, purpose=FOR_CACHE, host_ports=None):
        if purpose == self.FOR_CACHE:
            self._redis = UcloudRedisClusterProxy(host_ports) if host_ports else UcloudRedisClusterProxy(REDIS_CACHE_HOST_PORTS)
        elif purpose == self.FOR_DB:
            self._redis = UcloudRedisClusterProxy(host_ports) if host_ports else UcloudRedisClusterProxy(REDIS_DB_HOST_PORTS)
        else:
            assert False

    def __getattr__(self, name):
        return getattr(self._redis, name)

