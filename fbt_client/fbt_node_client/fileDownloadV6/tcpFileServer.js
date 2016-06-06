/**
 * Created by bone on 15-7-18.
 */

var DEBUG = false; // true for local test
var DETAILED = false;

var net = require('net'),
    fs = require('fs'),
    path = require('path');

if(DEBUG){
    utils = {
        fbtNormalize: function (filePath) {
            return filePath;
        }, assert: function(exp){
            return true;
        }
    };
    randomAccessFile = require('random-access-file');
}else{
    utils = require('../fbtUtils/fbtUtils');
    randomAccessFile = require(path.join(global.exec_path, 'random-access-file'));
}

var cipher = require('../fbtUtils/encrypt');
var querystring = require('querystring');

if (DEBUG) {
    request = require('request');
} else {
    request = require(path.join(global.exec_path, 'request'));
}

var EOF = new Buffer('\r\nEOF\r\n');
var MAX_CONNECTION = 32;

// globals
var resourceDB = null;//set by file api
var startedServers = {};
var downloadFileNames = {};
var fileStreams = {};

if(DEBUG){
    getFilePathFromHash = function (hash, callback) {
        var filePath = path.join(__dirname, 'fill.tar');
        callback(null, filePath);
    }
}
else{
   getFilePathFromHash = function (hash, callback) {
        //global.res_hash_collection
        resourceDB.findOne({'verify': parseInt(hash)}, function (err, doc) {
            if (err || doc === null) {
                callback(err);
            }
            else {
                callback(null, doc.path);
            }
        });
    }
}

function startServer(host, port, config) {
    function startNewServer() {
        var clientSockets = [];
        // Create a server instance, and chain the listen function to it
        // The function passed to net.createServer() becomes the event handler for the 'connection' event
        // The sock object the callback function receives UNIQUE for each connection
        var server = net.createServer(function (sock) {
            // We have a connection - a socket object is assigned to the connection automatically
            log2file('Connection in: ' + sock.remoteAddress + ':' + sock.remotePort);
            clientSockets.push(sock);
            log2file("clientSockets.length:"+clientSockets.length);
            if (clientSockets.length > MAX_CONNECTION) {
                if (DETAILED) log2file("Exceed max connection count. Drop it.");
                cleanUpSocket(sock);
                return;
            }

            var fileHash = null;
            var fileSize = 0;
            // Add a 'data' event handler to this instance of socket
            sock.on('data', function (data) {
                //if(DETAILED) log2file('DATA ' + sock.remoteAddress + ' length: ' + data.length + "=>"+data);
                try{
                    var json = JSON.parse(data);
                    var start = json["start"];
                    var blockID = json["blockID"];
                    var end = json["end"];
                    fileHash = json["hash"];
                    fileSize = json["size"];
                } catch(e){
                    log2file('http download from. abort it');
                    write2socket(sock, "NO SUPPORTED PROTOCOL", null, null);
                    cleanUpSocket(sock, fileHash);
                    return;
                }
                if (start > end) {
                    log2file('warning block start > end, clean it.');
                    cleanUpSocket(sock, fileHash);
                    return;
                }
                getFilePathFromHash(fileHash, function (err, filePath) {
                    if (err || !filePath) {
                        if (DETAILED) log2file("File not found in local DB:" + fileHash);
                        cleanUpSocket(sock, fileHash);
                        return;
                    }
                    var fileName = path.basename(filePath);
                    if (DETAILED) log2file("file: " + fileName + " hash:" + fileHash);
                    downloadFileNames[fileHash] = fileName;
                    filePath = utils.fbtNormalize(filePath);
                    var exists = fs.existsSync(filePath);
                    if (!exists) {
                        log2file("File not exist:" + fileHash +" handleResource404");
                        // 404 resource error
                        handleResource404(fileHash, fileSize, config);
                        cleanUpSocket(sock, fileHash);
                        return;
                    }
                    fs.stat(filePath, function fileSize(err, stats) {
                        if (err) {
                            if (DETAILED) log2file("File stat err:" + fileHash + " err:" + err);
                            cleanUpSocket(sock, fileHash);
                            return;
                        }
                        var totalSize = stats.size;
                        if (end >= totalSize) {
                            log2file('warning block end>total file size, clean it.');
                            cleanUpSocket(sock, fileHash);
                            return;
                        }
                        if (DETAILED) log2file('block start:' + start + " end:" + end + " =" + (end - start + 1));
                        /*
                        var readStream = fs.createReadStream(filePath, {start: start, end: end, autoClose: true});
                        readStream.on('data', function (data) {
                            //log2file("data length: "+data.length);
                            write2socket(sock, data, readStream, fileHash);
                        });
                        readStream.on('end', function () {
                            if (DETAILED) log2file('stream block EOF.');
                            write2socket(sock, EOF, null, fileHash);
                        });
                        readStream.on('error', function () {
                            if (DETAILED) log2file('stream data err.');
                            cleanUpSocket(sock, fileHash);
                        });
                        */
                        /*
                        sock.on('drain', function () {
                            // Resume the read stream when the write stream gets hungry
                            readStream.resume();
                        });
                        */
                        var file = null;
                        if (fileHash in fileStreams) {
                            file = fileStreams[fileHash];
                        }else{
                            file = randomAccessFile(filePath);
                            fileStreams[fileHash] = file;
                        }
                        //var file = randomAccessFile(filePath);
                        file.read(start, end-start+1, function(err, buffer) {
                            var header = new Buffer(4);
                            header.writeUInt32BE(blockID, 0);
                            /*
                            > buf.writeUInt32BE(1<<30,0)
                            undefined
                            > 1<<30
                            1073741824
                            > console.log(buf.readUInt32BE(0));
                            1073741824
                            */
                            write2socket(sock, header, null, fileHash);
                            write2socket(sock, buffer, null, fileHash);
                            write2socket(sock, EOF, null, fileHash);
                            /*
                            file.close(function() {
                                console.log('file is closed');
                            });
                            */
                            // TODO FIXME file descriptor leak bug
                        });
                    });
                });
            });

            sock.on('error', function(err){
                if(DETAILED) log2file("error in download:"+fileHash+" err:"+err);
                cleanUpSocket(sock, fileHash);
            });
            // Add a 'close' event handler to this instance of socket
            sock.on('close', function (data) {
                log2file("clear file hash:"+fileHash);
                cleanUpSocket(sock, fileHash);
                log2file("clientSockets.length:"+clientSockets.length);
            });
        });
        server.listen(port, host);

        server.on('listening', function (err) {
            startedServers[host] = server;
            log2file('TCP server has started for host==>'+host+' port==>'+port);
            reportMe(host, port, config);
        });
        
        server.on('error', function (err) {
            if (err.code == 'EADDRINUSE') {
                log2file('Address in use, retrying...');
                setTimeout(function () {
                    server.listen(port, host);
                }, 10000); //retry to bound address for every 10 seconds
            } else {
                log2file('unknown TCP listen err:' + err);
            }
        });
        /*
        server.close(function () {
            if(DETAILED) log2file("Http server has stopped for host:" + host + " port:" + port);
            // TODO restart
        });
        */

        function cleanUpSocket(sock, fileHash) {
            if (DETAILED) {
                if(sock.remoteAddress && sock.remotePort)
                    log2file('clean up socket: ' + sock.remoteAddress + ' ' + sock.remotePort);
            }
            sock.destroy();
            removeItemOfArray(clientSockets, sock);
            if(fileHash !== null){
                clearInvalidFileHash(fileHash);
                process.nextTick(function(){
                    if(fileHash in fileStreams){
                        log2file('close file :'+fileHash);
                        fileStreams[fileHash].close();
                        delete fileStreams[fileHash];
                    }
                });
            }
        }

        function removeItemOfArray(arr, item) {
            for (var i = arr.length; i--;) {
                if (arr[i] === item) {
                    arr.splice(i, 1);
                }
            }
        }

        function write2socket(sock, data, readStream, fileHash) {
            if (sock.writable) {
                var flushed = sock.write(data);
                // Pause the read stream when the write stream gets saturated
                //if (!flushed && readStream)
                //    readStream.pause();
            } else {
                cleanUpSocket(sock, fileHash);
            }
        }
    }
    if (host in startedServers) {
        try{
            startedServers[host].close(function () {
                log2file("tcp server has stopped for host:" + host + " port:" + port);
                startNewServer();
            });
        }catch(e){
            log2file("tcp server has stopped for host:" + host + " port:" + port+" error:"+e);
            startNewServer();
        }
    } else {
        startNewServer();
    }
}

function setResourceDB(DB) {
    utils.assert(DB);
    resourceDB = DB;
}

function reportMe(host, port, config) {
    if(!config){
        log2file("Not found config. Please set it.");
        return;
    }
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
            log2file("report_tcp_server_info err, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + error);
        }
        else {
            try {
                var json = JSON.parse(body);
                if ('type' in json && json['type'] == 1) {
                    log2file("upload tcp server ip and host to server. host:" + host + " port:" + port);
                } else {
                    log2file("report_tcp_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
                }
            } catch (e) {
                log2file("report_tcp_server_info, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
            }
        }
    }
    request(url, req);
}

function handleResource404(fileHash, fileSize, config) {
    var fileID = fileHash.toString()+"_"+fileSize;
    if(!config){
        log2file("Not found config. Please set it. fileID:"+fileID);
        return;
    }
    var uid = config['fbtUser'];
    var url = "http://" + config['fbtHost'] + ":" + config['fbtPort'] + '/resource404?' + querystring.stringify({
        'user': uid,
        'file_id': fileID
     });
    function req(error, response, body) {
        try {
            var json = JSON.parse(body);
            if ('err' in json && json['err'] == 0) {
                log2file("handleResource404 OK, fileID:" + fileID + " uid:" + uid);
            } else {
                log2file("handleResource404 json err:"+body);
            }
        } catch (e) {
            log2file("handleResource404 error, host:" + config['fbtHost'] + " port:" + config['fbtPort'] + " err:" + body);
        }
    }
    request(url, req);
}

function getDownloadingFiles(){
    return Object.keys(downloadFileNames).map(function(key){
        return downloadFileNames[key];
    });
}

function clearInvalidFileHash(fileHash){
    delete downloadFileNames[fileHash];
}

function test(){
    startServer('127.0.0.1', 8885);
    startServer('::1', 8885);
    setTimeout(function() {
        startServer('127.0.0.1', 8885);
        startServer('::1', 8885);
    }, 1000);
    var server = net.createServer(function (sock) {});
    server.listen(8880, 'localhost'); // for test time out
    setInterval(function(){log2file(JSON.stringify(getDownloadingFiles()));}, 2000);
}

function log2file(content){
    if(DEBUG){
        console.log("TCP server:"+content);
    }else{
        global.log.info("TCP server:"+content);
    }
}

if(DEBUG){
    test();
}

exports.setResourceDB = setResourceDB;
exports.startServer = startServer;
exports.getDownloadingFiles = getDownloadingFiles;
