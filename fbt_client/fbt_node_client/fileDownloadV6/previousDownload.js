/**
 * Created by bone-lee on 15-4-11.
 */

var http = require('http');
var fs = require('fs');
var path = require('path');
var randomAccessFile = require(path.join(global.exec_path,'random-access-file'));
var querystring = require('querystring');
var utils = require('../fbtUtils/fbtUtils');

// loads module and registers app specific cleanup callback...
var cleanup = require('../fbtUtils/cleanUp');

// defines app specific callback...
// place app specific cleanup code here
function myCleanup() {
    //backup download state
    saveDownloadState();
    saveDownloadOwner();
}
cleanup.registerClean(myCleanup);
//setInterval(myCleanup,60000);

//TODO
//set by experiment
var BLOCK_INCREASED = 1;
var config = { BLOCK_SIZE: 1024 * 1024 * BLOCK_INCREASED, //1M
    MAX_HTTP_CONNECTION_CNT: 60, //100? //30=~2.5MB
    STATE_FILE: path.join(global.fbt, 'downloadState.json'),
    OWNER_FILE: path.join(global.fbt, 'downloadOwner.json')
};//set to current path

var errTips={"duplicatedDownload":1,"historyDownload":2,"spaceFull":3,"invalidOwners":4,"unknown":5,"remove":6};
var tempSuffix=".tmp";

var DownloadState = {DOWNLOAD_OVER: 0, DOWNLOADING: 1, CANCELED: 2, PAUSED: 3, DOWNLOAD_ERR: 4};
/* state machine
 *
 |  -------------------------------------|
 \|/                                      |
 DOWNLOAD_OVER--------user click download again---->
 /|\
 | all file blocks downloaded ok
 begin file download-------->DOWNLOADING-----------user click pause----------->PAUSED-------user click resume--->
 /|\                                                                                |
 |                                                                                 |
 ---------------------------------------------------------------------------------
 if user removes the  file download, set the download state to CANCELED.
 if error occurs while downloading, set the download state to DOWNLOAD_ERR.
 */

var fileBlocksDownloadLeft = {};
var fileBlocksDownloading = {};
var fileBlocksDownloadOwners = {};
var fileDownloadStates = {}; //the download state of every file
var fileDownloadOverCallbacks = {};
var downloadProgressCallbacks = {};
var downloadHttpConnectionCnt = {};
var downloadErrCallbackInvoked = {};
var downloadOKCallbackInvoked = {};
var availableFileOwners = {};//all file keeper are store here
var filesToSave = {};
var filesStream = {};
var fileDownloadInfos = {};
var invalidDownloadOwners={};
var downloadBlockTimeAt={};
var fileDownloadEventEmitter = {};
//store all the http request, and aborted all when cancel,the key is fileHash+fileSize
var allHttpDownload = {};
try{
    loadDownloadState();
    loadDownloadOwner();
}catch(e){}

function inArray(arr, data) {
    for(var i=0;i<arr.length;i++) {
        if(JSON.stringify(arr[i]) === JSON.stringify(data)) return true;
    }
    return false;
}

function fileBlocks(fileSize) {
    return Math.floor((fileSize + config.BLOCK_SIZE - 1) / config.BLOCK_SIZE);
}

function loadDownloadState() {
    if (fs.existsSync(config.STATE_FILE)) {
        var data = fs.readFileSync(config.STATE_FILE);
        fileBlocksDownloadLeft = JSON.parse(data);
    }
}

function loadDownloadOwner() {
    if (fs.existsSync(config.OWNER_FILE)) {
        var data = fs.readFileSync(config.OWNER_FILE);
        fileBlocksDownloadOwners = JSON.parse(data);
    }
}

function saveDownloadState() {
    fs.writeFileSync(config.STATE_FILE, JSON.stringify(fileBlocksDownloadLeft, null, 2));
}

function saveDownloadOwner() {
    fs.writeFileSync(config.OWNER_FILE, JSON.stringify(fileBlocksDownloadOwners, null, 2));
}
function cancelAllSpecificDownload(fileHash, fileSize){
    /*var key = ""+fileHash+fileSize;
    if(key in allHttpDownload){
        var cancelOb = allHttpDownload[key];
        for(var i = 0; i < cancelOb.length; i++){
            cancelOb[i].abort();
        }
        delete allHttpDownload[key];
    }*/
}
/**
 * download a file.
 *
 * arguments:
 * fileHash: the file hash
 *
 */
function downloadFile(fileInfo, fileOwners, downloadEventEmitter, downloadOverCallback, downloadProgressCallback) {
    utils.assert(fileInfo['size'] > 0);
    utils.assert(fileInfo['hash'] > 0);
    var fileHash = fileInfo['hash'];
    var savedFile = fileInfo['file_to_save'];
    utils.assert(savedFile.length > 0);
    filesToSave[fileHash] = savedFile;
    filesStream[fileHash] = randomAccessFile(savedFile+tempSuffix);
    var downloadCallback = downloadOverCallback;

    var totalBlocksNum = fileBlocks(fileInfo['size']);
    var noSpeed=0;

    // not allowed duplicated file download
//    if (fileHash in fileDownloadStates) {
//        if (fileDownloadStates[fileHash] == DownloadState.DOWNLOAD_OVER) { //the file download has been already over
//            downloadProgressCallback(totalBlocksNum * config.BLOCK_SIZE, 1.0, noSpeed); //set progress 100%
//            //downloadCallback(null, filesToSave[fileHash],fileHash);
//            downloadCallback(errTips["duplicatedDownload"], filesToSave[fileHash],fileHash);//leave to controler
//            global.log.info('found duplicated download. downloadOK event. fileHash:' + fileHash);
//            downloadEventEmitter.emit("downloadOK", fileHash);
//            return;
//        } else
//        if (fileDownloadStates[fileHash] == DownloadState.PAUSED) {//user pause download
//            return;
//        }
//    }
    fileDownloadStates[fileHash] = DownloadState.DOWNLOADING;//the file is processing

    global.log.info('download fileHash:' + fileHash);
    utils.assert(utils.len(fileOwners) > 0);

    var fileBlocksCnt = totalBlocksNum;
    if (fileHash in fileBlocksDownloadLeft) {// useful for resume download
        //use history download blocks
        if (fileBlocksDownloadLeft[fileHash].length == 0) {//history download file OK
            if (fs.existsSync(savedFile)) {//if file download OK
                fileDownloadStates[fileHash] = DownloadState.DOWNLOAD_OVER;
                downloadProgressCallback(totalBlocksNum * config.BLOCK_SIZE, 1.0, noSpeed); //set progress 100%
                downloadCallback(null,filesToSave[fileHash],fileHash,"");//history download leave to controler
                global.log.info('found history download. downloadOK event. fileHash:' + fileHash);
                downloadEventEmitter.emit("downloadOK", fileHash);
                return;
            } else {
                fileBlocksDownloadLeft[fileHash] = utils.range(0, fileBlocksCnt);//re download the file
                global.log.info('found history download. but the user change file path. fileHash:' + fileHash);
            }
        } else {//history download
            if (fs.existsSync(savedFile+tempSuffix)) {//if file download OK
                global.log.info("discover history download...");
                var progress = (1 - fileBlocksDownloadLeft[fileHash].length / totalBlocksNum).toFixed(4); //%.2f
                var downloadedBlocks = totalBlocksNum - fileBlocksDownloadLeft[fileHash].length;
                utils.assert(downloadedBlocks >= 0 && progress >= 0);
                downloadProgressCallback(downloadedBlocks * config.BLOCK_SIZE, progress, noSpeed);//report progress
            }else{
                fileBlocksDownloadLeft[fileHash] = utils.range(0, fileBlocksCnt);//record the download state
            }
        }
    } else {//new download
        fileBlocksDownloadLeft[fileHash] = utils.range(0, fileBlocksCnt);//record the download state
    }

    fileBlocksDownloading[fileHash]=[];//init
    utils.assert(utils.isFunction(downloadCallback));//must provide callback
    utils.assert(utils.isFunction(downloadProgressCallback));//must provide callback

    //init globals
    fileDownloadOverCallbacks[fileHash] = downloadCallback;
    downloadProgressCallbacks[fileHash] = downloadProgressCallback;
    fileDownloadInfos[fileHash] = fileInfo;//for resume download
    fileDownloadEventEmitter[fileHash] = downloadEventEmitter;
    availableFileOwners[fileHash] = fileOwners;//store the file owners
    downloadErrCallbackInvoked[fileHash] = false;
    downloadOKCallbackInvoked[fileHash] = false;
    downloadBlockTimeAt[fileHash]=Date.now();

    var concurrentHttpCnt = Math.min(fileBlocksCnt, config.MAX_HTTP_CONNECTION_CNT);//oops maybe a bug
    concurrentHttpCnt = Math.min(concurrentHttpCnt, fileOwners.length);//MAYBE this is better for just has 1 owners
    global.log.info("concurrentHttpCnt:" + concurrentHttpCnt);
    downloadHttpConnectionCnt[fileHash] = concurrentHttpCnt;
    allHttpDownload[""+fileHash+fileInfo['size']] = [];
    for (var blockID = 0; blockID < concurrentHttpCnt; ++blockID) {
        downloadBlock(fileInfo, savedFile, blockID, downloadEventEmitter);
    }
}


function downloadBlock(fileInfo, localFile, blockID, downloadEventEmitter) {
    var fileHash = fileInfo['hash'];
    //utils.assert(fileHash in fileDownloadStates);
    if (!(fileHash in fileDownloadStates)) {//file download canceled
        global.log.info('file download pause or canceled...');
        return;
    }
    switch (fileDownloadStates[fileHash]) {
        case DownloadState.PAUSED://file download pause
            //case DownloadState.CANCELED://file download canceled
            global.log.info('file download paused...');
            return;
        case DownloadState.DOWNLOADING://file download canceled
            break;
        case DownloadState.DOWNLOAD_OVER://file download canceled
        case DownloadState.DOWNLOAD_ERR://file download canceled
        default:
            utils.assert("logic error");
    }

    utils.assert(fileHash in fileBlocksDownloadLeft && fileHash in availableFileOwners);
    var fileDownloadCallback = fileDownloadOverCallbacks[fileHash];
    var downloadProgressCallback = downloadProgressCallbacks[fileHash];
    var fileOwners = availableFileOwners[fileHash];
    if (fileOwners.length == 0) {
        utils.assert(fileBlocksDownloadLeft[fileHash].length > 0);//must download fail
    //try to continue downloading
    if((fileHash in invalidDownloadOwners) && (invalidDownloadOwners[fileHash].length>0)){
                global.log.info('file download error! No fileOwners! fileHash:' + fileHash+". BUT I will try to rescue the downloading: owners==>"+JSON.stringify(invalidDownloadOwners[fileHash]));
          process.nextTick(function(){
        downloadFile(fileInfo,invalidDownloadOwners[fileHash],fileDownloadEventEmitter[fileHash],fileDownloadOverCallbacks[fileHash],downloadProgressCallbacks[fileHash]);
          });
        return;
    }

        if (!downloadErrCallbackInvoked[fileHash]) {
            global.log.info('file download error! No fileOwners! downloadErr event. fileHash:' + fileHash);
            fileDownloadCallback(errTips["invalidOwners"],fileHash);//history download leave to controler
            downloadEventEmitter.emit("downloadErr", fileHash);
            downloadErrCallbackInvoked[fileHash] = true;
        }
        fileDownloadStates[fileHash] = DownloadState.DOWNLOAD_ERR;
        return;
    }

    var owner = utils.randomChoose(fileOwners);//random choose the file keeper. what if the owner is invalid???
    utils.assert('host' in owner && 'port' in owner && 'uid' in owner);

    var fileSize = fileInfo['size'];
    var totalBlocksNum = fileBlocks(fileSize);
    if (blockID >= totalBlocksNum) return;

    if(!inArray(fileBlocksDownloadLeft[fileHash],blockID)){//this block has been downloaded
        var nextBlockID = blockID + downloadHttpConnectionCnt[fileHash];// config.MAX_HTTP_CONNECTION_CNT;
        if (nextBlockID >= totalBlocksNum){
        if(fileBlocksDownloadLeft[fileHash].length>0) {
            var index=fileBlocksDownloadLeft[fileHash].length-1;
            while(index>=0 && inArray(fileBlocksDownloading[fileHash],fileBlocksDownloadLeft[fileHash][index])){
                index-=1;
            }
            if(index>=0){
                 nextBlockID=fileBlocksDownloadLeft[fileHash][index];
                        //global.log.info('fileHash:' + fileHash+" I will ACC the dowload nextBlockID:"+nextBlockID+" totalBlocksNum:"+totalBlocksNum);
            }
            else{
                 return;
            }
        }else{
            return;
        }
    }
        utils.assert(nextBlockID < totalBlocksNum);
                                           process.nextTick(function(){
                                        downloadBlock(fileInfo, localFile, nextBlockID, downloadEventEmitter);
                                          });
        return;
    }

    if(!inArray(fileBlocksDownloading[fileHash],blockID)){
       fileBlocksDownloading[fileHash].push(blockID);
    }else{//the block need be download again.
    //utils.assert(false);
    }

    var start = blockID * config.BLOCK_SIZE;
    var end = blockID * config.BLOCK_SIZE + config.BLOCK_SIZE - 1;
    if (end >= fileSize) end = fileSize - 1;

    var options = {
        hostname: owner['host'],
        port: owner['port'],
        path: '/download?' + querystring.stringify({"hash": fileHash}),//use hash of the file to identify the file
        method: 'GET',
        headers: {"Range": start + "-" + end}
    };

    var chunks = [];
    var dataHasCome=false;
    var httpWritingStream = http.get(options, function (response) {
        response.on('data', function (chunk) {
            if(!dataHasCome){
                downloadBlockTimeAt[fileHash]=Date.now();
                dataHasCome=true;
            }
            chunks.push(chunk);
        });

        var errorOccur = 0;
        response.on('error', function (err) {
            errorOccur = 1;
        });

        response.on('close', function () {// event emit when the server has stopped! may not follow with end event!
            global.log.info('**************close ....');
            if (errorOccur) {
                global.log.info("http get response err:" + err);
                global.log.info('fileHash:' + fileHash + ' remove ower uid:' +owner["uid"] +" ip:"+owner["host"]);
                utils.removeArrayItem(availableFileOwners[fileHash], owner);//this file owner is invalid
                    process.nextTick(function(){
                    downloadBlock(fileInfo, localFile, blockID, downloadEventEmitter);//go on download this block
                    });
            }
        });

        response.on('end', function () {// event emit when all data has come out!
            //I guess the main time consuming logic is here
            if (!(fileHash in fileDownloadStates)) {//file download canceled
                global.log.info('file download pause or canceled...');
                return;
            }
            switch (fileDownloadStates[fileHash]) {
                case DownloadState.PAUSED://file download pause
                    //case DownloadState.CANCELED://file download canceled
                    global.log.info('file download paused...');
                    return;
                case DownloadState.DOWNLOADING://file download canceled
                    break;
                case DownloadState.DOWNLOAD_OVER://file download canceled
                case DownloadState.DOWNLOAD_ERR://file download canceled
                default:
                    utils.assert("logic error");
            }

            var chunksData = Buffer.concat(chunks);
              chunks=null;

            var diffDownloadTime=(Date.now()-downloadBlockTimeAt[fileHash])/1000;
            var downloadSpeed= chunksData.length/diffDownloadTime;
            if(isNaN(downloadSpeed)|| downloadSpeed==Infinity){
                downloadSpeed=0;
            }
            downloadSpeed=downloadSpeed.toFixed(2);

            if ((response.statusCode == 404) || (chunksData.length != (end-start+1))){
                if(response.statusCode==404){
                    global.log.info('Warning: 404 page found. ' );
                    process.nextTick(function(){
                        var fbtHost="friendsbt.com";
                        //fbtHost="192.168.1.100";
                        var fbtPort=8888;
                        var fileID=fileHash.toString() + "_" + fileSize;
                        handleResource404(fbtHost, fbtPort, owner["uid"], fileID);
                    });
                }else{
                    global.log.info('FUCK: error chunksData length ' + chunksData.length+" end:"+end+" start:"+start);
                }
                global.log.info('fileHash:' + fileHash + ' remove ower uid:' +owner["uid"] +" ip:"+owner["host"]);
                utils.removeArrayItem(availableFileOwners[fileHash], owner);//this file owner is invalid

                    process.nextTick(function(){
                    downloadBlock(fileInfo, localFile, blockID, downloadEventEmitter);//go on download this block
                    });
            } else {
                utils.assert(response.statusCode == 206 || response.statusCode == 200);
                //utils.assert(chunksData.length <= config.BLOCK_SIZE);
                var downloadedBlocksCnt = totalBlocksNum - fileBlocksDownloadLeft[fileHash].length;
                var tempFile=localFile+tempSuffix;
                if (downloadedBlocksCnt > 0 && !(fs.existsSync(tempFile)) && !(fs.existsSync(localFile))) {//user delete the file
                    delete fileDownloadStates[fileHash];
                    if (!downloadErrCallbackInvoked[fileHash]) {
                        global.log.info('file removed detected while downloading: ' + fileHash);
                        fileDownloadCallback(errTips["remove"],fileHash);//history download leave to controler
                        downloadEventEmitter.emit("downloadErr", fileHash);
                        downloadErrCallbackInvoked[fileHash] = true;
                        return;
                    }
                }
                //var fileStreamToWrite = randomAccessFile(tempFile);
                var fileStreamToWrite = filesStream[fileHash]; //randomAccessFile(tempFile);
        if(!fileStreamToWrite) return;//close file
                fileStreamToWrite.write(blockID * config.BLOCK_SIZE, chunksData,
                    function (err) {
                        //fileStreamToWrite.close();//TODO
                        if (!(fileHash in fileDownloadStates)) {//file download canceled
                            global.log.info('file download canceled...');
                            return;
                        }
                        switch (fileDownloadStates[fileHash]) {//I guess the main time consuming logic is here too
                            case DownloadState.PAUSED://file download pause
                                //case DownloadState.CANCELED://file download canceled
                                global.log.info('file download paused...');
                                return;
                            case DownloadState.DOWNLOADING://file download canceled
                                break;
                            case DownloadState.DOWNLOAD_OVER://file download canceled
                            case DownloadState.DOWNLOAD_ERR://file download canceled
                            default:
                                utils.assert("logic error");
                        }

                        if (err) {
                            fileStreamToWrite.close();
                filesStream[fileHash]=null;
                            delete fileDownloadStates[fileHash];
                            if (!downloadErrCallbackInvoked[fileHash]) {
                                if (err.code == 'ENOSPC') {
                                    fileDownloadCallback(errTips["spaceFull"],fileHash);//history download leave to controler
                                }else{
                                    fileDownloadCallback(errTips["unknown"],fileHash);//history download leave to controler
                                }
                                downloadEventEmitter.emit("downloadErr", fileHash);
                                downloadErrCallbackInvoked[fileHash] = true;
                            }
                            global.log.info('file download error! downloadErr event:' + err + ' fileHash:' + fileHash);
                        } else {
                            utils.removeArrayItem(fileBlocksDownloadLeft[fileHash], blockID);//what if the user cancel the request
                if(fileHash in invalidDownloadOwners){//record for continue downloading file while error occur
                                if(!inArray(invalidDownloadOwners[fileHash],owner)){
                                    invalidDownloadOwners[fileHash].push(owner);
                                }
                            }else{
                                invalidDownloadOwners[fileHash]=[owner];
                            }

                            if(fileHash in fileBlocksDownloadOwners){
                                if(!inArray(fileBlocksDownloadOwners[fileHash],owner['uid'])){
                                    fileBlocksDownloadOwners[fileHash].push(owner['uid']);
                                }
                            }else{
                                fileBlocksDownloadOwners[fileHash]=[owner['uid']];
                            }
//                            global.log.info("blockID download OK:" + blockID);
                            var progress = (1 - fileBlocksDownloadLeft[fileHash].length / totalBlocksNum).toFixed(4); //%.2f
                            var downloadedBlocks = totalBlocksNum - fileBlocksDownloadLeft[fileHash].length;
                            utils.assert(downloadedBlocks > 0 && progress >= 0);
                            var downloadBytes=downloadedBlocks * config.BLOCK_SIZE;
                            if((downloadedBlocks * config.BLOCK_SIZE)>fileSize){
                                downloadBytes=fileSize;
                            }
                            utils.assert(downloadSpeed>=0);
                            if (!downloadErrCallbackInvoked[fileHash]) {
                                downloadProgressCallback(downloadBytes, progress, downloadSpeed);//report progress
                            }
                            //download over
                            if (fileBlocksDownloadLeft[fileHash].length == 0) { //the ony one gateway if download successfully
                                fileDownloadStates[fileHash] = DownloadState.DOWNLOAD_OVER;//the file download is over
                                  fileStreamToWrite.close();
                filesStream[fileHash]=null;
                                if (!downloadOKCallbackInvoked[fileHash]) {
                                    utils.assert(fileBlocksDownloadOwners[fileHash].length>0);
                                    fs.rename(tempFile, localFile, function (err) {
                                        if (err) global.log.info('rename file err. fileHash:' + fileHash);
                                        fileDownloadCallback(null, filesToSave[fileHash],fileHash,fileBlocksDownloadOwners[fileHash].join(','));
                    removeCache(fileHash);
                                    });
                                    global.log.info('file download OK. fileHash:' + fileHash);
                                    downloadEventEmitter.emit("downloadOK", fileHash);
                                    downloadOKCallbackInvoked[fileHash] = true;
                                }
                                return;
                            }
                            var nextBlockID = blockID + downloadHttpConnectionCnt[fileHash];//config.MAX_HTTP_CONNECTION_CNT;
        if (nextBlockID >= totalBlocksNum){
        if(fileBlocksDownloadLeft[fileHash].length>0) {
            var index=fileBlocksDownloadLeft[fileHash].length-1;
            while(index>=0 && inArray(fileBlocksDownloading[fileHash],fileBlocksDownloadLeft[fileHash][index])){
                index-=1;
            }
            if(index>=0){
                 nextBlockID=fileBlocksDownloadLeft[fileHash][index];
                        //global.log.info('fileHash:' + fileHash+" I will ACC the dowload nextBlockID:"+nextBlockID+" totalBlocksNum:"+totalBlocksNum);
            }
            else{
                 return;
            }
        }else{
            return;
        }
    }
                    utils.assert(nextBlockID < totalBlocksNum);
                                           process.nextTick(function(){
                                        downloadBlock(fileInfo, localFile, nextBlockID, downloadEventEmitter);
                                          });
                        }
                    }
                );
            }
        });
    });


    httpWritingStream.on('error', function requestError(err) {
        //handle error if server not connect
        global.log.info("request error:" + err);
        global.log.info('fileHash:' + fileHash + ' remove ower uid:' +owner["uid"] +" ip:"+owner["host"]);
        utils.removeArrayItem(availableFileOwners[fileHash], owner);//this file owner is invalid
          process.nextTick(function(){
            downloadBlock(fileInfo, localFile, blockID, downloadEventEmitter);//go on download this block
          });
    });

    httpWritingStream.on('socket', function (socket) {
        socket.setTimeout(10000);
        socket.on('timeout', function() {
           httpWritingStream.abort();
        });
    });
    allHttpDownload[""+fileHash+fileSize].push(httpWritingStream);
}

/**
 * remove file download from queue, delete downloaded file at the same time.
 *
 * fileHash: hash of file to remove from download queue
 * callback: callback when complete
 */
function removeFileDownload(fileHash) {
    utils.assert(fileHash> 0);
    global.log.info("remove file download:" + fileHash);
    delete fileBlocksDownloadLeft[fileHash];
    removeCache(fileHash);
}

function removeCache(fileHash){
    delete fileDownloadStates[fileHash];
    delete fileBlocksDownloading[fileHash];
    delete fileBlocksDownloadOwners[fileHash];
    delete invalidDownloadOwners[fileHash];
    //added by bone
    delete downloadErrCallbackInvoked[fileHash];
    delete downloadOKCallbackInvoked[fileHash];
    delete fileDownloadOverCallbacks[fileHash];
    delete downloadProgressCallbacks[fileHash];
    delete availableFileOwners[fileHash];
    delete downloadHttpConnectionCnt[fileHash];
    delete filesToSave[fileHash];
    filesStream[fileHash] && filesStream[fileHash].close();
    delete filesStream[fileHash];
    delete fileDownloadInfos[fileHash];
    delete fileDownloadEventEmitter[fileHash];
    delete downloadBlockTimeAt[fileHash];
}

/**
 * pause a file download
 *
 * fileHash: hash of file
 */
function pauseFileDownload(fileHash) {
    if (fileHash in fileDownloadStates && fileDownloadStates[fileHash] == DownloadState.DOWNLOADING) {
        global.log.info("pause file download:" + fileHash);
        fileDownloadStates[fileHash] = DownloadState.PAUSED;
    }
}


/**
 * resume a file download
 *
 * fileHash: hash of file
 */
function resumeFileDownload(fileHash) {
    if (fileHash in fileDownloadStates && fileDownloadStates[fileHash] == DownloadState.PAUSED) {
        global.log.info("resume file download:" + fileHash);
        fileDownloadStates[fileHash] = DownloadState.DOWNLOADING;
        downloadFile(fileDownloadInfos[fileHash], availableFileOwners[fileHash], fileDownloadEventEmitter[fileHash], fileDownloadOverCallbacks[fileHash], downloadProgressCallbacks[fileHash]);
    }
}

function handleResource404(fbtHost, fbtPort, uid, fileID){
    utils.assert(fbtHost.length > 0);
    utils.assert(fbtPort > 0);
    utils.assert(uid >= 0);
    utils.assert(fileID.length > 0);

    var queryInfo={'user':uid,
        'file_id': fileID};

    var options = {
        hostname: fbtHost,
        port: fbtPort,
        path: '/resource404?' + querystring.stringify(queryInfo),
        method: 'GET'
    };

    var chunks = [];
    var httpWritingStream = http.get(options, function (response) {
        response.on('data', function (chunk) {
            chunks.push(chunk);
        });

        var errorOccur = 0;
        response.on('error', function (err) {
            errorOccur = 1;
        });

        response.on('close', function () {// event emit when the server has stopped! may not follow with end event!
            if (errorOccur) {
                global.log.info("error in handleResource404");
            }
        });

        response.on('end', function () {// event emit when all data has come out!
            try{
              var chunksData = Buffer.concat(chunks);
              var json=JSON.parse(chunksData);
              if('err' in json && json['err']==0){
                  global.log.info("handleResource404 OK, fileID:"+fileID+" uid:"+uid);
              }else{
                  global.log.info("handleResource404 json err:",json);
              }
            }catch(e){
                global.log.info("handleResource404 found server not update code.");
            }
        });
    });

    httpWritingStream.on('error', function(err) {
        global.log.info("error in http handleResource404:"+err);
    });
}

exports.pauseFileDownload = pauseFileDownload;
exports.resumeFileDownload = resumeFileDownload;
exports.removeFileDownload = removeFileDownload;
exports.downloadFile = downloadFile;
exports.cancelAllSpecificDownload = cancelAllSpecificDownload;
exports.myCleanup = myCleanup;
