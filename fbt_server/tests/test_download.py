__author__ = 'bone-lee'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from user_ip_cache import UserIPCache
from http_server_info_cache import HttpServerInfoCache
from redis_proxy import RedisProxy
from download_medium import DownloadMedium

import tornado.gen
import tornado.testing
import redis

def mock_file_hash(file_name):
    return str(abs(hash(file_name)))

class DownloadTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test
    def test_download_ipv4_lan(self):
        client = redis.StrictRedis()
        client.flushdb()
        r = RedisProxy(redis_client=client)
        UserIPCache.set_cache(r)
        UserIPCache.reset()

        online_users = []
        # user offline
        my_uid = 1234
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        # user online but has no owners
        ip = "1.1.1.1"
        UserIPCache.update_my_ip(my_uid, ip)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        # user just see himself
        online_users = [my_uid, ]
        lan_ip = "192.168.0.1"
        port = 8885
        HttpServerInfoCache.update_ipv4_address(my_uid, lan_ip, port)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, False)
        self.assertEqual(ret, {'owners': [{'host': lan_ip, 'uid': my_uid, 'port': port}], 'download_type': DownloadMedium.download_type["V4_LAN"]})
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        his_uid = 4321
        UserIPCache.update_my_ip(his_uid, ip)
        his_lan_ip = "192.168.0.2"
        his_port = 8884
        HttpServerInfoCache.update_ipv4_address(his_uid, his_lan_ip, his_port)
        online_users.append(his_uid)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [{'host': his_lan_ip, 'uid': his_uid, 'port': his_port}], 'download_type': DownloadMedium.download_type["V4_LAN"]})

        her_uid = 5678
        UserIPCache.update_my_ip(her_uid, ip)
        her_lan_ip = "192.168.0.1"
        her_port = 8885
        HttpServerInfoCache.update_ipv4_address(her_uid, her_lan_ip, her_port)
        online_users.append(her_uid)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [{'host': his_lan_ip, 'uid': his_uid, 'port': his_port},
                                          {'host': her_lan_ip, 'uid': her_uid, 'port': her_port},
                                          ], 'download_type': DownloadMedium.download_type["V4_LAN"]})


    @tornado.testing.gen_test
    def test_download_ipv6(self):
        client = redis.StrictRedis()
        client.flushdb()
        r = RedisProxy(redis_client=client)
        UserIPCache.set_cache(r)
        UserIPCache.reset()

        online_users = []
        # user offline
        my_uid = 12345
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        # user online but has no owners
        ip = "1.1.1.1"
        UserIPCache.update_my_ip(my_uid, ip)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        # user just see himself
        online_users = [my_uid, ]
        v6_ip = "2001::1"
        port = 8885
        HttpServerInfoCache.update_ipv6_address(my_uid, v6_ip, port)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, False)
        self.assertEqual(ret, {'owners': [{'host': v6_ip, 'uid': my_uid, 'port': port}], 'download_type': DownloadMedium.download_type["V6"]})
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [], 'download_type': DownloadMedium.download_type["None"]})

        his_uid = 54321
        his_ip = '2.2.2.2'
        UserIPCache.update_my_ip(his_uid, his_ip)
        his_v6_ip = "2001::2"
        his_port = 8886
        HttpServerInfoCache.update_ipv6_address(his_uid, his_v6_ip, his_port)
        online_users.append(his_uid)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [{'host': his_v6_ip, 'uid': his_uid, 'port': his_port}], 'download_type': DownloadMedium.download_type["V6"]})

        her_uid = 56789
        her_ip = '3.3.3.3'
        UserIPCache.update_my_ip(her_uid, her_ip)
        her_v6_ip = "2001::3"
        her_port = 8885
        HttpServerInfoCache.update_ipv6_address(her_uid, her_v6_ip, her_port)
        online_users.append(her_uid)
        ret = DownloadMedium.get_matched_online_owners(my_uid, online_users, False, True)
        self.assertEqual(ret, {'owners': [{'host': his_v6_ip, 'uid': his_uid, 'port': his_port},
                                          {'host': her_v6_ip, 'uid': her_uid, 'port': her_port},
                                          ], 'download_type': DownloadMedium.download_type["V6"]})


if __name__ == '__main__':
    import unittest
    unittest.main()
