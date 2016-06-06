#!/usr/bin/env bash

# mongo
sudo mongod -f /etc/mongod.conf --fork

# nginx
sudo nginx

sleep 10

/usr/bin/screen -dmS fb_rank bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fb_rank_main...;python fb_rank_main.py; sleep 3; exec bash'
/usr/bin/screen -dmS res_online bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start res_online...;python res_online_tornado.py; sleep 3; exec bash'
/usr/bin/screen -dmS res_search bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start res_search...;python resSearchTornado.py; sleep 3; exec bash'
/usr/bin/screen -dmS fbt_http1 bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fbt_http1...;sleep 5;python  fbt_http.py --port=8001; sleep 5; exec bash'
/usr/bin/screen -dmS fbt_http2 bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fbt_http2...;sleep 5;python  fbt_http.py --port=8002; sleep 5; exec bash'
/usr/bin/screen -dmS fbt_http3 bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fbt_http3...;sleep 5;python  fbt_http.py --port=8003; sleep 5; exec bash'
/usr/bin/screen -dmS fbt_http4 bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fbt_http4...;sleep 5;python  fbt_http.py --port=8005; sleep 5; exec bash'
/usr/bin/screen -dmS fbt_socket bash -c 'cd /home/fbt/latest_fbt_server_py/;echo will start fbt_socket...;sleep 10;python  fbt_socket.py --port=8006; sleep 5; exec bash'
