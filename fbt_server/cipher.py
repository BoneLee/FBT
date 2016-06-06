# -*- coding: utf-8 -*-

__author__ = 'bone-lee'

import base64
#from Crypto import Random #not work in python2.6
#from Crypto.Cipher import AES
#import os
from time import time


class WaveCipher:
    @classmethod
    def encrypt(cls,data):
        return '~'.join(data)
        #map(ord,u'Hello, 马克')
        #[72, 101, 108, 108, 111, 44, 32, 39532, 20811]
        #splitter=ord('~')
        #wave_data=[splitter]
        #buffer=map(ord,data)
        #for x in buffer:
        #    wave_data.append(x)
        #    wave_data.append(splitter)
        #return ''.join(unichr(x) for x in wave_data)

    @classmethod
    def decrypt(cls,data):
        return data.replace('~','')


class XorCipher:
    @classmethod
    def encrypt(cls,data):
        buffer=map(ord,data.encode('utf-8'))
        #map(ord,u'Hello, 马克'.encode('utf8')) ==>[72, 101, 108, 108, 111, 44, 32, 233, 169, 172, 229, 133, 139]
        return base64.b64encode(''.join(chr(x ^ 123) for x in buffer))

    @classmethod
    def decrypt(cls,data):
        #buffer=map(lambda x: ord(x)^123, base64.b64decode(data))
        #return ''.join(map(chr,buffer)).decode('utf-8')
        return ''.join(chr(ord(x) ^ 123) for x in base64.b64decode(data)).decode('utf-8')

'''
class AESCipher:
    '
    Encrypt and decrypt with text.
    '
    default_key=(str(u'GFW吃屎！GFW吃屎！GFW吃屎！GFW吃屎！'.encode('utf-8')))[:32]

    def __init__(self, key=default_key):
        self.bs = 32
        if len(key) >= 32:
            self.key = key[:32]
        else:
            self.key = self._pad(key)

    def encrypt(self, raw):
        raw=str(raw.encode('utf-8')) #all text data are encoded with utf8
        raw = self._pad(raw)
        #iv = 'asdfasdfasdfasdf'#Random.new().read(AES.block_size)
        #print AES.block_size == 16
        #iv=os.urandom(AES.block_size)
        iv=(str(int(time()))+str(int(time())))[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return iv + base64.b64encode(cipher.encrypt(raw))

    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        enc = base64.b64decode(enc[AES.block_size:])
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc)).decode('utf-8') # all text data are decoded with utf8

    def _pad (self ,data):
        BLOCK_SIZE = AES.block_size
        pad = BLOCK_SIZE - len(data) % BLOCK_SIZE
        return data + pad * chr(pad)

    def _unpad (self, padded):
        pad = ord(padded[-1])
        return padded[:-pad]
'''

#print XorCipher.encrypt(u"FBT架构.png")
#print XorCipher.decrypt('PTkvneXNneX/VQsVHA==')
#print WaveCipher.encrypt(u"FBT架构.png")
#print WaveCipher.decrypt(u'~F~B~T~架~构~.~p~n~g~')

