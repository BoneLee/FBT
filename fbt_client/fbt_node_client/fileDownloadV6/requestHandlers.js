var querystring = require("querystring"), fs = require("fs");
var url = require('url');

var util = require('util');
var path = require('path');
var mime = require(path.join(global.exec_path, 'mime'));

var utils = require('../fbtUtils/fbtUtils');
//var randomAccessFile = require(path.join(global.exec_path, 'random-access-file'));

var debug = 0;
var expireTimeOfFileHashes={};
var downloadFileNames={};
var MAX_DOWNLOAD_IN_UPDATE_TIME=10;
var UPDATE_TIME=10*1000;//60 seconds
var THREE_MINUTES=60;

function now(){
    return parseInt(new Date().getTime()/1000);
}

function clearInvalidFileHash(fileHash){
    delete expireTimeOfFileHashes[fileHash];
    delete downloadFileNames[fileHash];
}

function about(request, response) {
    var body = '<html>' +
        '<head>' +
        '<meta http-equiv="Content-Type" ' +
        'content="text/html; charset=UTF-8" />' +
        '</head>' +
        '<body>' +
        'Hello! It works!' +
        '</body>' +
        '</html>';
    response.writeHead(200, {"Content-Type": "text/html"});
    response.write(body);
    response.end();
}

var resourceDB = null;//set by file api

/*
 function getFilePathByHashFromDB(hash){
 utils.assert(hash.length > 0);
 var DB={};
 if(resourceDB){
 DB=resourceDB;
 }else{//fake DB
 DB={"123":"../my-share/sample.zip",
 "456":"../my-share/fav.mp3",
 "789":"F:/node-webkit-bin/my-sample/my-share/stallman.jpg",
 "0":"./cleanUp.js",
 "1":"./router.js",
 "2":"./run.js",
 "3":"./server.js"};
 }
 return DB[hash];
 }
 */

function getFilePathFromHash(hash, callback) {
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

/**
 * get header range like: Range: 0-123
 * return {start:0,end:123}
 */
function getHeaderRange(headerRange, totalSize) {
    var parts = headerRange.replace(/bytes=/, "").split("-");
    var partialstart = parts[0];
    var partialend = parts[1];
    var start = parseInt(partialstart);
    var end = partialend ? parseInt(partialend) : totalSize - 1;
    return {start: start, end: end};
}

/**
 * page 404
 */
function page404(response, content) {
    utils.assert(content.length > 0);
    response.writeHead(404, {'content-type': 'text/html'});
    response.end(content);
}

/**
 * refuse connection
 */
function refuseConnection(response) {
    response.writeHead(503);
    response.end();
}

function pipeFileStream(fileStream, response) {
    //fix memory leak bug
    /*
     http://grokbase.com/t/gg/nodejs/138kjyv011/memory-leak-on-http-chunked-fs-createreadstream-pipe-res
     https://groups.google.com/forum/#!topic/nodejs/A8wbaaPmmBQ
     https://groups.google.com/forum/#!topic/nodejs/wtmIzV0lh8o
     */
    fileStream.on('close', function () {
        response.destroy.bind(response);
    })
        .on('error', function () {
            response.destroy.bind(response);
        })
        .pipe(response)
        .on('close', fileStream.destroy.bind(fileStream))
        .on('error', fileStream.destroy.bind(fileStream));
}

function downloadFile(request, response) {
    var urlParts = url.parse(request.url, true);
    var query = urlParts.query;

    // request must has param file=xxx&size=xxx&hash=xxx
    // and they must in line with DB. if not, means the server return file info logic error.
    //var requestedFileName=query["file"];
    //var requestedFileSize=query["size"];
    var requestedFileHash = query["hash"];
    //global.window.console.log("filehash");
    //global.window.console.log(requestedFileHash);
    if (!requestedFileHash) {
        return page404(response, "hash argument not found");
    }
    //utils.assert(requestedFileName.length > 0);
    //utils.assert(requestedFileSize.length > 0);
    //utils.assert(requestedFileHash.length > 0);

    if(!(requestedFileHash in expireTimeOfFileHashes) && (Object.keys(expireTimeOfFileHashes).length >= MAX_DOWNLOAD_IN_UPDATE_TIME)){
        if(debug) global.log.info("REFUSE CONNECTION. requestedFileHash:"+requestedFileHash+" expireTimeOfFileHashes:"+JSON.stringify(expireTimeOfFileHashes));
        return refuseConnection(response);
    }
    expireTimeOfFileHashes[requestedFileHash]=now()+THREE_MINUTES;

    getFilePathFromHash(requestedFileHash, function getPathCallback(err, filePath) {
        //var filePath=getFilePathByHashFromDB(requestedFileHash);
        //global.window.console.log("filepath");
        //global.window.console.log(filePath);
        if (err || !filePath) {
            clearInvalidFileHash(requestedFileHash);
            return page404(response, "Resource not found. Maybe the user delete the file.");
        }

        var fileName = path.basename(filePath);
        downloadFileNames[requestedFileHash]=fileName;
        //utils.assert(fileName === requestedFileName,"DB error or logic error");

        //var file = __dirname + '/'+ filePath;
        filePath = utils.fbtNormalize(filePath);
        var exists = fs.existsSync(filePath);
        if (exists) {
            fs.stat(filePath, function fileSize(err, stats) {
                if (!err) {
                    var totalSize = stats.size;
                    //utils.assert(totalSize==requestedFileSize);
                    var mimetype = mime.lookup(filePath);
                    if (request.headers['range']) {
                        var range = getHeaderRange(request.headers.range, totalSize);
                        var start = range.start;
                        var end = range.end;
                        var chunksize = (end - start) + 1;
                        //global.log.info('RANGE: ' + start + ' - ' + end + ' = ' + chunksize);
                        //global.window.console.log("start");
                        //global.window.console.log(start+","+end+","+totalSize);
//                        utils.assert(start <= end);
//                        utils.assert(end < totalSize);
                        if(start>end || end>=totalSize){
                            if(debug) global.log.info("download client logic error. requestedFileHash:"+requestedFileHash+" expireTimeOfFileHashes:"+JSON.stringify(expireTimeOfFileHashes));
                            if(debug) global.log.info("debug info. start:"+start+" end:"+end+" chunk size:"+chunksize);
                            clearInvalidFileHash(requestedFileHash);
                            return refuseConnection(response)
                        }


                        /*
                        var f = randomAccessFile(filePath);
                        var contentRange = 'bytes ' + start + '-' + end + '/' + totalSize;
                        f.read(start, chunksize, function(err, buffer) {
                            response.writeHead(206, {'Content-Range': contentRange, 'Accept-Ranges': 'bytes', 'Content-Length': chunksize, 'Content-Type': mimetype});
                            response.write(buffer);
                            response.end();
                        });
                        f.close();
                        */

                        var fileStream = fs.createReadStream(filePath, {start: start, end: end, autoClose: true}); //maybe the autoClose: true will fix the memory leak
                        var contentRange = 'bytes ' + start + '-' + end + '/' + totalSize;
                        response.writeHead(206, {'Content-Range': contentRange, 'Accept-Ranges': 'bytes', 'Content-Length': chunksize, 'Content-Type': mimetype});
                        pipeFileStream(fileStream, response);
                    } else {
                        //下载的文件没有名字，后缀名怎么办？参考http报头Content-Disposition属性
                        response.writeHead(200, {'Content-Length': totalSize, 'Content-Type': mimetype, 'Content-disposition': 'attachment; fileName=' + fileName});
                        pipeFileStream(fs.createReadStream(filePath, {autoClose: true}), response);
                    }
                } else {
                    utils.assert(false, "logic err.");//file already exist. and download locally.
                }
            });
        } else {
            clearInvalidFileHash(requestedFileHash);
            return page404(response, "Resource not found. DB error. The user DB has not updated.");
        }
    });
}

function setResourceDB(DB) {
    utils.assert(DB);
    resourceDB = DB;
}

function getDownloadingFiles(){
    var res=[];
    for(var k in expireTimeOfFileHashes) {
        if(k in downloadFileNames) {
            res.push(downloadFileNames[k]);
        }
    }
    return res;
}

setInterval(function updateExpireTime() {
    for(var fileHash in Object.keys(expireTimeOfFileHashes)){
        var expireTime=expireTimeOfFileHashes[fileHash];
        var nowTime=now();
        if(nowTime > expireTime){
            clearInvalidFileHash(fileHash);
        }
    }
}, UPDATE_TIME);

exports.about = about;
exports.downloadFile = downloadFile;
exports.setResourceDB = setResourceDB;
exports.getDownloadingFiles = getDownloadingFiles;
