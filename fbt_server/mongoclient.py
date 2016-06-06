import sys
import pymongo
from settings import mongo_machines, REPLICASET_NAME, FBT_USER, FBT_PASSWD

mode = None
def set_mode(m):
    global mode
    mode = m

class Wrapper:

    localhost = '127.0.0.1'
    port = 27017
    dbs = {'fbt': None}

    def __init__(self, module):
        self.module = module
        self._mongoclient = None

    def __getattr__(self, item):
        if item in self.dbs and self._mongoclient is None:
            if mode == 'test':
                self._mongoclient = pymongo.MongoClient(host=self.localhost,
                                                        port=self.port)
            else:
                self._mongoclient = pymongo.MongoReplicaSetClient(
                    ','.join(mongo_machines),
                    replicaSet=REPLICASET_NAME,
                )

	    	#print "+++++++++authing++++++++++"
	    	self._mongoclient.fbt.authenticate(FBT_USER, FBT_PASSWD)
	    	#print "+++++++++authing OK++++++++++"+str(ok)

            self.dbs['fbt'] = self._mongoclient.fbt
            self.module.__dict__.update(self.dbs)

        return getattr(self.module, item)

sys.modules[__name__] = Wrapper(sys.modules[__name__])
