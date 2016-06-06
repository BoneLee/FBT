__author__ = 'bone-lee'

import ip_address as IP
from user_ip_cache import UserIPCache
from http_server_info_cache import HttpServerInfoCache, Address
from constant import CACHE_OWNER_OF_RESOURCE
from redis_cache_client import RedisCacheClient
from redis import TimeoutError

class DownloadMedium(object):
    download_type = {"None": 0, "V4_LAN": 1, "V4_NAT": 2, "V6": 3, "V4_NOT_ALLOW": 4}
    _redis_cache = RedisCacheClient().get_instance()

    @classmethod
    def get_online_owners_num_of_res(cls,file_id):
        try:
            return cls._redis_cache.scard(CACHE_OWNER_OF_RESOURCE + file_id)
        except TimeoutError as e:
            return 0

    @classmethod
    def get_online_owners_of_res(cls,file_id):
        return cls._redis_cache.smembers(CACHE_OWNER_OF_RESOURCE + file_id)

    @classmethod
    def get_matched_online_owners(cls, my_uid, res_users, allowV4Download=False, need_romove_self=False):
        assert my_uid > 0
        online_owners = filter(UserIPCache.user_online, res_users)
        if need_romove_self:
            if online_owners.count(my_uid):  # remove myself
                online_owners.remove(my_uid)
        if len(online_owners):
            if (UserIPCache.user_online(my_uid)):
                shouldCheckV4 = True
                my_ipv6_addrs = HttpServerInfoCache.get_user_ipv6(my_uid)
                if isinstance(my_ipv6_addrs, set):
                    assert len(my_ipv6_addrs) > 0
                    v6_owners = []
                    for user in online_owners:
                        v6_addrs = HttpServerInfoCache.get_user_ipv6(user)
                        if isinstance(v6_addrs, set):
                            for addr in v6_addrs:
                                if isinstance(addr, Address):
                                    assert IP.is_valid_ipv6_address(addr.get_host())
                                    v6_owners.append({"uid": user, "host": addr.get_host(), "port": addr.get_port()})
                                else:
                                    assert IP.is_valid_ipv6_address(addr)
                                    v6_owners.append({"uid": user, "host": addr, "port": 8886})
                    if len(v6_owners):
                        return {"owners": v6_owners, "download_type": cls.download_type["V6"]}
                    elif not allowV4Download:
                        shouldCheckV4 = False
                if shouldCheckV4:
                    my_ipv4 = UserIPCache.get_user_ip(my_uid)
                    assert IP.is_valid_ipv4_address(my_ipv4)
                    same_ip_users = filter(lambda user: UserIPCache.get_user_ip(user) == my_ipv4, online_owners)
                    if len(same_ip_users):  # LAN USER
                        v4_owners = []
                        for user in same_ip_users:
                            addr = HttpServerInfoCache.get_user_ipv4(user)
                            if addr is not None:
                                if isinstance(addr, Address):
                                    if IP.is_valid_ipv4_address(addr.get_host()):
                                        v4_owners.append(user)
                                else:
                                    if IP.is_valid_ipv4_address(addr):
                                        v4_owners.append(user)
                        grep_owners = []
                        for user in v4_owners:
                            addr = HttpServerInfoCache.get_user_ipv4(user)
                            if addr is not None:
                                if isinstance(addr, Address):
                                    grep_owners.append({"uid": user, "host": addr.get_host(), "port": addr.get_port()})
                                else:
                                    grep_owners.append({"uid": user, "host": addr, "port": 8884})
                        return {"owners": grep_owners, "download_type": cls.download_type["V4_LAN"]}
                    else:  # NAT USER #V4 user cant download v6's resource
                        return {"owners": [], "download_type": cls.download_type["None"]}
                        # TODO
                        # valid_v4_owners = [user for user in online_owners if
                        #                    IP.is_valid_ipv4_address(UserIPCache.get_user_ip(
                        #                        user))]  #and not isinstance(HttpServerInfoCache.get_user_ipv6(user),set)]
                        # grep_owners = [{"uid": user, "host": UserIPCache.get_user_ip(user), "port": 8884} for user in
                        #                valid_v4_owners]  #CAUTION: if user has a external IP, he cant open local LAN server. SO there must use get_user_ip, but not get_user_ipv4
                        # return {"owners": grep_owners, "download_type": cls.download_type["V4_NAT"]}
                else:
                    return {"owners": [], "download_type": cls.download_type["V4_NOT_ALLOW"]}
            else:
                return {"owners": [], "download_type": cls.download_type["None"]}
        else:
            return {"owners": [], "download_type": cls.download_type["None"]}

    # TODO fix download user has ipv6, but node websocket has a bug. Server can't send msg to client socket.
    # TODO So I allow all user download through ipv6.
    # TODO add unit test for download
    @classmethod
    def get_matched_online_owners2(cls, my_uid, res_users, allowV4Download=False, need_romove_self=False):
        assert my_uid > 0
        online_owners = filter(UserIPCache.user_online, res_users)
        if need_romove_self:
            if online_owners.count(my_uid):  # remove myself
                online_owners.remove(my_uid)
        if len(online_owners):
            #if (UserIPCache.user_online(my_uid)):
                shouldCheckV4 = True
                # my_ipv6_addrs = HttpServerInfoCache.get_user_ipv6(my_uid)
                # if isinstance(my_ipv6_addrs, set):
                #     assert len(my_ipv6_addrs) > 0
                v6_owners = []
                for user in online_owners:
                        v6_addrs = HttpServerInfoCache.get_user_ipv6(user)
                        if isinstance(v6_addrs, set):
                            for addr in v6_addrs:
                                if isinstance(addr, Address):
                                    assert IP.is_valid_ipv6_address(addr.get_host())
                                    v6_owners.append({"uid": user, "host": addr.get_host(), "port": addr.get_port()})
                                else:
                                    assert IP.is_valid_ipv6_address(addr)
                                    v6_owners.append({"uid": user, "host": addr, "port": 8886})
                if len(v6_owners):
                    return {"owners": v6_owners, "download_type": cls.download_type["V6"]}
                elif not allowV4Download:
                    shouldCheckV4 = False
                if shouldCheckV4:
                    my_ipv4 = UserIPCache.get_user_ip(my_uid)
                    assert IP.is_valid_ipv4_address(my_ipv4)
                    same_ip_users = filter(lambda user: UserIPCache.get_user_ip(user) == my_ipv4, online_owners)
                    if len(same_ip_users):  # LAN USER
                        v4_owners = []
                        for user in same_ip_users:
                            addr = HttpServerInfoCache.get_user_ipv4(user)
                            if addr is not None:
                                if isinstance(addr, Address):
                                    if IP.is_valid_ipv4_address(addr.get_host()):
                                        v4_owners.append(user)
                                else:
                                    if IP.is_valid_ipv4_address(addr):
                                        v4_owners.append(user)
                        grep_owners = []
                        for user in v4_owners:
                            addr = HttpServerInfoCache.get_user_ipv4(user)
                            if addr is not None:
                                if isinstance(addr, Address):
                                    grep_owners.append({"uid": user, "host": addr.get_host(), "port": addr.get_port()})
                                else:
                                    grep_owners.append({"uid": user, "host": addr, "port": 8884})
                        return {"owners": grep_owners, "download_type": cls.download_type["V4_LAN"]}
                    else:  # NAT USER #V4 user cant download v6's resource
                        return {"owners": [], "download_type": cls.download_type["None"]}
                        # TODO
                        # valid_v4_owners = [user for user in online_owners if
                        #                    IP.is_valid_ipv4_address(UserIPCache.get_user_ip(
                        #                        user))]  #and not isinstance(HttpServerInfoCache.get_user_ipv6(user),set)]
                        # grep_owners = [{"uid": user, "host": UserIPCache.get_user_ip(user), "port": 8884} for user in
                        #                valid_v4_owners]  #CAUTION: if user has a external IP, he cant open local LAN server. SO there must use get_user_ip, but not get_user_ipv4
                        # return {"owners": grep_owners, "download_type": cls.download_type["V4_NAT"]}
                else:
                    return {"owners": [], "download_type": cls.download_type["V4_NOT_ALLOW"]}
            #else:
            #    return {"owners": [], "download_type": cls.download_type["None"]}
        else:
            return {"owners": [], "download_type": cls.download_type["None"]}

    @classmethod
    def get_online_file_owner(cls, my_uid, file_id, allowV4Download=False,dir_id=None):
        my_uid = long(my_uid)
        assert my_uid >= 0
        if dir_id:
            fid = dir_id
        else:
            fid = file_id
        res_users = [long(uid) for uid in cls.get_online_owners_of_res(fid)]
        return cls.get_matched_online_owners2(my_uid, res_users, allowV4Download,True)


