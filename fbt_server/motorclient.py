import sys
import motor
from settings import mongo_machines, REPLICASET_NAME, FBT_USER, FBT_PASSWD
from pymongo import ReadPreference
import tornado.ioloop
import tornado.gen
from time import time

print(','.join(mongo_machines))


mode = None
def set_mode(m):
    global mode
    mode = m

class Wrapper:

    localhost = '127.0.0.1'
    port = 27017
    dbs = {
        'fbt': None,
        'reward': None,
        'fbt_realtime': None,
        'fbt_test': None,
        'fbt_log': None
    }

    def __init__(self, module):
        self.module = module
        self._motorclient = None
        self._motorclient_realtime = None

    def __getattr__(self, item):
        if item in self.dbs and self._motorclient is None:
            if mode == 'test':
                self._motorclient = motor.MotorClient(host=self.localhost,
                                                      port=self.port)
                self._motorclient_realtime = self._motorclient
            else:
                self._motorclient = motor.MotorReplicaSetClient(
                    ','.join(mongo_machines),
                    replicaSet=REPLICASET_NAME,
                    readPreference=ReadPreference.NEAREST)

                self._motorclient_realtime = motor.MotorReplicaSetClient(
                    ','.join(mongo_machines),
                    replicaSet=REPLICASET_NAME,
                    readPreference=ReadPreference.PRIMARY)

                ioloop=tornado.ioloop.IOLoop.instance()
                @tornado.gen.coroutine
                def auth_db():
                    yield self._motorclient.open()
                    yield self._motorclient_realtime.open()
                    #print "+++++++++authing++++++++++"
                    yield self._motorclient.fbt_log.authenticate(FBT_USER, FBT_PASSWD)
                    yield self._motorclient_realtime.fbt.authenticate(FBT_USER, FBT_PASSWD)
                    yield self._motorclient.fbt.authenticate(FBT_USER, FBT_PASSWD)
                    yield self._motorclient.fbt_reward.authenticate(FBT_USER, FBT_PASSWD)
                    #print "+++++++++authing OK++++++++++"+str(ok)
                    #ioloop.run_sync(f)
                    #ioloop.add_timeout(time() + 1, lambda: ioloop.run_sync(f))
                ioloop.add_future(auth_db(), lambda future: True)

            self.dbs['fbt'] = self._motorclient.fbt
            self.dbs['reward'] = self._motorclient.fbt_reward
            self.dbs['fbt_realtime'] = self._motorclient_realtime.fbt
            #self.dbs['fbt_test'] = self._motorclient_realtime.fbt_test
            self.dbs['fbt_log'] = self._motorclient.fbt_log
            self.module.__dict__.update(self.dbs)

        return getattr(self.module, item)

sys.modules[__name__] = Wrapper(sys.modules[__name__])
