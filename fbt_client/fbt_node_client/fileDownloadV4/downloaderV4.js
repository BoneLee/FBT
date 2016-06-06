var fs = require('fs');
var paths = require('path');
var raf = require(paths.join(global.exec_path, 'random-access-file'));
var res_api = require('../res/res_api');
var settings = require('./settings');
var global_settings = require('../settings');

var downloaders = {};  // node 环境中保存所有 V4Downloader
global.downloaders = downloaders;

var forwardDownloader = require('./forwardDownloader');
var peerjsDownloader = require('./peerDownloader').peerjsDownloader;

var DOWNLOAD_OVER = settings.DownloadState['DOWNLOAD_OVER'],
    DOWNLOADING = settings.DownloadState['DOWNLOADING'],
    CANCELED = settings.DownloadState['CANCELED'],
    PAUSED = settings.DownloadState['PAUSED'],
    DOWNLOAD_ERR = settings.DownloadState['DOWNLOAD_ERR'],
    ALREADY_COMPLETE = settings.DownloadState['ALREADY_COMPLETE'];

var DUP = global_settings.errTips["duplicatedDownload"],
    HISTORY_DOWNLOAD = global_settings.errTips["historyDownload"],
    SPACEFULL = global_settings.errTips["spaceFull"],
    INVA = global_settings.errTips["invalidOwners"],
    UNKNOWN = global_settings.errTips["unknown"],
    REMOVE = global_settings.errTips["remove"],
    XPV4 = global_settings.errTips["xp_v4"],
    V4_FAILED = global_settings.errTips["v4_failed"];

function v4Downloader(fileInfo, my_uid, uploader_uids, e,
        downloadOverCallback, downloadProgressCallback) {
  this.my_uid = my_uid;
  this.innerDownloader = new peerjsDownloader(fileInfo);
  this.hash = fileInfo.hash;
  this.size = fileInfo.size;
  this.file_to_save = fileInfo.file_to_save;
  this.fileInfo = fileInfo;
  this.file_to_save_tmp = fileInfo.file_to_save + '.tmp';
  this.uploaderUidList = uploader_uids.split(',');
  this.descriptor = raf(this.file_to_save_tmp);
  this.complete_parts = 0;
  this.total_parts = parseInt((fileInfo.size+settings.partsize-1)/settings.partsize);
  this.e = e;
  this.downloadOverCallback = downloadOverCallback;
  this.downloadProgressCallback = downloadProgressCallback;
  this.status = DOWNLOADING;
  this.partsToRemove = [];  // record complete but not removed parts
  this.MAX_LEN = Math.ceil(this.total_parts / 100);
  this.MAX_LEN = this.MAX_LEN <= 160 ? this.MAX_LEN : 160;
  this.lastDownloadState = {
    lastTime: Date.now() / 1000,
    calcSpeed: function (nowTime) {
      var speed = settings.partsize / (nowTime - this.lastTime);
      this.lastTime = nowTime;
      return speed;
    }
  };
}

v4Downloader.prototype.startFileDownload = function(parts_left) {
  this.innerDownloader.startFileDownload(parts_left);
  var file_watch = this.file_to_save_tmp;
  var that = this;
  var intervalObj = setInterval(function(){
    if (fs.existsSync(file_watch)) {
      watchFile();
      clearInterval(intervalObj);
    }
  }, 1000);
  function watchFile() {
    that.watcher = fs.watch(file_watch, function (event) {
      if (event === 'rename') {
        if (!fs.existsSync(file_watch)) {
          global.log.info("file removed or renamed during downloading.");
          if (!fs.existsSync(that.file_to_save)) {
            that.cancelFileDownload();
            that.watcher.close();
            delete that.watcher;
            that.e.emit("downloadErr", that.hash, -1);
            that.downloadOverCallback(REMOVE);
          }
        }
      }
    });
  }
};

v4Downloader.prototype.pauseFileDownload = function() {
  this.status = PAUSED;
  this.innerDownloader.pauseFileDownload();
};

v4Downloader.prototype.resumeFileDownload = function() {
  this.status = DOWNLOADING;
  this.innerDownloader.resumeFileDownload();
};

v4Downloader.prototype.cancelFileDownload = function() {
  if (this.status === DOWNLOADING || this.status === PAUSED) {
    this.status = CANCELED;
    this.innerDownloader.cancelFileDownload();
    if (fs.existsSync(this.file_to_save_tmp)) {
      fs.unlinkSync(this.file_to_save_tmp);
    }
    res_api.remove_record_from_parts_left(this.hash);
    this.descriptor.close();
    this.innerDownloader = null;
    if (this.watcher) {
      this.watcher.close();
    }
  }
};

v4Downloader.prototype.useForward = function() {
  // can't use Peerjs so use forward mode
  // TODO: safe delete this.innerDownloader, simple delete may leak memory
  delete this.innerDownloader;
  this.innerDownloader = new forwardDownloader(
    this.fileInfo,
    this.my_uid,
    this.uploaderUidList,
    this.e,
    this.downloadOverCallback,
    this.downloadProgressCallback
  );
  var d = this;
  res_api.get_parts_left(d.hash, function(parts_left){
    d.startFileDownload(parts_left);
  });
};

v4Downloader.prototype.downloadOver = function(){
  global.log.info("downloadOver called");
  var that = this;
  if (this.watcher) {
    this.watcher.close();  // fs.FSWatcher.close()
  }
  if (this.descriptor) {
    this.descriptor.close();
  }
  global.socket.emit("complete", this.hash);
  fs.rename(
    this.file_to_save_tmp,
    this.file_to_save,
    function(err) {
      if (err) {
        global.log.err(err);
      }
    }
  );
  this.innerDownloader = null;
  delete downloaders[this.hash];
  res_api.get_uploaders(this.hash, function(uploaders){
    if (uploaders) {
      uploaders = uploaders.join(',');
    } else {
      uploaders = '';
    }
    that.e.emit("downloadOK", that.hash, -1);
    that.downloadOverCallback(null, that.file_to_save, that.hash, that.size, uploaders);
    global.log.info("call downloadOverCallback with args" + JSON.stringify({
        "file": that.file_to_save,
        "hash": that.size,
        "uploaders": uploaders
    }));
  });
};

exports.downloadFile = function(fileInfo, my_uid, uploader_uids,
                                e, downloadOverCallback, downloadProgressCallback) {
  fileInfo.size = parseInt(fileInfo.size);
  var d = new v4Downloader(
    fileInfo,   // {size, hash, file_to_save}
    my_uid,
    uploader_uids,
    e,
    downloadOverCallback,
    downloadProgressCallback
  );
  downloaders[fileInfo.hash] = d;
  var hash = fileInfo.hash;
  res_api.get_parts_left(hash, function(parts_left){
    if (parts_left) {
      if (fs.existsSync(d.file_to_save) || fs.existsSync(d.file_to_save_tmp)){
        if (parts_left.length === 0) {
          global.log.info("already complete");
          d.complete_parts = d.total_parts;
          e.emit("downloadOK", fileInfo.hash, -1);
          downloadProgressCallback(fileInfo.size, 1.0, 0);
          downloadOverCallback(HISTORY_DOWNLOAD);
          global.socket.emit('setState', {
            hash: hash,
            state: ALREADY_COMPLETE
          });
        } else {
          global.log.info("resume unfinished downloading, parts left: " + parts_left.length);
          d.complete_parts = d.total_parts - parts_left.length;
          d.startFileDownload(parts_left);
        }
      } else {
        global.log.info("file does not exist, redownload file");
        parts_left.length = 0;
        for (var i = 0; i < d.total_parts; i++) {
          parts_left.push(i);
        }
        res_api.update_parts_left(hash, parts_left);
        d.startFileDownload(parts_left);
      }
    } else {
      global.log.info("new download");
      parts_left = [];
      for (i = 0; i < d.total_parts; i++) {
        parts_left.push(i);
      }
      res_api.update_parts_left(hash, parts_left);
      d.startFileDownload(parts_left);
    }
  });
};

exports.pauseFileDownload = function(hash) {
  downloaders[hash].pauseFileDownload();
};

exports.resumeFileDownload = function(hash) {
  downloaders[hash].resumeFileDownload();
};

exports.removeFileDownload = function(hash) {
  downloaders[hash].cancelFileDownload();
  delete downloaders[hash];
};
