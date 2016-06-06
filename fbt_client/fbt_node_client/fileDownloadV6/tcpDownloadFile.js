/**
 * Created by bone on 15-7-15.
 */
var DEBUG = false; // true for local test
var DETAILED = false;

var net = require('net'),
    path = require('path');
var fs = require('fs');

if(DEBUG){
    randomAccessFile = require('random-access-file');
    utils = {
        fbtNormalize: function (filePath) {
            return filePath;
        }, assert: function(exp){
            return true;
        }
    };
    Nigel = require('nigel');
}else{
    randomAccessFile = require(path.join(global.exec_path, 'random-access-file'));
    utils = require('../fbtUtils/fbtUtils');
    Nigel = require(path.join(global.exec_path, 'nigel'));
}

var EOF = new Buffer('\r\nEOF\r\n');
var config = {
    BLOCK_SIZE: 128 * 1024, // 64KB
    MAX_HTTP_CONNECTION_CNT: 32,
    STATE_FILE: DEBUG? 'downloadState2.json':path.join(global.fbt, 'downloadState2.json'),
    OWNER_FILE: DEBUG? 'downloadOwner2.json':path.join(global.fbt, 'downloadOwner2.json')
};

if (DEBUG){
    DIFF_TIME = 1000;
    //config.MAX_HTTP_CONNECTION_CNT = 5;
}else{
    DIFF_TIME = 3000;
}

var errTips = {"duplicatedDownload": 1, "historyDownload": 2, "spaceFull": 3, "invalidOwners": 4, "unknown": 5, "remove": 6};
var tempSuffix = ".tmp";
var DownloadState = {DOWNLOAD_OVER: 0, DOWNLOADING: 1, CANCELED: 2, PAUSED: 3, DOWNLOAD_ERR: 4};
var noSpeed = 0.0;

var fileBlocksDownloadLeft = {};
var fileBlocksDownloading = {};
var downloadCandidateQueue = {};
var downloadActiveQueue = {};
var fileBlocksLeftRecord = {};
var fileBlocksDownloadOwners = {};
var goodDownloadOwners = {};
var fileBlocksDownloaded = {};
var fileDownloadStates = {}; //the download state of every file
var fileDownloadProgressTimer = {};
var fileDownloadInfos = {};
var fileDownloadBlockTimer = {};

var preSavedDownloadLeft = null;
var preSavedDownloadOwners = null;

function loadDownloadState() {
    if (fs.existsSync(config.STATE_FILE)) {
        var data = fs.readFileSync(config.STATE_FILE);
        fileBlocksLeftRecord = JSON.parse(data);
    }
}

function loadDownloadOwner() {
    if (fs.existsSync(config.OWNER_FILE)) {
        var data = fs.readFileSync(config.OWNER_FILE);
        fileBlocksDownloadOwners = JSON.parse(data);
    }
}

function saveDownloadState() {
    var toSave = JSON.stringify(fileBlocksLeftRecord);
    if (preSavedDownloadLeft != toSave) {
        preSavedDownloadLeft = toSave;
        fs.writeFileSync(config.STATE_FILE, toSave);
    }
}

/**
 * Randomize array element order in-place.
 * Using Fisher-Yates shuffle algorithm.
 */
function shuffleArray(array) {
    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
    return array;
}

function getBlockSize(blockID, fileSize){
    var start =  blockID*config.BLOCK_SIZE;
    var end = (blockID+1)*config.BLOCK_SIZE-1;
    if (end >= fileSize){
        end = fileSize - 1;
    }
    return (end-start+1);
}

function constructHeader(blockID, fileHash, fileSize){
    blockID = parseInt(blockID);
    var start =  blockID*config.BLOCK_SIZE;
    var end = (blockID+1)*config.BLOCK_SIZE-1;
    if (end >= fileSize){
        end = fileSize - 1;
    }
    return new Buffer(JSON.stringify({"start": start, "end": end, "hash": fileHash, "size": fileSize, "blockID": blockID}));
}

function fileBlocks(fileSize) {
    return Math.floor((fileSize + config.BLOCK_SIZE - 1) / config.BLOCK_SIZE);
}


try {
    loadDownloadState();
    loadDownloadOwner();
} catch (e) {
    // pass
}

function getHistoryDownloadBlocks(fileID, savedFile, totalBlocksNum) {
    log2file("check history download.");
    if (fileID in fileBlocksLeftRecord) {
        var blocksLeft = fileBlocksLeftRecord[fileID];
        // use history download blocks
        if (blocksLeft.length == 0) {// history download file OK
            if (fs.existsSync(savedFile)) {// if file download OK
                fileDownloadStates[fileID] = DownloadState.DOWNLOAD_OVER;
                return [];
            } else {
                log2file('found history download. but the user change file path. fileID:' + fileID);
                return range(0, totalBlocksNum);//re download the file
            }
        } else {// history download
            if (fs.existsSync(savedFile + tempSuffix)) {//if file download OK
                log2file("discover history download...");
                return blocksLeft;
            } else {
                return range(0, totalBlocksNum);
            }
        }
    } else {
        return range(0, totalBlocksNum);
    }
}


function downloadFile(fileInfo, fileOwners, downloadEventEmitter, downloadOverCallback, downloadProgressCallback){
    var fileHash = parseInt(fileInfo['hash']);
    var fileSize = parseInt(fileInfo['size']);
    var fileID = genFileID(fileHash, fileSize);
    var savedFile = fileInfo['file_to_save'];

    fileDownloadInfos[fileID] = {'fileInfo': fileInfo, // 'fileOwners':fileOwners,
        'downloadEventEmitter':downloadEventEmitter, 'downloadOverCallback': downloadOverCallback,
        'downloadProgressCallback': downloadProgressCallback};

    log2file('download fileID:' + fileID);
    if(fileOwners.length == 0) {
        log2file("TCP download no file owners");
        return;
    }
    var totalBlocksNum = fileBlocks(fileSize);

    downloadCandidateQueue[fileID] = shuffleArray(fileOwners);
    downloadActiveQueue[fileID] = [];
    fileDownloadStates[fileID] = DownloadState.DOWNLOADING;//the file is processing

    var downloadOverCalled = false;
    var downloadOverCallbackOnce = function(err, filename, fileHash, fileSize, from) {
        if(!downloadOverCalled){
            if(err){
                downloadEventEmitter.emit("downloadErr", fileHash, fileSize);
            }else{
                // no more use this owners
                downloadEventEmitter.emit("downloadOK", fileHash, fileSize);
                delete fileBlocksDownloadOwners[fileID];
            }
            downloadOverCallback(err, filename, fileHash, fileSize, from);

            // clear timer
            if(fileID in fileDownloadProgressTimer){
                setTimeout(function(){ // ensure that the progress 100% is set.
                    clearInterval(fileDownloadProgressTimer[fileID]);
                }, DIFF_TIME*2);
            }

            downloadOverCalled = true;
        } else{
            log2file('Already called downloadOverCallback!');
        }
    };

    // read history download from file
    fileBlocksDownloadLeft[fileID] = getHistoryDownloadBlocks(fileID, savedFile, totalBlocksNum);
    if(fileBlocksDownloadLeft[fileID].length == 0) {
        downloadProgressCallback(fileSize, 1.0, noSpeed);
        log2file('found history download. downloadOK event. fileID:' + fileID);
        downloadOverCallbackOnce(null, savedFile, fileHash, fileSize);
        return;
    }

    fileBlocksLeftRecord[fileID] = fileBlocksDownloadLeft[fileID].concat();
    fileBlocksDownloading[fileID] = [];
    fileBlocksDownloaded[fileID] = [];
    fileDownloadBlockTimer[fileID] = {};

    // set download progress timer
    var fileDownloadBytes = fileSize - fileBlocksLeftRecord[fileID].length * config.BLOCK_SIZE;
    if (fileDownloadBytes < 0) fileDownloadBytes = 0;

    fileDownloadProgressTimer[fileID] = setInterval(function updateProgress() {
        if (fileID in fileBlocksLeftRecord) {
            var progress = (1 - fileBlocksLeftRecord[fileID].length / totalBlocksNum).toFixed(4); //%.2f
            var fileDownloadBytes2 = fileSize - fileBlocksLeftRecord[fileID].length * config.BLOCK_SIZE;
            if (fileDownloadBytes2 < 0) fileDownloadBytes2 = 0;
            var downloadSpeed = (fileDownloadBytes2 - fileDownloadBytes) / (DIFF_TIME / 1000);
            var FAKE_SPEED_RATE = 1.68;
            downloadSpeed = downloadSpeed.toFixed(2)* FAKE_SPEED_RATE;
            fileDownloadBytes = fileDownloadBytes2;
            if(downloadSpeed < 0) downloadSpeed = 0;
            process.nextTick(function () {
                if (userPausedOrCancelFileDownload(fileID)) downloadSpeed = 0;
                if (downloadOverCalled){
                    downloadProgressCallback(fileDownloadBytes2, progress, downloadSpeed);
                    // reset progress call back
                    downloadProgressCallback = function(){
                        log2file("download over or failed. I will not call progress callback:"+fileID);
                    };
                } else {
                    downloadProgressCallback(fileDownloadBytes2, progress, downloadSpeed);//report progress
                }
            });
        }
    }, DIFF_TIME);

    var concurrentHttpCnt = Math.min(totalBlocksNum, config.MAX_HTTP_CONNECTION_CNT);
    concurrentHttpCnt = Math.min(concurrentHttpCnt, fileOwners.length);//MAYBE this is better for just has 1 owners
    log2file("concurrent tcp socket Cnt:" + concurrentHttpCnt);
    for (var i = 0; i < concurrentHttpCnt; ++i) {
        process.nextTick(function () {
            var owner = pop(downloadCandidateQueue[fileID]);
            if (owner) {
                downloadActiveQueue[fileID].push(owner);
                downloadBlockHelper(owner, savedFile, fileHash, fileSize, downloadOverCallbackOnce);
            }
        });
    }
}


function restoreDownloadInfo(fileID) {
    if (fileID in downloadCandidateQueue && fileID in fileBlocksDownloadLeft) {
        downloadCandidateQueue[fileID].push.apply(downloadCandidateQueue[fileID], downloadActiveQueue[fileID]);
        downloadActiveQueue[fileID] = [];
        fileBlocksDownloadLeft[fileID].push.apply(fileBlocksDownloadLeft[fileID], fileBlocksDownloading[fileID]);
        fileBlocksDownloading[fileID] = [];
    }
}

function userPausedOrCancelFileDownload(fileID) {
    if (!(fileID in fileDownloadStates)) {//file download canceled
        log2file('file download canceled...');
        restoreDownloadInfo(fileID);
        return true;
    }
    switch (fileDownloadStates[fileID]) {
        case DownloadState.PAUSED://file download pause
            log2file('file download paused...');
            restoreDownloadInfo(fileID);
            return true;
        case DownloadState.DOWNLOADING://file download canceled
            break;
        case DownloadState.DOWNLOAD_OVER://file download canceled
        case DownloadState.DOWNLOAD_ERR://file download canceled
        default:
            // when file download over. call the progress timer will throw logic error
            break;
            //log2file("logic error: download state ==>"+fileDownloadStates[fileID]);
    }
    return false;
}

function genFileID(fileHash, fileSize){
    return fileHash.toString()+"_"+fileSize;
}

function saveDownloadOwner() {
    var toSave = JSON.stringify(fileBlocksDownloadOwners);
    if (preSavedDownloadOwners != toSave) {
        preSavedDownloadOwners = toSave;
        fs.writeFileSync(config.OWNER_FILE, toSave);
    }
}

function updateBlocksToDB(fileID){
    saveDownloadState();
    saveDownloadOwner();
    fileBlocksDownloaded[fileID]=[];
}

function inArray(arr, data) {
    if(arr){
        for (var i = 0; i < arr.length; i++) {
            if (arr[i] == data) return true;
        }
    }
    return false;
}

function recordDownloadedOwners(owner, fileID) {
    if (fileID in fileBlocksDownloadOwners) {
        if (!inArray(fileBlocksDownloadOwners[fileID], owner['uid'])) {
            fileBlocksDownloadOwners[fileID].push(owner['uid']);
        }
    } else {
        fileBlocksDownloadOwners[fileID] = [owner['uid']];
    }
}

function downloadBlockHelper(owner, filePath, fileHash, fileSize, downloadOverCallback){
    var HOST = owner['host'];
    var PORT = owner['port'];

    var fileID = genFileID(fileHash, fileSize);
    if(fileBlocksDownloadLeft[fileID].length == 0){
        return;
    }
    if (userPausedOrCancelFileDownload(fileID)) return;

    //var blockID = pop(fileBlocksDownloadLeft[fileID]);
    //fileBlocksDownloading[fileID].push(blockID);

    var client = new net.Socket();

    var closeBySelf = false;

    function write2socket(data, blockID) {
        if (client.writable) {
            var flushed = client.write(data);
        } else {
            cleanUpSocket(true, blockID);
        }
    }

    function freeDownloadBlock(blockId){
        removeItemOfArray(fileBlocksDownloading[fileID], blockId);
        fileBlocksDownloadLeft[fileID].unshift(blockId);
    }

    function removeInvalidOwner(owner){
        try{
            // download failed check
            removeItemOfArray(downloadActiveQueue[fileID], owner);
            log2file('fileID:' + fileID + ' remove owner uid:' + owner["uid"] + " ip:" + owner["host"]);
            if(downloadNoOwner(fileID)){
                log2file("no file owners:"+fileID);
                downloadOverCallback(errTips["invalidOwners"], filePath);
                fileDownloadStates[fileID] = DownloadState.DOWNLOAD_ERR;
            }
        }catch(e){
            // pass
            log2file("clean up err:"+e);
        }
    }

    function cleanUpSocket(socketErrOccur, blockID){
        if(typeof blockID !== 'undefined'){
            freeDownloadBlock(blockID);
        }
        if(socketErrOccur){
            removeInvalidOwner(owner);
        }else{
            downloadCandidateQueue[fileID].unshift(owner);
            removeItemOfArray(downloadActiveQueue[fileID], owner);
        }
        closeSelf(socketErrOccur);
    }

    function closeSelf(socketErrOccur){
        // if this time is too small, data is transporting.
        var timeOut = DEBUG ? 1000 : 60 * 1000;
        setTimeout(function(){
            try{
                if(socketErrOccur){
                    client.destroy(); // Ensures that no more I/O activity happens on this socket. Only necessary in case of errors (parse error or so).
                }else{
                    closeSelfNow();
                }
            }catch(e){
                // pass
            }
        }, timeOut);
    }

    function closeSelfNow(){
        try{
            closeBySelf = true;
            client.end(); // Half-closes the socket. i.e., it sends a FIN packet. It is possible the server will still send some data.
        }catch(e){
            // pass
        }
    }

    function setBlockTimer(blockID3) {
        if (blockID3 in fileDownloadBlockTimer[fileID]) clearTimeout(fileDownloadBlockTimer[fileID][blockID3]);
        fileDownloadBlockTimer[fileID][blockID3] = setTimeout(function () {
            if (userPausedOrCancelFileDownload(fileID)) return;
            if (inArray(fileBlocksLeftRecord[fileID], blockID3)) {
                log2file("block download timeout:" + fileID + " block:" + blockID3+" owner:"+JSON.stringify(owner));
                if(fileID in goodDownloadOwners && inArray(goodDownloadOwners[fileID], owner['host'])){
                    log2file("But it is a good owner. I will not remove it.");
                    return;
                }
                removeItemOfArray(fileBlocksDownloading[fileID], blockID3);
                fileBlocksDownloadLeft[fileID].unshift(blockID3);
                closeSelfNow();
                removeInvalidOwner(owner);
                process.nextTick(function () {
                    var anotherOwner = pop(downloadCandidateQueue[fileID]);
                    if (anotherOwner) {
                        log2file("block download timeout:" + fileID + " block:" + blockID3 + " and try anthor owner:"+JSON.stringify(anotherOwner));
                        downloadActiveQueue[fileID].push(anotherOwner);
                        downloadBlockHelper(anotherOwner, filePath, fileHash, fileSize, downloadOverCallback);
                    }
                });
            }
        }, 20 * 1000);
    }

    client.connect(PORT, HOST, function () {
        // Write a message to the socket as soon as the client is connected, the server will receive it as message from the client
        if(fileBlocksDownloadLeft[fileID].length == 0){
            closeSelfNow();
            return;
        }
        var blockID = pop(fileBlocksDownloadLeft[fileID]);
        log2file('CONNECTED TO: ' + HOST + ':' + PORT+" download block begin:"+blockID + " fileID:"+fileID);
        fileBlocksDownloading[fileID].push(blockID);

        setBlockTimer(blockID);

        write2socket(constructHeader(blockID, fileHash, fileSize), blockID);
    });

    // Add a 'data' event handler for the client socket
    // data is what the server sent to this socket
    var chunks = [];
    var file = randomAccessFile(filePath + tempSuffix);

    client.on('data', function (data) {
       if (userPausedOrCancelFileDownload(fileID)) {
           // clear socket
           closeSelfNow();
           return;
       }
        var eofIndex = Nigel.horspool(data, EOF);
        if (eofIndex >= 0) {
            var pumpData = data.slice(0, eofIndex);
            if (pumpData.length > 0){
                if(DETAILED) log2file("pump data len:"+pumpData.length);
                chunks.push(pumpData);
            }
            // read header
            var headerLen = 4;
            var blockID2 = chunks[0].slice(0, headerLen).readUInt32BE(0);
            chunks[0] = chunks[0].slice(headerLen);

            if(blockID2 in fileDownloadBlockTimer[fileID]){
                if(DEBUG) log2file("complete block:" + blockID2 + " clear timer");
                clearTimeout(fileDownloadBlockTimer[fileID][blockID2]);
            }

            var content = Buffer.concat(chunks);
            chunks = [];
            var leftData = data.slice(eofIndex + EOF.length);
            if (leftData.length > 0) {
                if(DETAILED) log2file("left data len:"+leftData.length);
                chunks.push(leftData);
            }
            if(DEBUG) log2file("complete block:" + blockID2 + " content len:" + content.length);

            // check if content size error.
            var blockSize = getBlockSize(blockID2, fileSize);
            if(content.length != blockSize){
                log2file("********check logic********block size error:"+blockSize+" I will retry again.");
                setBlockTimer(blockID2);
                write2socket(constructHeader(blockID2, fileHash, fileSize), blockID2);
                return;
            }

            file.write(blockID2 * config.BLOCK_SIZE, content,
                function (err) {
                    if (userPausedOrCancelFileDownload(fileID)) {
                        // clear socket
                        closeSelfNow();
                        return;
                    }

                    if (err) {
                        if(DETAILED) log2file("write block to file error, I will destroy socket.");
                        if (err.code == 'ENOSPC') {
                            downloadOverCallback(errTips["spaceFull"], fileHash, fileSize);
                        } else {
                            downloadOverCallback(errTips["unknown"], fileHash, fileSize);
                        }

                        cleanUpSocket(false, blockID2);
                        file.close();
                        delete fileDownloadStates[fileID]; // TODO FIXME maybe bad!
                    } else {
                        recordDownloadedOwners(owner, fileID);
                        if(fileID in goodDownloadOwners){
                            if(!inArray(goodDownloadOwners[fileID], owner["host"])){
                                goodDownloadOwners[fileID].push(owner["host"]);
                            }
                        }else{
                            goodDownloadOwners[fileID] = [owner["host"]];
                        }

                        removeItemOfArray(fileBlocksDownloading[fileID], blockID2);
                        removeItemOfArray(fileBlocksLeftRecord[fileID], blockID2);

                        fileBlocksDownloaded[fileID].push(blockID2);
                        var MAX_CACHE_CNT= 16; // 160*64=10M
                        if(fileBlocksDownloaded[fileID].length >= MAX_CACHE_CNT){
                            updateBlocksToDB(fileID);
                        }

                        if(DETAILED) log2file("write content block Ok.");
                        if(downloadOver(fileID)){
                            fileDownloadStates[fileID] = DownloadState.DOWNLOAD_OVER;//the file download is over
                            fs.rename(filePath + tempSuffix, filePath, function (err) {
                                cleanUpSocket(false);
                                var closeFIleTimeout = DEBUG ? 1000:3000;
                                setTimeout(function () {
                                    file.close();
                                    if(!err){
                                        downloadOverCallback(null, filePath, fileHash, fileSize, fileBlocksDownloadOwners[fileID].join(','));
                                        updateBlocksToDB(fileID);
                                    }else{
                                        downloadOverCallback(errTips["unknown"], fileHash, fileSize);
                                    }
                                    log2file("file download Ok:" + fileID + " and closed file descriptor.");
                                }, closeFIleTimeout);
                            });
                            return;
                        }

                        // complete my download task
                        if(fileBlocksDownloadLeft[fileID].length == 0){
                            cleanUpSocket(false);
                            // set timer check if need accelerate
                            // Download the last block is too slow. I will accelerate it.
                            var ACC_BLOCK_LIMIT = DEBUG ? 3:6;
                            if(downloadBlocksLeft(fileID) <= ACC_BLOCK_LIMIT){
                                log2file("blocks left <=3. check to accelerate it:" + fileID);
                                setTimeout(function(){
                                    if(downloadBlocksLeft(fileID) > 0){
                                        process.nextTick(function () {
                                            log2file("download time out. blocks left(<=3). accelerate it:" + fileID);
                                            pauseFileDownload(fileHash, fileSize);
                                            resumeFileDownload(fileHash, fileSize);
                                        });
                                    } else{
                                        log2file("download blocks left(<=3). Good. need not accelerate:" + fileID);
                                    }
                                }, downloadBlocksLeft(fileID) * 10 * 1000);
                            }
                            return;
                        }

                        // next block download
                        var blockID = pop(fileBlocksDownloadLeft[fileID]);
                        setBlockTimer(blockID);
                        write2socket(constructHeader(blockID, fileHash, fileSize), blockID);
                        if(DETAILED) log2file("next block:" + blockID);
                    }
                }
            );
        } else {
            chunks.push(data);
            //if(DETAILED) log2file('DATA: coming...'+typeof(data)+" data:");
        }
    });

    client.on('end', function () {
        if (userPausedOrCancelFileDownload(fileID)) return;
        if(!closeBySelf){
            log2file('disconnected from server');
            // should be the server error
            removeInvalidOwner(owner);
        }
    });

    var tryTimes = 0;

    function retryOnTimeout(){
        if(fileID in goodDownloadOwners && inArray(goodDownloadOwners[fileID], owner['host'])){
            if(tryTimes >= 10){
                log2file('fileID:' + fileID + ' tried too many times. give up.');
                cleanUpSocket(true);
                return;
            }
            log2file('********check logic********fileID:' + fileID + ' ETIMEDOUT. but will not remove owner uid:' + owner["uid"] + " ip:" + owner["host"]);
            closeSelfNow();
            log2file('********check logic********open a new socket and go on downloading...');
            /**
             * Event: 'timeout'#
             * Emitted if the socket times out from inactivity. This is only to notify that the socket has been idle.
             * The user must manually close the connection.
             */
            process.nextTick(function () {
                downloadBlockHelper(owner, filePath, fileHash, fileSize, downloadOverCallback);
            });
            tryTimes+=1;
        } else {
            log2file('fileID:' + fileID + ' timeout.');
            cleanUpSocket(true);
        }
    }

    client.on('error', function (err) {
        if (userPausedOrCancelFileDownload(fileID)) return;

        log2file('error on socket:'+err);
        if(err.code === 'ECONNRESET' || err.code === 'ETIMEDOUT') { /* apply logic */
            log2file("err:"+err+" but will try again or give up:"+fileID+ " owner:" + JSON.stringify(owner));
            retryOnTimeout();
        } else {
            cleanUpSocket(true);
        }
    });

    // Add a 'close' event handler for the client socket
    client.on('close', function () {
        if (userPausedOrCancelFileDownload(fileID)) return;

        if(DETAILED) log2file('Connection closed');
    });

    if(DEBUG){
        client.setTimeout(30000); // for heartbeat, set the timeout
    } else {
        client.setTimeout(60000);
    }
    /**
     * socket.setTimeout(timeout[, callback])#
     Sets the socket to timeout after timeout milliseconds of inactivity on the socket. By default net.Socket do not have a timeout.
     When an idle timeout is triggered the socket will receive a 'timeout' event but the connection will not be severed. The user must manually end() or destroy() the socket.
     If timeout is 0, then the existing idle timeout is disabled.
     The optional callback parameter will be added as a one time listener for the 'timeout' event.
     */

    client.on('timeout', function () {
        log2file("err: timeout but will try again or give up:"+fileID+ " owner:" + JSON.stringify(owner));
        retryOnTimeout();
    });
}

function pop(arr) {
    if(typeof arr !== 'undefined')
        return arr.shift();
    else
        return null;
}

function removeItemOfArray(arr, item) {
    for (var i = arr.length; i--;) {
        if (arr[i] === item) {
            arr.splice(i, 1);
        }
    }
}

//python range
function range(lowEnd,highEnd){
	var arr = [];
	while(lowEnd < highEnd){
	   arr.push(lowEnd++);
	}
	return arr;
}


function downloadBlocksLeft(fileID){
    //return (fileBlocksDownloading[fileID].length+fileBlocksDownloadLeft[fileID].length);
    //if(fileID in fileBlocksLeftRecord){
        return fileBlocksLeftRecord[fileID].length;
    //}else{
    //    return 0;
    //}
}

function downloadOver(fileID){
    return fileBlocksLeftRecord[fileID].length == 0;
    //return downloadBlocksLeft(fileID) == 0;
}

function downloadNoOwner(fileID){
    return downloadActiveQueue[fileID].length == 0 && downloadCandidateQueue[fileID].length == 0;
}


function log2file(content){
    if(DEBUG){
        console.log("TCP download:" + content);
    }else{
        global.log.info("TCP download: "+content);
    }
}

function removeCache(fileID) {
    delete fileDownloadStates[fileID];
    delete fileBlocksDownloadLeft[fileID];
    delete fileBlocksLeftRecord[fileID];
    delete fileBlocksDownloaded[fileID];
    delete fileBlocksDownloadOwners[fileID];
    delete fileBlocksDownloading[fileID];
    delete fileDownloadProgressTimer[fileID];
    delete downloadCandidateQueue[fileID];
    delete downloadActiveQueue[fileID];
    delete fileDownloadInfos[fileID];
}

function removeFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    log2file("remove file download:" + fileID);
    clearInterval(fileDownloadProgressTimer[fileID]);
    removeCache(fileID);
}


function pauseFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in fileDownloadStates && fileDownloadStates[fileID] == DownloadState.DOWNLOADING) {
        log2file("pause file download:" + fileID);
        fileDownloadStates[fileID] = DownloadState.PAUSED;
        updateBlocksToDB(fileID);
        clearInterval(fileDownloadProgressTimer[fileID]);
    }
}

function resumeFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in fileDownloadStates && fileDownloadStates[fileID] == DownloadState.PAUSED) {
        log2file("resume file download:" + fileID);
        fileDownloadStates[fileID] = DownloadState.DOWNLOADING;
        downloadFile(fileDownloadInfos[fileID]['fileInfo'], downloadCandidateQueue[fileID], fileDownloadInfos[fileID]['downloadEventEmitter'],  fileDownloadInfos[fileID]['downloadOverCallback'], fileDownloadInfos[fileID]['downloadProgressCallback']);
    }
}

if(DEBUG){
    var fileOwners =   [{'host': '127.0.0.1', 'port': 8885, 'uid': 1234},
        {'host': '::1', 'port': 8885, 'uid': 4321},
        {'host': '2001::1', 'port': 8885, 'uid': 5321}, // for test unreachable
        {'host': 'localhost', 'port': 8880, 'uid': 54321}, //for test time out
        {'host': 'localhost', 'port': 8880, 'uid': 14321}, //for test time out
        {'host': 'localhost', 'port': 8880, 'uid': 321} //for test time out
        ];
    var EventEmitter = require("events").EventEmitter;
    var downloadEventEmitter = new EventEmitter();
    var fileHash = 321;
    var fileSize = 350517248;
    var fileID = genFileID(fileHash, fileSize);
    downloadFile({"hash": fileHash, "size": fileSize, file_to_save: path.join(__dirname, 'fill2.tar')}, fileOwners, downloadEventEmitter, function(err, filename, hash, size, from){
        log2file("download over callback. file:"+filename+" hash:"+hash + " size:"+size+" from:"+from+" err:"+err);
    }, function(downloaded, progress, speed){
        log2file("file downloaded:"+downloaded+" progress:"+progress + " speed:"+speed);
    });
    // mock user pause file download
    var timeAt = Math.floor(821+Math.random()*1000);
    //console.log("log:"+timeAt);
    if(timeAt % 2 ==0){ // test remove file download
    //if(False){ // test remove file download
        setTimeout(function(){
            removeFileDownload(fileHash, fileSize);
        }, timeAt);
    }else{
        setTimeout(function(){ // test pause and resume download
            pauseFileDownload(fileHash, fileSize);
        }, timeAt);
        setTimeout(function(){
            resumeFileDownload(fileHash, fileSize);
        }, timeAt + 2000);
    }

}

function getDownloadingCnt() {
    var ret = 0;
    for (var h in fileDownloadStates){
        if(fileDownloadStates[h] == DownloadState.DOWNLOADING){
            ret += 1; 
        }
    }
    return ret;
}

function myCleanup() {
    //backup download state
    saveDownloadState();
    saveDownloadOwner();
}

exports.pauseFileDownload = pauseFileDownload;
exports.resumeFileDownload = resumeFileDownload;
exports.removeFileDownload = removeFileDownload;
exports.downloadFile = downloadFile;
exports.myCleanup = myCleanup;
