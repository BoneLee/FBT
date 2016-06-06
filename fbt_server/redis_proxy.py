__author__ = 'bone'

from redis_handler import RedisHandler


class RedisProxy(object):
    def __init__(self, redis_client=None, redis_type=RedisHandler.type_search):
        if redis_client:
            self._redis = redis_client
        else:
            self._redis = None
        self._type = redis_type

    def __getattr__(self, command):
        if self._redis is None:
            self._redis = RedisHandler(tp=self._type)
        return getattr(self._redis, command)

# if __name__ == "__main__":
#     import redis
#     r = RedisProxy(redis_client=redis.StrictRedis())
#     r.set("name", "bone")
#     name = r.get("name")
#     assert name == "bone"
