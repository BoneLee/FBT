var http = require("http");
var urlLib = require("url");
var querystring = require('querystring');
var cipher = require('../fbtUtils/encrypt');
var path = require('path');
var request = require(path.join(global.exec_path, 'request'));

var startedServers = {};

function reportMe(host, port, config) {
    var host2 = cipher.encrypt(host);
    var port2 = cipher.encrypt(port.toString());
    var user2 = cipher.encrypt(config['fbtUser'].toString());
    var url = "http://" + config['fbtHost'] + ":" + config['fbtPort'] + '/report_http_server_info?' + querystring.stringify({
            ip: host2,
            port: port2,
            user: user2,
            version: 2.0
     });
    function req(error, response, body) {
        if (error) {
            global.socket.emit("net");
            global.log.info("report_http_server_info err, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + error);
        }
        else {
            try {
                var json = JSON.parse(body);
                if ('type' in json && json['type'] == 1) {
                    global.log.info("upload http server ip and host to server. host:" + host + " port:" + port);
                } else {
                    global.log.info("report_http_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
                }
            } catch (e) {
                global.log.info("report_http_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
            }
        }
    }
    request(url, req);
}

function start(route, handle, host, port, config) {
    function startNewServer() {
        function onRequest(request, response) {
            // we're not too busy!  let's process a request!
            var pathname = urlLib.parse(request.url).pathname;
            route(handle, pathname, response, request);
        }

        var server = http.createServer(onRequest);
        server.listen(port, host);
        server.on('listening', function (err) {
            global.log.info("Http server has started for host==>" + host + " port==>" + port);
            startedServers[host] = server;
            reportMe(host, port, config);
        });
        server.on('error', function (err) {
            if (err.code == 'EADDRINUSE') {
                global.log.info('Address in use, retrying...');
                setTimeout(function () {
                    server.listen(port, host);
                }, 10000); //retry to bound address for every 10 seconds
            } else {
                global.log.info('unknown http listen err:' + err);
            }
        });
    }

    if (host in startedServers) {
        try{
            startedServers[host].close(function () {
                global.log.info("Http server has stopped for host:" + host + " port:" + port);
                startNewServer();
            });
        }catch(e){
                global.log.info("Http server stopp error:"+e);
                startNewServer();
        }
    } else {
        startNewServer();
    }
}

exports.start = start;
