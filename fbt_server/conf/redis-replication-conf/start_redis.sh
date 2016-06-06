# 26381~26385 sentinel
#screen -dmS sent1 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-cache.conf;  exec bash'
#screen -dmS sent2 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-session.conf;  exec bash'
#screen -dmS sent3 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-search.conf;  exec bash'
#screen -dmS sent4 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-msg.conf;  exec bash'
#screen -dmS sent5 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-lru.conf;  exec bash'
#screen -dmS sent6 bash -c 'cd /home/fbt/redis-replication-conf/;sudo redis-sentinel sentinel-db.conf;  exec bash'

# slaveof
# master machine must start up first
slaveip=[]
masterip=[]
password=(123-fbt-all-cache-!@# 123-fbt-session-cache-!@# 123-fbt-search-cache-!@# 123-fbt-msg-cache-!@# 123-fbt-lru-cache-!@# 123-fbt-db-cache-!@#)
port=(6381 6382 6383 6384 6385 6386)
for i in 0 1 2 3 4 5
do
pwd=${password[$i]}
redis-cli -h $slaveip -p ${port[$i]} -a $pwd slaveof $masterip ${port[$i]}
done

# reset sentinel
#for i in 26381 26382 26383 26384 26385 26386
#do
#redis-cli -p ${port[$i]} sentinel reset cache-redis
#done
