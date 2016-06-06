__author__ = 'bone-lee'

import ip_address as IP
import cPickle as pickle
import os
import logging

class Address(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def get_host(self):
        return self._host

    def get_port(self):
        return self._port

    def __eq__(self, another):
        return self._port == another._port and self._host == another._host

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return self._host+"="+str(self._port)

class HttpServerInfoCache(object):
    _http_server_info = dict()  # such as {fbt_user1: {ipv4:xxx.xxx.xxx.xxx, ipv6: xx:xx:xx:xx},fbt_user2:{ipv4:xxx,ipv6:xxx}}

    @classmethod
    def update_ipv4_address(cls, user, ip, port):
        assert user >= 0
        assert IP.is_valid_ipv4_address(ip)
        addr = Address(ip, port)
        if user in cls._http_server_info:
            cls._http_server_info[user]["ipv4"] = addr
        else:
            cls._http_server_info[user] = {"ipv4": addr, "ipv6": None}

    @classmethod
    def update_ipv6_address(cls, user, ip, port):
        assert user >= 0
        assert IP.is_valid_ipv6_address(ip)
        addr = Address(ip, port)
        if user in cls._http_server_info:
            if isinstance(cls._http_server_info[user]["ipv6"],set):
                cls._http_server_info[user]["ipv6"].add(addr) # multiple ipv6 address
            else:
                cls._http_server_info[user]["ipv6"]=set([addr])
        else:
            cls._http_server_info[user] = {"ipv6": set([addr]), "ipv4": None}

    @classmethod
    def get_server_info(cls):
        return cls._http_server_info

    @classmethod
    def get_user_ipv4(cls, user):
        assert user >= 0
        if user in cls._http_server_info:
            return cls._http_server_info[user]["ipv4"]
        else:
            return None

    @classmethod
    def get_user_ipv6(cls, user):
        assert user >= 0
        if user in cls._http_server_info:
            return cls._http_server_info[user]["ipv6"]
        else:
            return None

    @classmethod
    def delete_user(cls, user):
        assert user >= 0
        if user in cls._http_server_info:
            del cls._http_server_info[user]

    @classmethod
    def _get_pkl_file(cls, port):
        file_name = "http_server_info_"+str(port)+".pkl"
        return file_name

    @classmethod
    def load(cls, port):
        file_name = cls._get_pkl_file(port)
        if os.path.isfile(file_name):
            with open(file_name,'r+') as infile:
                cls._http_server_info = pickle.load(infile)
                logging.info("load http server info from local file")

    @classmethod
    def save(cls, port):
        file_name = cls._get_pkl_file(port)
        with open(file_name, 'wb') as outfile:
            pickle.dump(cls._http_server_info, outfile)
            logging.info("save http server info to local file")
