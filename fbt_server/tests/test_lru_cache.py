from lru_cache import LRUCache
import random
lru = LRUCache(5)
for i in xrange(10):
	lru.set(i%8,random.randint(1,100))
for i in xrange(10):
	print lru.get(i%8)