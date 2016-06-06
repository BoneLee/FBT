# coding: utf-8
import json
from time import time

import tornado.httpserver
import tornado.ioloop
from tornado import gen, web
import tornado.options

#from tornado.options import options
import motorclient
from redis_sub_client import RedisSubClient

from resource_manager import ResourceStoreManager
from cipher import WaveCipher as Cipher
import util
from user_log import LogForUser
from fileNameSearcher import FileNameSearcher
from rpctcpserver import RPCTCPServer
from constant import SEARCH_RPC_SERVER_PORT
from util import add_download_info_to_resource_list, cipher_resource_list, getPages
from constant import RES_CNT_IN_A_PAGE, CHANNEL_RES_PASS, CHANNEL_RES_HIDDEN, CHANNEL_RES_REVEALED, PUB_SUB_HOST, PUB_SUB_PORT, PUB_SUB_PWD

log_db = motorclient.fbt_log
LogForUser.set_db(log_db)

# TODO: add sth

def write_RPC(types, error, result):
    return {"type": types,
                  "error": error,
                  "result": result}

def errorHandle_RPC(num):
    if num == 0:
        return write_RPC(0, "400", {})
    elif num == 1:
        return write_RPC(0, "sorry", {})


class ResRemoveSubcriber(RedisSubClient):
    """docstring for ResRemoveSubcriber"""
    def __init__(self, channel, host, port, passwd = None):
        super(ResRemoveSubcriber, self).__init__(channel, host, port, passwd)
    
    """msg =  {"file_id": file_id, "file_name": file_name}"""
    def msgHandler(self, msg) :
        try :
            resInfoDict = json.loads(msg)
        except ValueError, e :
            print e
        else :
            file_name = resInfoDict.get('file_name')
            file_id = resInfoDict.get('file_id')
            if file_id and file_name :
                print 'del:', file_name
                FileNameSearcher().remove_file_id_sync(file_id, file_name)

class ResPassSubcriber(RedisSubClient):
    """docstring for ResPassSubcriber"""
    def __init__(self, channel, host, port, passwd = None):
        super(ResPassSubcriber, self).__init__(channel, host, port, passwd)
    
    """msg =  {"file_id": file_id, "file_name": file_name, "uid": uid}"""
    def msgHandler(self, msg) :
        try :
            passInfoDict = json.loads(msg)
        except ValueError, e :
            print 'add error:', e
        else :
            file_name = passInfoDict.get('file_name')
            file_id = passInfoDict.get('file_id')
            if file_id and file_name :
                try:
                    print 'add: ', file_name
                except Exception, e:
                    print e
                FileNameSearcher().file_id_add_title_sync(file_id, file_name)

class MainHandler(tornado.web.RequestHandler):
    """ by type{by hot,by latest},by page """
    @web.asynchronous
    @gen.coroutine
    def post(self):
        version = self.get_argument("version","")
        user = self.get_argument("user", None) 
        page = self.get_argument("page", 1)
        sort_by = self.get_argument("sort_by", ResourceStoreManager.res_sort_by["time"])
        which_type = self.get_argument("type", None)
        private = self.get_argument("private", None)
        key_word = self.get_argument("key_word", "")
        try:
            user = long(user)
            page = int(page)
            assert page>0
            sort_by = int(sort_by)
            assert sort_by==ResourceStoreManager.res_sort_by["time"] or sort_by==ResourceStoreManager.res_sort_by["download_num"]
            sort_by = ResourceStoreManager.get_sort_item(sort_by)
            key_word=Cipher.decrypt(key_word).strip()
            assert len(key_word)>0
        except:
            util.errorHandle(self, 0)
            self.finish()
        else:
            if private and '1' == private:
                result = yield ResourceStoreManager.search_resources_private(user, version, key_word,page,sort_by,RES_CNT_IN_A_PAGE)
            else:
                result = yield ResourceStoreManager.search_resources(version, key_word,page,sort_by,RES_CNT_IN_A_PAGE)
            resource_list = result["res"]
            cipher_resource_list(resource_list, version)
            add_download_info_to_resource_list(resource_list)
            if version >= "1.8":
                util.write(self, 1, "", {"size": getPages(result["size"]), "res":resource_list})
            else:
                util.write(self, 1, "", resource_list)
            self.finish()
            yield LogForUser.log_user_search(user, long(time()), key_word, result["size"])

class MyRPCServer(RPCTCPServer):
    @gen.coroutine
    def search(self, version="", user=None, page=1, sort_by=ResourceStoreManager.res_sort_by["time"], key_word=""):
        try:
            user = long(user)
            page = int(page)
            assert page>0
            sort_by = int(sort_by)
            assert sort_by==ResourceStoreManager.res_sort_by["time"] or sort_by==ResourceStoreManager.res_sort_by["download_num"]
            sort_by = ResourceStoreManager.get_sort_item(sort_by)
            key_word=Cipher.decrypt(key_word).strip()
            assert len(key_word)>0
        except:
            raise gen.Return(errorHandle_RPC(0))
        else:
            RES_CNT_IN_A_PAGE=20
            result = yield ResourceStoreManager.search_resources(version, key_word,page,sort_by,RES_CNT_IN_A_PAGE)
            resource_list = result["res"]
            cipher_resource_list(resource_list, version)
            add_download_info_to_resource_list(resource_list)
            # Have to wait for log, TODO: change it!
            yield LogForUser.log_user_search(user, long(time()), key_word, result["size"])
            if version >= "1.8":
                raise gen.Return(write_RPC(1, "", {"size": getPages(result["size"]), "res":resource_list}))
            else:
                raise gen.Return(write_RPC(1, "", resource_list))

application = tornado.web.Application([
        (r'/res/search', MainHandler),
])

if __name__ == '__main__':
    #tornado.options.parse_command_line()
    #application.listen(options.port)
    application.listen(8891)
    server = MyRPCServer()    
    server.listen(SEARCH_RPC_SERVER_PORT)   
    rm_sub_client = ResRemoveSubcriber(CHANNEL_RES_HIDDEN, PUB_SUB_HOST, PUB_SUB_PORT,PUB_SUB_PWD)
    pass_sub_client = ResPassSubcriber(CHANNEL_RES_PASS, PUB_SUB_HOST, PUB_SUB_PORT,PUB_SUB_PWD)
    revealed_sub_client = ResPassSubcriber(CHANNEL_RES_REVEALED, PUB_SUB_HOST, PUB_SUB_PORT,PUB_SUB_PWD)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        rm_sub_client.close()
        pass_sub_client.close()
        revealed_sub_client.close()
        print "OK. Exit..."
