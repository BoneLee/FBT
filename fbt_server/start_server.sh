#!/usr/bin bash
sudo redis-server /etc/redis/redis-search.conf
sudo redis-server /etc/redis/redis-token.conf
sudo redis-server /etc/redis/redis-cache.conf
sudo redis-server /etc/redis/redis-pub.conf