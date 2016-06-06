cp /var/lib/redis/* /home/fbt/redis-backup/

# # backup redis
# 0 4     * * *   fbt    sh /home/fbt/redis-backup/backup.sh