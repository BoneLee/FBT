#-*- coding:utf-8 -*-
import socket
import os

#from http://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python

def is_valid_ipv4_address(address):
    if address is None:
        return False
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def is_valid_ipv6_address(address):
    if address is None:
        return False
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True

if os.name != "nt":
    import fcntl
    import struct
    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print "get host error: host name is " + socket.gethostname()
        ip = "127.0.0.1"
    if ip.startswith("127.") and os.name != "nt":
        interfaces = ["eth1", "eth2", "eth0", "wlan0", "wlan1", "wifi0", "ath0", "ath1", "ppp0"]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

class HostsSetWrong(Exception):
    """ Warning: tornado hosts set wrong. host name must be hostXXXX. """
    pass

def get_hostname():
    host_name = socket.gethostname()
    if "fbt" not in host_name:
        # print "***************** Wrong host name: " + host_name + " ****************"
        raise HostsSetWrong("Wrong host name:"+host_name)
    return host_name
