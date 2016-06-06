var paths = require('path');
var settings = require('./settings');
var global_settings = require('../settings');
var res_api = require('../res/res_api');

var DUP = global_settings.errTips["duplicatedDownload"],
    HISTORY_DOWNLOAD = global_settings.errTips["historyDownload"],
    SPACEFULL = global_settings.errTips["spaceFull"],
    INVA = global_settings.errTips["invalidOwners"],
    UNKNOWN = global_settings.errTips["unknown"],
    REMOVE = global_settings.errTips["remove"],
    XPV4 = global_settings.errTips["xp_v4"],
    V4_FAILED = global_settings.errTips["v4_failed"];

var BLOCK_SIZE = settings.BLOCK_SIZE;
var downloaders = global.downloaders;

global.socket.on('receive', function(dataDOM2Node){
  var hash = dataDOM2Node.hash;
  try {
    downloaders[hash].descriptor.write(
      dataDOM2Node.index * BLOCK_SIZE,
      dataDOM2Node.content,
      function (err) {
        if (err) {
          global.log.info(err);
        }
      }
    );
  } catch(e) {
    if (e.code === 'ENOSPC') {
      downloaders[hash].e.emit("downloadErr", hash);
      downloaders[hash].downloadOverCallback(SPACEFULL);
      downloaders[hash].cancelFileDownload();
    }
  }
});

global.socket.on("part-complete", function(partInfo){
  var hash = partInfo.hash;
  var partsToRemove = downloaders[hash].partsToRemove;

  downloaders[hash].complete_parts++;
  partsToRemove.push(partInfo.index);
  if (partsToRemove.length >= downloaders[hash].MAX_LEN) {
    res_api.remove_part_from_parts_left(hash, partsToRemove);
    partsToRemove.length = 0;
  }
  var download_Bs = null;
  if (downloaders[hash].complete_parts === downloaders[hash].total_parts) {
    global.log.info("receive complete, ", Date());
    download_Bs = downloaders[hash].fileInfo.size;
    res_api.remove_part_from_parts_left(hash, partsToRemove, true);  // compact
    partsToRemove.length = 0;
    setTimeout(function(){  // 最后一个block可能还没有写入, 必须延迟一点关闭文件
      downloaders[hash].downloadOver();
    }, 1000);
  }
  download_Bs = download_Bs || downloaders[hash].complete_parts * settings.partsize;
  var progress = downloaders[hash].complete_parts / downloaders[hash].total_parts;
  var downloadSpeed = downloaders[hash].lastDownloadState.calcSpeed(Date.now()/1000);
  downloaders[hash].downloadProgressCallback(download_Bs, progress, downloadSpeed);
});

global.socket.on("uploader", function(info) { // 记录某个资源的上传者
  global.log.info("record uploader:", info.uploader);
  global.window.console.log("record uploader:", info.uploader);
  res_api.record_uploader(info.hash, info.uploader);
});

global.socket.on("forward", function(hash){  // 切换转发模式
  downloaders[hash].useForward();
  global.log.info("V4 use forward mode");
});

var peerjsDownloader = function(fileInfo) {
  this.hash = fileInfo.hash;
  this.size = fileInfo.size;
  this.file_to_save = fileInfo.file_to_save;
};

peerjsDownloader.prototype.startFileDownload = function(parts_left){
  global.socket.emit('downloadV4', {
    hash: this.hash,
    parts_left: parts_left
  });
};

peerjsDownloader.prototype.pauseFileDownload = function(){
  global.socket.emit('setState', {
    hash: this.hash,
    state: settings.DownloadState.PAUSED
  });
};

peerjsDownloader.prototype.resumeFileDownload = function(){
  global.socket.emit('setState', {
    hash: this.hash,
    state: settings.DownloadState.DOWNLOADING
  });
};

peerjsDownloader.prototype.cancelFileDownload = function(){
  global.socket.emit('setState', {
    hash: this.hash,
    state: settings.DownloadState.CANCELED
  });
};

exports.peerjsDownloader = peerjsDownloader;
