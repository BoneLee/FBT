var http = require('http');
//http.globalAgent.maxSockets = 512;
var fs = require('fs');
var path = require('path');
var randomAccessFile = require(path.join(global.exec_path, 'random-access-file'));
var querystring = require('querystring');
var utils = require('../fbtUtils/fbtUtils');
//var cleanup = require('../fbtUtils/cleanUp');

var debug = 0;

//set by experiment
var BLOCK_INCREASED = 1;
var config = { BLOCK_SIZE: 64 * 1024 * BLOCK_INCREASED, //64KB
    MAX_HTTP_CONNECTION_CNT: 64, //100? //30=~2.5MB
    STATE_FILE: path.join(global.fbt, 'downloadState.json'),
    OWNER_FILE: path.join(global.fbt, 'downloadOwner.json')
};//set to current path

var errTips = {"duplicatedDownload": 1, "historyDownload": 2, "spaceFull": 3, "invalidOwners": 4, "unknown": 5, "remove": 6};
var tempSuffix = ".tmp";

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
var fileBlocksLeftRecord = {};
var fileBlocksDownloadOwners = {};
var fileBlocksDownloading = {};
var validOwners = {};
var fileBlocksDownloaded = {};
var downloadTriedTimes = {};
var fileDownloadProgressTimer = {};

var downloadCandidateQueue = {};
var downloadActiveQueue = {};
var download503Queue = {};

var fileDownloadStates = {}; //the download state of every file
var fileDownloadOverCallbacks = {};
var downloadProgressCallbacks = {};
var downloadErrCallbackInvoked = {};
var downloadOKCallbackInvoked = {};
var filesToSave = {};
var filesStream = {};
var fileDownloadInfos = {};
var fileDownloadBytes = {};
//var fileDownloadAt = {};
var fileDownloadEventEmitter = {};

var preSavedDownloadLeft = null;
var preSavedDownloadOwners = null;


function myCleanup() {
    //backup download state
    saveDownloadState();
    saveDownloadOwner();
}

//setInterval(myCleanup, 60 * 1000);
//cleanup.registerClean(myCleanup);


try {
    loadDownloadState();
    loadDownloadOwner();
} catch (e) {
}


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

function updateBlocksToDB(fileID){
    saveDownloadState();
    saveDownloadOwner();
    fileBlocksDownloaded[fileID]=[];
}

function saveDownloadOwner() {
    var toSave = JSON.stringify(fileBlocksDownloadOwners);
    if (preSavedDownloadOwners != toSave) {
        preSavedDownloadOwners = toSave;
        fs.writeFileSync(config.OWNER_FILE, toSave);
    }
}

function downloadOver(fileID){
    return (fileBlocksDownloadLeft[fileID].length == 0 && fileBlocksDownloading[fileID].length == 0);
}

function inArray(arr, data) {
    for (var i = 0; i < arr.length; i++) {
        if (JSON.stringify(arr[i]) === JSON.stringify(data)) return true;
    }
    return false;
}

function fileBlocks(fileSize) {
    return Math.floor((fileSize + config.BLOCK_SIZE - 1) / config.BLOCK_SIZE);
}

function genFileID(fileHash, fileSize) {
    return fileHash + "_" + fileSize;
}


function removeItemOfArray(arr, item) {
    for (var i = arr.length; i--;) {
        if (arr[i] === item) {
            arr.splice(i, 1);
        }
    }
}

function pop(arr) {
    return arr.shift();
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
    var fileHash = parseInt(fileInfo['hash']);
    var fileSize = parseInt(fileInfo['size']);
    var fileID = genFileID(fileHash, fileSize);
    var savedFile = fileInfo['file_to_save'];
    utils.assert(savedFile.length > 0);

    global.log.info('download fileID:' + fileID);
    if (utils.len(fileOwners) == 0) {
        global.log.info("no file owners... that's very bad!");
        downloadOverCallback('file download error! No fileOwners!');
        downloadEventEmitter.emit("downloadErr", fileHash, fileSize);
        //clearInterval(fileDownloadProgressTimer[fileID]);
        //removeCache(fileID);
        return;
    }

    var totalBlocksNum = fileBlocks(fileSize);
    var noSpeed = 0;

    fileDownloadStates[fileID] = DownloadState.DOWNLOADING;//the file is processing
    filesToSave[fileID] = savedFile;
    filesStream[fileID] = randomAccessFile(savedFile + tempSuffix);
    var fileBlocksCnt = totalBlocksNum;

    if (fileID in fileBlocksLeftRecord) {
        var blocksLeft = fileBlocksLeftRecord[fileID];
        //use history download blocks
        if (blocksLeft.length == 0) {//history download file OK
            if (fs.existsSync(savedFile)) {//if file download OK
                fileDownloadStates[fileID] = DownloadState.DOWNLOAD_OVER;
                downloadProgressCallback(totalBlocksNum * config.BLOCK_SIZE, 1.0, noSpeed); //set progress 100%
                downloadOverCallback(errTips["historyDownload"], filesToSave[fileID], fileHash, fileSize);//history download leave to controler
                global.log.info('found history download. downloadOK event. fileID:' + fileID);
                downloadEventEmitter.emit("downloadOK", fileHash, fileSize);
                return;
            } else {
                fileBlocksDownloadLeft[fileID] = utils.range(0, fileBlocksCnt);//re download the file
                global.log.info('found history download. but the user change file path. fileID:' + fileID);
            }
        } else {//history download
            if (fs.existsSync(savedFile + tempSuffix)) {//if file download OK
                global.log.info("discover history download...");
                fileBlocksDownloadLeft[fileID] = blocksLeft;
            } else {
                fileBlocksDownloadLeft[fileID] = utils.range(0, fileBlocksCnt);//record the download state
            }
        }
    } else {
        fileBlocksDownloadLeft[fileID] = utils.range(0, fileBlocksCnt);//record the download state
    }
    fileBlocksLeftRecord[fileID] = fileBlocksDownloadLeft[fileID].concat();
    utils.assert(utils.isFunction(downloadOverCallback));//must provide callback
    utils.assert(utils.isFunction(downloadProgressCallback));//must provide callback

    //init globals
    fileDownloadOverCallbacks[fileID] = downloadOverCallback;
    downloadProgressCallbacks[fileID] = downloadProgressCallback;
    fileDownloadInfos[fileID] = fileInfo;//for resume download
    fileDownloadEventEmitter[fileID] = downloadEventEmitter;

    /****************************************************/
    downloadCandidateQueue[fileID] = shuffleArray(fileOwners);
    downloadActiveQueue[fileID] = [];
    download503Queue[fileID] = {};
    fileBlocksDownloading[fileID] = [];
    if (!(fileID in validOwners) || !(fileID in downloadTriedTimes)) {
        validOwners[fileID] = {};
        downloadTriedTimes[fileID] = 1;
    }
    fileBlocksDownloaded[fileID]=[];
    /****************************************************/

    downloadErrCallbackInvoked[fileID] = false;
    downloadOKCallbackInvoked[fileID] = false;

    var concurrentHttpCnt = Math.min(fileBlocksCnt, config.MAX_HTTP_CONNECTION_CNT);//oops maybe a bug
    concurrentHttpCnt = Math.min(concurrentHttpCnt, fileOwners.length);//MAYBE this is better for just has 1 owners
    global.log.info("concurrentHttpCnt:" + concurrentHttpCnt);

    fileDownloadBytes[fileID] = (totalBlocksNum - fileBlocksDownloadLeft[fileID].length - fileBlocksDownloading[fileID].length) * config.BLOCK_SIZE;
    if (fileDownloadBytes[fileID] > fileSize) {
        fileDownloadBytes[fileID] = fileSize;
    }

    var DIFF_TIME = 3000;
    fileDownloadProgressTimer[fileID] = setInterval(function updateProgress() {
        if (fileID in fileBlocksDownloadLeft && fileID in fileBlocksDownloading) {
            var progress = (1 - (fileBlocksDownloadLeft[fileID].length + fileBlocksDownloading[fileID].length) / totalBlocksNum).toFixed(4); //%.2f
            var downloadBytes = (totalBlocksNum - fileBlocksDownloadLeft[fileID].length - fileBlocksDownloading[fileID].length) * config.BLOCK_SIZE;
            if (downloadBytes > fileSize) {
                downloadBytes = fileSize;
            }
            var downloadSpeed = (downloadBytes - fileDownloadBytes[fileID]) / (DIFF_TIME / 1000);
            fileDownloadBytes[fileID] = downloadBytes;
            var FAKE_SPEED_RATE = 1.58;
            downloadSpeed = downloadSpeed.toFixed(2) * FAKE_SPEED_RATE;
            if(downloadSpeed < 0) downloadSpeed = 0;
            utils.assert(downloadSpeed >= 0);
            if (!downloadErrCallbackInvoked[fileID] && !downloadOKCallbackInvoked[fileID]) {
                process.nextTick(function () {
                    if (userPausedOrCancelFileDownload(fileID)) downloadSpeed = 0;
                    downloadProgressCallback(downloadBytes, progress, downloadSpeed);//report progress
                });
            }
        }
    }, DIFF_TIME);

    for (var i = 0; i < concurrentHttpCnt; ++i) {
        downloadBlockFromOwner(fileID);
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

function downloadBlockFromOwner(fileID) {
    process.nextTick(function () {
        var owner = pop(downloadCandidateQueue[fileID]);
        if (owner) {
            downloadActiveQueue[fileID].push(owner);
            downloadBlockHelper(fileDownloadInfos[fileID], filesToSave[fileID], owner, fileDownloadEventEmitter[fileID], fileDownloadOverCallbacks[fileID]);
        }
    });
}

function recordGoodOwners(owner, fileID) {
    if (!(owner['host'] in validOwners[fileID])) {
        validOwners[fileID][owner['host']] = owner;
    }
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

function downloadFailed(fileID) {
    if (downloadActiveQueue[fileID].length == 0 && downloadCandidateQueue[fileID].length == 0) {
        //utils.assert(fileBlocksDownloadLeft[fileID].length > 0);//must download fail
        if (!downloadErrCallbackInvoked[fileID]) {
            if(debug) global.log.info('file download error! No fileOwners! downloadErr event. fileID:' + fileID);
            updateBlocksToDB(fileID);
            var MAX_TRY_TIME = 10;
            if (downloadTriedTimes[fileID] < MAX_TRY_TIME && Object.keys(validOwners[fileID]).length > 0) {
                //try to fix the file download
                if(debug) global.log.info('But I will try again:' + fileID);
                downloadTriedTimes[fileID] += 1;
                var goodOwners = Object.keys(validOwners[fileID]).map(function (key) {
                    return validOwners[fileID][key];
                });
                clearInterval(fileDownloadProgressTimer[fileID]);
                downloadFile(fileDownloadInfos[fileID], goodOwners, fileDownloadEventEmitter[fileID], fileDownloadOverCallbacks[fileID], downloadProgressCallbacks[fileID]);
            } else {
                fileDownloadOverCallbacks[fileID]('file download error! No fileOwners!');
                var fileHashAndSize = fileID.split('_');
                var fileHash = parseInt(fileHashAndSize[0]);
                var fileSize = parseInt(fileHashAndSize[1]);
                fileDownloadEventEmitter[fileID].emit("downloadErr", fileHash, fileSize);
                clearInterval(fileDownloadProgressTimer[fileID]);
                downloadErrCallbackInvoked[fileID] = true;
            }
        }
        fileDownloadStates[fileID] = DownloadState.DOWNLOAD_ERR;
        return true;
    }
    return false;
}

function userPausedOrCancelFileDownload(fileID) {
    if (!(fileID in fileDownloadStates)) {//file download canceled
        if(debug) global.log.info('file download pause or canceled...');
        restoreDownloadInfo(fileID);
        return true;
    }
    switch (fileDownloadStates[fileID]) {
        case DownloadState.PAUSED://file download pause
           if(debug) global.log.info('file download paused...');
            restoreDownloadInfo(fileID);
            return true;
        case DownloadState.DOWNLOADING://file download canceled
            break;
        case DownloadState.DOWNLOAD_OVER://file download canceled
        case DownloadState.DOWNLOAD_ERR://file download canceled
        default:
            utils.assert("logic error");
    }
    return false;
}

function downloadBlockHelper(fileInfo, localFile, owner, downloadEventEmitter, fileDownloadOverCallback) {
    utils.assert('host' in owner && 'port' in owner && 'uid' in owner);
    var fileHash = parseInt(fileInfo['hash']);
    var fileSize = parseInt(fileInfo['size']);
    var fileID = genFileID(fileHash, fileSize);
    if (userPausedOrCancelFileDownload(fileID)) return;

    var blockID = pop(fileBlocksDownloadLeft[fileID]);
    if ((typeof blockID) == 'undefined') {
        removeItemOfArray(downloadActiveQueue[fileID], owner);
        downloadCandidateQueue[fileID].push(owner);
        return;
    }
    blockID = parseInt(blockID);
    fileBlocksDownloading[fileID].push(blockID);
    //global.log.info('fileID:' + fileID + ' blockID:'+blockID+" owners:"+JSON.stringify(downloadActiveQueue[fileID])+" candidate:"+JSON.stringify( downloadCandidateQueue[fileID])+" downloading:"+JSON.stringify(fileBlocksDownloading[fileID])+" left:"+JSON.stringify(fileBlocksDownloadLeft[fileID]));
    var totalBlocksNum = fileBlocks(fileSize);
    utils.assert(blockID < totalBlocksNum);

    var start = blockID * config.BLOCK_SIZE;
    var end = blockID * config.BLOCK_SIZE + config.BLOCK_SIZE - 1;
    if (end >= fileSize) end = fileSize - 1;

    //if(!(fileID in fileDownloadAt)) fileDownloadAt[fileID]=Date.now();


    var options = {
        hostname: owner['host'],
        port: owner['port'],
        path: '/download?' + querystring.stringify({"hash": fileHash, "size": fileSize}),//use hash of the file to identify the file
        method: 'GET',
        //agent: false,
        headers: {//"Connection": 'keep-alive',//Sending a 'Connection: keep-alive' will notify Node that the connection to the server should be persisted until the next request.
                  "Range": start + "-" + end
        }
    };

    var chunks = [];
    var httpWritingStream = http.get(options, function (response) {
        response.on('data', function (chunk) {
            chunks.push(chunk);
        });

        var errorOccur = 0;
        //According to the documentation, a socket error event will be followed by a socket close event.
        response.on('error', function (err) {
            errorOccur = 1;
            if(debug) global.log.info("error in response occur:"+err);
        });

        response.on('close', function () {// event emit when the server has stopped! may not follow with end event!
            //global.log.info('**************close ....');
            if (userPausedOrCancelFileDownload(fileID)) return;

            if (errorOccur) {
                //global.log.info("http get response err:" + err);
                if(debug) global.log.info('errorOccur fileID:' + fileID + ' remove ower uid:' + owner["uid"] + " ip:" + owner["host"]);
                removeItemOfArray(downloadActiveQueue[fileID], owner);
                removeItemOfArray(fileBlocksDownloading[fileID], blockID);
                fileBlocksDownloadLeft[fileID].unshift(blockID);
                if (!downloadFailed(fileID)) {
                    downloadBlockFromOwner(fileID);
                }
            }
        });

        response.on('end', function () {// event emit when all data has come out!
            //I guess the main time consuming logic is here
            if (userPausedOrCancelFileDownload(fileID)) return;

            var chunksData = Buffer.concat(chunks);
            chunks = null;

            if ((response.statusCode == 404) || (chunksData.length != (end - start + 1))) {
                var needTryAgain = false;
                if (response.statusCode == 404) {
                    if(debug) global.log.info('Warning: 404 page found. ');
                    process.nextTick(function () {
                        var fbtHost = "friendsbt.com";
                        var fbtPort = 8888;
                        var fileID = fileHash.toString() + "_" + fileSize;
                        handleResource404(fbtHost, fbtPort, owner["uid"], fileID);
                    });
                    needTryAgain = false;
                } else {
                    if(debug) global.log.info('Error chunksData length ' + chunksData.length + " end:" + end + " start:" + start+' response.statusCode:'+response.statusCode);
                    needTryAgain = hasTriedEnough(owner, fileID);
                }
                removeItemOfArray(fileBlocksDownloading[fileID], blockID);
                fileBlocksDownloadLeft[fileID].unshift(blockID);
                if (needTryAgain) {
                    if(debug) global.log.info('Error chunks data. But try again. times:'+download503Queue[fileID][owner['host']]+" for owner:"+ owner["uid"] + " ip:" + owner["host"]);
                    setTimeout(function () {
                        downloadBlockHelper(fileInfo, localFile, owner, downloadEventEmitter, fileDownloadOverCallback);
                    }, 1000);
                } else {
                    if(debug) global.log.info('fileID:' + fileID + ' remove ower uid:' + owner["uid"] + " ip:" + owner["host"]);
                    removeItemOfArray(downloadActiveQueue[fileID], owner);
                    if (!downloadFailed(fileID)) {
                        downloadBlockFromOwner(fileID);
                    }
                }
            } else {
                utils.assert(response.statusCode == 206 || response.statusCode == 200);
                /*
                 var downloadedBlocksCnt = totalBlocksNum - fileBlocksDownloadLeft[fileID].length - fileBlocksDownloading[fileID].length;
                 var tempFile = localFile + tempSuffix;
                 if (downloadedBlocksCnt > 0 && !(fs.existsSync(tempFile)) && !(fs.existsSync(localFile))) {//user delete the file
                 delete fileDownloadStates[fileID];
                 if (!downloadErrCallbackInvoked[fileID]) {
                 global.log.info('file removed detected while downloading: ' + fileID);
                 fileDownloadOverCallback(errTips["remove"], fileHash, fileSize);//history download leave to controler
                 downloadEventEmitter.emit("downloadErr", fileHash, fileSize);
                 //clearInterval(fileDownloadProgressTimer[fileID]);
                 downloadErrCallbackInvoked[fileID] = true;
                 return;
                 }
                 }
                 */
                //var fileStreamToWrite = randomAccessFile(tempFile);
                var fileStreamToWrite = filesStream[fileID]; //randomAccessFile(tempFile);
                if (!fileStreamToWrite) return;//TODO FIXME must be a logic error
                fileStreamToWrite.write(blockID * config.BLOCK_SIZE, chunksData,
                    function (err) {
                        if (userPausedOrCancelFileDownload(fileID)) return;

                        if (err) {
                            fileStreamToWrite.close();
                            filesStream[fileID] = null;
                            delete fileDownloadStates[fileID];
                            if (!downloadErrCallbackInvoked[fileID]) {
                                if (err.code == 'ENOSPC') {
                                    fileDownloadOverCallback(errTips["spaceFull"], fileHash, fileSize);//history download leave to controler
                                } else {
                                    fileDownloadOverCallback(errTips["unknown"], fileHash, fileSize);//history download leave to controler
                                }
                                downloadEventEmitter.emit("downloadErr", fileHash, fileSize);
                                clearInterval(fileDownloadProgressTimer[fileID]);
                                downloadErrCallbackInvoked[fileID] = true;
                                //removeCache(fileID);
                            }
                            global.log.info('file download error! downloadErr event:' + err + ' fileID:' + fileID);
                        } else {
                            recordGoodOwners(owner, fileID);
                            recordDownloadedOwners(owner, fileID);
                            removeItemOfArray(fileBlocksDownloading[fileID], blockID);
                            removeItemOfArray(fileBlocksLeftRecord[fileID], blockID);

                            fileBlocksDownloaded[fileID].push(blockID);
                            var MAX_CACHE_CNT= 160;
                            if(fileBlocksDownloaded[fileID].length >= MAX_CACHE_CNT){
                                updateBlocksToDB(fileID);
                            }
                            //var progress = (1 - (fileBlocksDownloadLeft[fileID].length+fileBlocksDownloading[fileID].length) / totalBlocksNum).toFixed(4); //%.2f
                            /* //transient download speed
                             var downloadBytes = (totalBlocksNum - fileBlocksDownloadLeft[fileID].length-fileBlocksDownloading[fileID].length) * config.BLOCK_SIZE;
                             if (downloadBytes > fileSize) {
                             downloadBytes = fileSize;
                             }
                             var progress = ((downloadBytes+0.0)/fileSize).toFixed(4);
                             var downloadSpeed = (downloadBytes - fileDownloadBytes[fileID]) / ((Date.now()-fileDownloadAt[fileID])/1000);
                             fileDownloadBytes[fileID] = downloadBytes;
                             fileDownloadAt[fileID]=Date.now();
                             var FAKE_SPEED_RATE = 1.58;
                             downloadSpeed = downloadSpeed.toFixed(2) * FAKE_SPEED_RATE;
                             utils.assert(downloadSpeed >= 0);
                             process.nextTick(function () {
                             if (!downloadErrCallbackInvoked[fileID]){ //&& !downloadOKCallbackInvoked[fileID]) {
                             downloadProgressCallbacks[fileID](downloadBytes, progress, downloadSpeed);//report progress
                             }
                             });
                             */

                            //download over
                            if(downloadOver(fileID)){
                                fileDownloadStates[fileID] = DownloadState.DOWNLOAD_OVER;//the file download is over
                                fileStreamToWrite.close();
                                filesStream[fileID] = null;


                                if (!downloadOKCallbackInvoked[fileID]) {
                                    var tempFile = localFile + tempSuffix;
                                    fs.rename(tempFile, localFile, function (err) {
                                        if (err) global.log.info('rename file err. fileID:' + fileID);
                                        updateBlocksToDB(fileID);
                                        fileDownloadOverCallback(null, filesToSave[fileID], fileHash, fileSize, fileBlocksDownloadOwners[fileID].join(','));
                                        // no more use this owners
                                        delete fileBlocksDownloadOwners[fileID];
                                    });
                                    global.log.info('file download OK. fileID:' + fileID);
                                    downloadEventEmitter.emit("downloadOK", fileHash, fileSize);
                                    clearInterval(fileDownloadProgressTimer[fileID]);
                                    downloadOKCallbackInvoked[fileID] = true;
                                }
                                return;
                            }
                            process.nextTick(function () {
                                downloadBlockHelper(fileInfo, localFile, owner, downloadEventEmitter, fileDownloadOverCallback);
                            });
                        }
                    }
                );
            }
        });
    });


    httpWritingStream.on('error', function requestError(err) {
        if (userPausedOrCancelFileDownload(fileID)) return;
        //handle error if server not connect
        if(debug) global.log.info("request error:" + err);
        if(debug) global.log.info('fileID:' + fileID + ' remove ower uid:' + owner["uid"] + " ip:" + owner["host"]);
        httpWritingStream.abort();

        removeItemOfArray(fileBlocksDownloading[fileID], blockID);
        fileBlocksDownloadLeft[fileID].unshift(blockID);

        var needTryAgain = false;
        //if ((fileID in validOwners && owner['host'] in validOwners[fileID]) && (err.code == 'ECONNRESET')){ // The remote uploader is fake dead. I will try again.
        if (downloadCandidateQueue[fileID].length==0 && err.code == 'ECONNRESET'){ // The remote uploader is fake dead. I will try again.
            needTryAgain = hasTriedEnough(owner, fileID);                                   
        }       
        if(needTryAgain){
            if(debug) global.log.info("But I will try again.");
            setTimeout(function () {
                downloadBlockHelper(fileInfo, localFile, owner, downloadEventEmitter, fileDownloadOverCallback);
            }, 1000);   
        }else{
            removeItemOfArray(downloadActiveQueue[fileID], owner);
            if (!downloadFailed(fileID)) {
                downloadBlockFromOwner(fileID);
            }
        }
    });

    httpWritingStream.on('socket', function (socket) {
        socket.setTimeout(10000);
        socket.on('timeout', function () {
            httpWritingStream.abort();
        });
    });

}


function hasTriedEnough(owner, fileID){
    var needTryAgain = false;
    if (owner['host'] in download503Queue[fileID]) {
        var MAX_TRY_TIMES = 64;
        if (download503Queue[fileID][owner['host']] >= MAX_TRY_TIMES) {
            if(debug) global.log.info('I tried too many times, and give up!');
            needTryAgain = false;
        } else {
            download503Queue[fileID][owner['host']] += 1;
            needTryAgain = true;
        }
    } else {
        download503Queue[fileID][owner['host']] = 1;
        needTryAgain = true;
    }   
    return needTryAgain;
}

/**
 * remove file download from queue, delete downloaded file at the same time.
 *
 * fileHash: hash of file to remove from download queue
 * callback: callback when complete
 */
function removeFileDownload(fileHash, fileSize) {
    utils.assert(fileHash > 0);
    global.log.info("remove file download:" + fileID);
    var fileID = genFileID(fileHash, fileSize);
    clearInterval(fileDownloadProgressTimer[fileID]);
    removeCache(fileID);
}

function removeCache(fileID) {
    delete fileDownloadStates[fileID];
    delete fileBlocksDownloadLeft[fileID];
    delete fileBlocksLeftRecord[fileID];
    delete fileBlocksDownloaded[fileID];
    delete fileBlocksDownloadOwners[fileID];
    delete validOwners[fileID];
    delete downloadTriedTimes[fileID];
    delete fileBlocksDownloading[fileID];
    delete fileDownloadProgressTimer[fileID];

    delete downloadCandidateQueue[fileID];
    delete downloadActiveQueue[fileID];
    delete download503Queue[fileID];
    //added by bone
    delete downloadErrCallbackInvoked[fileID];
    delete downloadOKCallbackInvoked[fileID];
    delete fileDownloadOverCallbacks[fileID];
    delete downloadProgressCallbacks[fileID];
    delete filesToSave[fileID];
    filesStream[fileID] && filesStream[fileID].close();
    delete filesStream[fileID];
    delete fileDownloadInfos[fileID];
    delete fileDownloadEventEmitter[fileID];
    delete fileDownloadBytes[fileID];
    //delete fileDownloadAt[fileID];
}

/**
 * pause a file download
 *
 * fileHash: hash of file
 */
function pauseFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in fileDownloadStates && fileDownloadStates[fileID] == DownloadState.DOWNLOADING) {
        global.log.info("pause file download:" + fileID);
        fileDownloadStates[fileID] = DownloadState.PAUSED;
        updateBlocksToDB(fileID, false);
        clearInterval(fileDownloadProgressTimer[fileID]);
    }
}


/**
 * resume a file download
 *
 * fileHash: hash of file
 */
function resumeFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in fileDownloadStates && fileDownloadStates[fileID] == DownloadState.PAUSED) {
        global.log.info("resume file download:" + fileID);
        fileDownloadStates[fileID] = DownloadState.DOWNLOADING;
        downloadFile(fileDownloadInfos[fileID], downloadCandidateQueue[fileID], fileDownloadEventEmitter[fileID], fileDownloadOverCallbacks[fileID], downloadProgressCallbacks[fileID]);
    }
}

function handleResource404(fbtHost, fbtPort, uid, fileID) {
    utils.assert(fbtHost.length > 0);
    utils.assert(fbtPort > 0);
    utils.assert(uid >= 0);
    utils.assert(fileID.length > 0);

    var queryInfo = {'user': uid,
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
                //global.log.info("error in handleResource404");
            }
        });

        response.on('end', function () {// event emit when all data has come out!
            try {
                var chunksData = Buffer.concat(chunks);
                var json = JSON.parse(chunksData);
                if ('err' in json && json['err'] == 0) {
                    global.log.info("handleResource404 OK, fileID:" + fileID + " uid:" + uid);
                } else {
                    global.log.info("handleResource404 json err:", json);
                }
            } catch (e) {
                global.log.info("handleResource404 found server not update code.");
            }
        });
    });

    httpWritingStream.on('error', function (err) {
        global.log.info("error in http handleResource404:" + err);
    });
}

exports.pauseFileDownload = pauseFileDownload;
exports.resumeFileDownload = resumeFileDownload;
exports.removeFileDownload = removeFileDownload;
exports.downloadFile = downloadFile;
exports.myCleanup = myCleanup;
