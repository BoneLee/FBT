var utils = require('../fbtUtils/fbtUtils');

var httpServer = require('./wrapper.js');
var tcpServer = require('./wrapper2.js');
var http = require('http');
var net = require('net');
var path = require('path');
var querystring = require('querystring');
var request = require(path.join(global.exec_path, 'request'));

//just a test
var ipUtil = require("./ipUtil");

function start(config) {
    if (config && ('fbtHost' in config) && ('fbtPort' in config) && ('fbtUser' in config)) {
        global.log.info("start detect local ip");
        var ipv4addrs = ipUtil.ipv4addrs;
        for (var i in ipv4addrs) {
            var ipv4address = ipv4addrs[i];
            global.log.info('private ipv4 address:' + ipv4address);
            if (ipv4address && isPrivateIPV4(ipv4address)) {
                //httpServer.runAt(ipv4address, 8884, config);//!!!IPv6 Port for Http server is 8886!!!
                tcpServer.runAt(ipv4address, 8885, config);
                break; //just a LAN IP is enough
            } else {
                global.log.info('It is not an private ipv4 address. IP:' + ipv4address);
            }
        }
        var hasV6 = false;
        var ipv6addrs = ipUtil.ipv6addrs;
        var validAddr = [];
        for (var index in ipv6addrs) {
            var ipv6address = ipv6addrs[index];
            global.log.info('public ipv6 address:' + ipv6address);
            if (ipv6address && isPublicIPV6(ipv6address)) {
                hasV6 = true;
                global.identify = ipv6address;
                httpServer.runAt(ipv6address, 8886, config);//!!!IPv6 Port for Http server is 8886!!!
                tcpServer.runAt(ipv6address, 8885, config);
                validAddr.push(ipv6address);
            } else {
                global.log.info('It is not an public ipv6 address. IP:' + ipv6address);
            }
        }
        if (!hasV6) {
            global.socket.emit('inform', "FBT检测到您的ipv6存在问题，可能会影响下载");
            global.isV4 = true;
        }
        if(validAddr.length > 0){
            reportTcpInfo(config, validAddr);
        }
        global.log.info('start local http server function invoke....');
    } else {
        global.log.info("Argument error! config should be {'fbtUser': xxx, 'fbtHost': xxx, 'fbtPort': 8888 }");
    }

    //function is useful for get lan or public external IP
    //对于获取独立IP非常有用
    function getLANIP(callback) {
        var socket = net.createConnection(config.fbtPort, config.fbtHost);//+'/request_local_ip');
        //var socket = net.createConnection(80, 'nodejs.org');
        socket.on('connect', function () {
            //global.log.info("%j",socket.address());
            //global.log.info("socket.remoteAddress:"+socket.remoteAddress);
            //global.log.info("socket.localAddress:"+socket.localAddress);
            callback(undefined, socket.address().address);//if is extern IP, it will return it. and if it is LAN, return LAN IP
            socket.end();
        });
        socket.on('error', function (e) {
            callback(e);
        });
    }
}


function reportTcpInfo(config, ipList) {
    var url = "http://" + config['fbtHost'] + ":" + config['fbtPort'] + '/report_tcp_server_info?' + querystring.stringify({
            ip_list: JSON.stringify(ipList),
            user: config['fbtUser'],
            version: 2.0
        });
    function req(error, response, body) {
        if (error) {
            global.log.info("report_tcp_server_info err, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + error);
        }
        else {
            try {
                var json = JSON.parse(body);
                if ('type' in json && json['type'] == 1) {
                    global.log.info("upload tcp server ip and host to server:"+body);
                } else {
                    global.log.info("report_tcp_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
                }
            } catch (e) {
                global.log.info("report_tcp_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
            }
        }
    }
    request(url, req);
}

function isPrivateIPV4(addr) {
    return addr.match(/^10\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
        addr.match(/^192\.168\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
        addr.match(/^172\.(1[6-9]|2\d|30|31)\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
        addr.match(/^127\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
        addr.match(/^169\.254\.([0-9]{1,3})\.([0-9]{1,3})/) != null;
}

function isPublicIPV6(addr) {
    if ((/^[Ff][Cc]00:/.test(addr) == false) && (/^[fF][eE]80:/.test(addr) == false)) {//addr is not private ipv6
        return /^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/.test(addr);
    } else {
        return false;
    }
}

exports.start = start;
exports.getDownloadingFiles = function() {
  return httpServer.getDownloadingFiles().concat(tcpServer.getDownloadingFiles());
};

