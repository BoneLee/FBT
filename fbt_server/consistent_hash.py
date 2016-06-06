__author__ = 'bone'
# refer http://techspot.zzzeek.org/2012/07/07/the-absolutely-simplest-consistent-hashing-example/

import bisect
from hashlib import md5
from tornado.escape import utf8

class ConsistentHashRing(object):
    """Implement a consistent hashing ring."""

    def __init__(self, replicas=100):
        """Create a new ConsistentHashRing.

        :param replicas: number of replicas.

        """
        self.replicas = replicas
        self._keys = []
        self._nodes = {}

    def _hash(self, key):
        """Given a string key, return a hash value."""
        m = md5()
        m.update(utf8(key))
        return long(m.hexdigest(), 16)

    def _repl_iterator(self, nodename):
        """Given a node name, return an iterable of replica hashes."""

        return (self._hash("%s:%s" % (nodename, i))
                for i in xrange(self.replicas))

    def __setitem__(self, nodename, node):
        """Add a node, given its name.

        The given nodename is hashed
        among the number of replicas.

        """
        for hash_ in self._repl_iterator(nodename):
            if hash_ in self._nodes:
                raise ValueError("Node name %r is "
                            "already present" % nodename)
            self._nodes[hash_] = node
            bisect.insort(self._keys, hash_)

    def __delitem__(self, nodename):
        """Remove a node, given its name."""

        for hash_ in self._repl_iterator(nodename):
            # will raise KeyError for nonexistent node name
            del self._nodes[hash_]
            index = bisect.bisect_left(self._keys, hash_)
            del self._keys[index]

    def __getitem__(self, key):
        """Return a node, given a key.

        The node replica with a hash value nearest
        but not less than that of the given
        name is returned.   If the hash of the
        given name is greater than the greatest
        hash, returns the lowest hashed node.

        """
        hash_ = self._hash(key)
        start = bisect.bisect(self._keys, hash_)
        if start == len(self._keys):
            start = 0
        return self._nodes[self._keys[start]]

if __name__ == "__main__":
    """
    Just a test for consistent hash.
    """
    cr = ConsistentHashRing(100)
    cr["node1"]="host_name1"
    cr["node2"]="host_name2"

    print "key located on node list:"
    for i in range(10):
        key="hello consistent hash"+str(i)
        print key, "==>", cr[key]
