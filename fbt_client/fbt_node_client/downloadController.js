/**
 *
 * Created by fbt on 14-7-26.
 */
var fileDownloadV6 = require('./fileDownloadV6/downloadFile');
var fileDownloadV6Plus = require('./fileDownloadV6/tcpDownloadFile');
//注释V4
var fileDownloadV4 = fileDownloadV6;//require('./fileDownloadV4/downloaderV4.js');
var fileDownloadLAN = fileDownloadV6; //require('./fileDownloadLAN/downloadFile');
var fileDownloadLANPlus = fileDownloadV6Plus;

var path = require('path');
var fs = require('fs');
var utils = require('./fbtUtils/fbtUtils');
var rmdir = require(path.join(global.exec_path, 'rimraf'));
var sets = require('./settings');

var fileDownloadQueue = [];
var filesToSave = {}; //local file to save
var currentDownloadCnt = 0;
var allDownloadInfos = {}; //all incoming download info is here

var config = {
    MAX_DOWNLOAD_CNT: 2
};
var fbtUID = null;
var fileDownloadTypes = {};
var fileDownloadImpl = {};
var DOWNLOAD_TYPE = {
    "None": 0,
    "V4_LAN": 1,
    "V4_NAT": 2,
    "V6": 3
};

var EventEmitter = require("events").EventEmitter;
var downloadEventEmitter = new EventEmitter();
downloadEventEmitter.on("downloadOK", function (fileHash, fileSize) {
    removeDownloadInfoCache(fileHash, fileSize);
    doWhatIfDownloadOKorErr(fileHash, fileSize, 0);
});

downloadEventEmitter.on("downloadErr", function (fileHash, fileSize) {
    removeDownloadInfoCache(fileHash, fileSize);
    doWhatIfDownloadOKorErr(fileHash, fileSize, 1);
});

function doWhatIfDownloadOKorErr(fileHash, fileSize, isErr) {
    if (isErr) {
        //callback to ui
        global.log.info("event downloadErr occurred");
    } else {
        global.log.info("event downloadOK occurred");
    }
    currentDownloadCnt -= 1;
    if (currentDownloadCnt < 0) {
        global.log.info("there must be a logic error in download....");
        currentDownloadCnt = 0;
    }

    global.log.info("free a file download in queue....");
    downloadFileInQueue();
}

function genFileID(fileHash, fileSize) {
    utils.assert(fileHash >= 0 && fileSize > 0);
    return fileHash + "_" + fileSize;
}

/**
 * add to file download queue
 *
 * arguments:
 * fileInfo: such as {file: name of the file,hash: hash of the file, size: file size}
 * fileOwners: the owner of the file, is an array such as [{host: ip1, port: port1},{host: ip2, port: port2}]
 * saveDir: the dir to save the file
 * downloadOverCallback: the callback for invoker when the file download is over
 * downloadProgressCallbacks: the download progress callback
 *
 */
function addToDownloadQueue(fbtUid, fileInfo, fileOwners, downloadType, saveDir, downloadOverCallback, downloadProgressCallback, queueAddedCallback) {
    //pack all the download info into download task queue.
    global.log.info("add to download queue");
    if ((fbtUid < 0) || (fileInfo['size'] <= 0) ||
        (fileInfo['file'].length <= 0) || (fileInfo['hash'] <= 0) ||
        (downloadType < 0) || (utils.len(fileOwners) <= 0) ||
        (!utils.isFunction(downloadOverCallback)) || //must provide download over callback
        (!utils.isFunction(downloadProgressCallback)) //must provide download progress callback
       ){
        global.log.info("argument err:" + saveDir);
        downloadOverCallback(sets.errTips['argument_err']);
        return;
    }

    var fileHash = fileInfo['hash'];
    var fileSize = fileInfo['size'];
    var fileID = genFileID(fileHash, fileSize);
    fbtUID = fbtUid;
    var fileName = fileInfo["file"];

    if (!fs.existsSync(saveDir)) {
        global.log.info("file save dir not exist:" + saveDir);
        try {
            fs.mkdirSync(saveDir);
            global.log.info("mkdir ok:" + saveDir);
        } catch (e) {
            global.log.info("mkdir failed:" + saveDir);
            // queueAddedCallback("无法创建下载路径：" + saveDir);
            downloadOverCallback(sets.errTips['download_dir_create_failed']);
            return;
        }
    }

    var tcpFileOwners = [];
    var httpFileOwners = [];
    var TCP_PORT = 8885;
    fileOwners.forEach(function (owner) {
        if (owner["port"] === TCP_PORT) {
            tcpFileOwners.push(owner);
        } else {
            httpFileOwners.push(owner);
        }
    });

    var savedFile = path.join(saveDir, fileName);
    global.log.info("file to save local:" + savedFile);
    filesToSave[fileID] = savedFile;
    fileDownloadTypes[fileID] = downloadType;
    switch (fileDownloadTypes[fileID]) {
        case DOWNLOAD_TYPE["V4_LAN"]:
            global.log.info("found V4 LAN download:" + fileID);
            if(tcpFileOwners.length > 0){
                fileDownloadImpl[fileID] = fileDownloadLANPlus;
                fileOwners = tcpFileOwners;
            }else{
                fileDownloadImpl[fileID] = fileDownloadLAN;
                fileOwners = httpFileOwners;
            }
            break;
        case DOWNLOAD_TYPE["V6"]:
            global.log.info("found V6 download:" + fileID);
            if(process.platform === "darwin") {
                global.log.info("Check Ok. It is mac. use http download:" + fileID);
                fileDownloadImpl[fileID] = fileDownloadV6;
                fileOwners = httpFileOwners;
            } else if (tcpFileOwners.length < 20 || tcpFileOwners.length > 100) {
                global.log.info("Check Ok. TCP download:" + fileID);
                fileDownloadImpl[fileID] = fileDownloadV6Plus;
                fileOwners = tcpFileOwners;
                /*
                if(httpFileOwners.length < 10 || httpFileOwners.length < tcpFileOwners.length ){
                    global.log.info("Check Ok. TCP download:" + fileID);
                    fileDownloadImpl[fileID] = fileDownloadV6Plus;
                    fileOwners = tcpFileOwners;
                }else{
                    global.log.info("Check Ok. Http download:" + fileID);
                    fileDownloadImpl[fileID] = fileDownloadV6;
                    fileOwners = httpFileOwners;
                }
                */
            }else{
                fileDownloadImpl[fileID] = fileDownloadV6;
                fileOwners = httpFileOwners;
            }
            break;
        case DOWNLOAD_TYPE["V4_NAT"]:
            global.log.info("found V4 NAT download:" + fileID);
            fileDownloadImpl[fileID] = fileDownloadV4;
            break;
        case DOWNLOAD_TYPE["None"]:
        default:
            utils.assert(false);
    }
    fileInfo['file_to_save'] = savedFile;
    if (fileID in allDownloadInfos) {//already in queue
        if (inArray(fileDownloadQueue, fileID)) {
            global.log.info("the file is already in queue:" + fileID + ", I will move it to bottom and update the download file info.");
            utils.removeArrayItem(fileDownloadQueue, fileID);
            fileDownloadQueue.push(fileID);//add to queue
        } else {//the file is downloading
            //queueAddedCallback("文件已在下载队列！", fileName);          
            global.log.info("the file is already in queue:" + fileID + ", and is downloading...");
            //return;
        }
    } else {
        fileDownloadQueue.push(fileID);//add to queue
    }

    allDownloadInfos[fileID] = {'fileInfo': fileInfo, 'fileOwners': fileOwners, 'saveDir': saveDir, 'downloadCallback': downloadOverCallback, 'progressCallback': downloadProgressCallback};
    // queueAddedCallback(null, fileName);

    downloadFileInQueue();
}

function downloadFileInQueue() {
    var concurrentDownloadCnt = config.MAX_DOWNLOAD_CNT;//Math.min(fileDownloadQueue.length, config.MAX_DOWNLOAD_CNT);
    global.log.info("concurrentDownloadCnt=" + concurrentDownloadCnt + " currentDownloadCnt=" + currentDownloadCnt);
    for (var i = 0; i < fileDownloadQueue.length; ++i) {
        var fileID = fileDownloadQueue[i];
        if (currentDownloadCnt < concurrentDownloadCnt) {
            utils.removeArrayItem(fileDownloadQueue, fileID);
            currentDownloadCnt += 1;
            global.log.info("the file is downloading:" + fileID);
            var fileOwners = allDownloadInfos[fileID]['fileOwners'];
            if (fileDownloadTypes[fileID] == DOWNLOAD_TYPE["V4_NAT"]) {// || fileDownloadTypes[fileHash]==DOWNLOAD_TYPE["V4_LAN"]){//for nat download
                fileOwners = fileOwners.map(function (arg) {
                    return arg['uid']
                }).join(',');//"uid1,uid2,....."
                global.log.info("fileOwners:" + fileOwners);
                fileDownloadImpl[fileID].downloadFile(
                    allDownloadInfos[fileID]['fileInfo'], fbtUID,
                    fileOwners, downloadEventEmitter, allDownloadInfos[fileID]["downloadCallback"],
                    allDownloadInfos[fileID]["progressCallback"]);
            } else {
                fileDownloadImpl[fileID].downloadFile(
                    allDownloadInfos[fileID]['fileInfo'], fileOwners,
                    downloadEventEmitter, allDownloadInfos[fileID]["downloadCallback"],
                    allDownloadInfos[fileID]["progressCallback"]);
            }
        } else {
            //wait
            global.log.info("waiting queue to free:" + fileID);
        }
    }
}

/**
 * remove file download from queue, delete downloaded file at the same time.
 *
 * fileHash: hash of file to remove from download queue
 * callback: callback when complete
 */
function removeFileDownloadFromQueue(isDir, fileSize, fileHash, callback) {
    utils.assert(fileHash > 0 && utils.isFunction(callback));
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in allDownloadInfos) {//already in queue
        global.log.info("remove file download from queue:" + fileID);
        if (!inArray(fileDownloadQueue, fileID)) {//the file is downloading
            currentDownloadCnt -= 1;
            if (currentDownloadCnt < 0) {
                global.log.info("the must be a logic error in download....");
                currentDownloadCnt = 0;
            }
        }
    }
    fileDownloadImpl[fileID] && fileDownloadImpl[fileID].removeFileDownload(fileHash, fileSize);
    removeFileInSaveDir(isDir, fileHash, fileSize, callback);
    removeDownloadInfoCache(fileHash, fileSize);
    // download next file in queue
    downloadFileInQueue();
}

function removeDownloadInfoCache(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    utils.removeArrayItem(fileDownloadQueue, fileID);
    delete allDownloadInfos[fileID];
    delete fileDownloadImpl[fileID];
    delete fileDownloadTypes[fileID];
    delete filesToSave[fileID];
}

function removeFileInSaveDir(isDir, fileHash, fileSize, callback) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in filesToSave) {
        var file = filesToSave[fileID];
        if(isDir){
            rmdir(path.dirname(file), function(err){
                if (err) {
                    global.log.info("del dir err:" + err+' file:'+file);
                } else {
                    global.log.info('successfully deleted dir:' + file);
                }
            });
        }else{
            fs.unlink(file + ".tmp", function (err) {//delete temp file
                if (err) {
                    global.log.info("del file err:" + err);
                } else {
                    global.log.info('successfully deleted file:' + file + " fileID:" + fileID);
                }
                delete filesToSave[fileID];
            });
        }
    }
    else {
        global.log.info("file not in download queue:" + fileID);
    }
    callback(null);
    //else ???? is there a bug???
}


/**
 * pause a file download
 *
 * fileHash: hash of file
 */
function pauseFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in allDownloadInfos) {//already in queue
        global.log.info("pause file download in control:" + fileID);
        if (!inArray(fileDownloadQueue, fileID)) {//the file is downloading
            fileDownloadImpl[fileID] && fileDownloadImpl[fileID].pauseFileDownload(fileHash, fileSize);
            currentDownloadCnt -= 1;
            if (currentDownloadCnt < 0) {
                global.log.info("the must be a logic error in download....");
                currentDownloadCnt = 0;
            }
            // download next file in queue
            downloadFileInQueue();
        }
    }
}


/**
 * resume a file download
 *
 * fileHash: hash of file
 */
function resumeFileDownload(fileHash, fileSize) {
    var fileID = genFileID(fileHash, fileSize);
    if (fileID in allDownloadInfos) {//already in queue
        global.log.info("resume file download in control:" + fileID);
        if (!inArray(fileDownloadQueue, fileID)) {//the file is downloading
            fileDownloadImpl[fileID] && fileDownloadImpl[fileID].resumeFileDownload(fileHash, fileSize);
            currentDownloadCnt += 1;
        }
    }
}

function inArray(array, data) {
    for (var i = 0; i < array.length; i++) {
        if (array[i] === data) return true;
    }
    return false;
}

function cleanup() {
    fileDownloadV6.myCleanup();
}

exports.addToDownloadQueue = addToDownloadQueue;
exports.removeFileDownloadFromQueue = removeFileDownloadFromQueue;
exports.pauseFileDownload = pauseFileDownload;
exports.resumeFileDownload = resumeFileDownload;
exports.cleanup = cleanup;
