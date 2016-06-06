var fs = require('fs');
var paths = require('path');
var EventEmitter = require('events').EventEmitter;
var randomAccessFile = require(paths.join(global.exec_path, 'random-access-file'));
var chatRoomTalker = require('./chatRoom-talker.js');
var res_api = require('../res/res_api');
var settings = require('./settings');
var global_settings = require('../settings');

var DUP = global_settings.errTips["duplicatedDownload"],
    HISTORY_DOWNLOAD = global_settings.errTips["historyDownload"],
    SPACEFULL = global_settings.errTips["spaceFull"],
    INVA = global_settings.errTips["invalidOwners"],
    UNKNOWN = global_settings.errTips["unknown"],
    REMOVE = global_settings.errTips["remove"],
    XPV4 = global_settings.errTips["xp_v4"],
    V4_FAILED = global_settings.errTips["v4_failed"];

function sleep(milliSeconds) {
  var startTime = new Date().getTime();
  while (new Date().getTime() < startTime + milliSeconds);
}

var downloaders = global.downloaders;

var forwardDownloader = module.exports = function(
  fileInfo,
  my_uid,
  uploaderUidList,
  e, 
  downloadOverCallback,
  downloadProgressCallback
) {
  this.DownloadState = {
    DOWNLOAD_OVER: 0,
    DOWNLOADING: 1,
    CANCELED: 2,
    PAUSED: 3,
    DOWNLOAD_ERR: 4,
    ALREADY_COMPLETE: 5
  };
  this.BLOCKSIZE = 64*1024; //1024*1024; // 1MB

  this.piecesize = 64*1024; //64KB
  this.pieceindex = 0;
  this.pieces_left = []; // Set by initPieces
  this.parts_left = []; // Set by startFileDownload
  this.complete_parts = [];
  this.lastTime = null; // Set by startFileDownload

  this.file_to_save = fileInfo.file_to_save;
  this.file_to_save_tmp = this.file_to_save + '.tmp';
  this.filesize = fileInfo.size;
  this.hash = fileInfo.hash;

  this.state = null;
  this.uploaderUidList = (function(list) {
    var set = {};
    list.forEach(function(i) {
        set[i] = null;
    });
    return Object.keys(set);
  }(uploaderUidList));
  this.uploaderindex = 0;
  this.retrytime = 0;
  this.response = null;
  
  this.my_uid = my_uid;

  var that = this;

  this.downloader = new chatRoomTalker('http://211.149.223.98:8099', my_uid);
  this.downloader.onError = function(error) {
    that.response = 'Error';
    if(error) {
      if(that.retrytime >= 3) {
        global.log.info('Cannot find valid uploader!');
        that.downloadOverCallback(INVA);
        downloaders[that.hash].cancelFileDownload();
        return;
      }

      setTimeout(function() {
        that.uploaderindex = (that.uploaderindex+1) % that.uploaderUidList.length;
        global.log.info('Retry uploader index: ' + that.uploaderUidList[that.uploaderindex]);

        if(that.uploaderindex === (that.uploaderUidList.length-1)) {
          that.retrytime++;
          global.log.info('Retry time: ' + that.retrytime);
        }
        that.resumeFileDownload();
      }, 5000)
    }
  };
  this.downloader.onMessage = function(sUid, message) {
    that.response = 'Message';
    this.retrytime = 0;
    if(that.state !== that.DownloadState.DOWNLOADING) {
      return;
    }
    // Reject unexpected block
    if((that.pieces_left.indexOf(message.pieceindex) < 0)
      || (message.hash !== that.hash)) {
      return;
    }

    // Hash validation
    /*
    var isHashCorrect
      = !message.piecehash || message.piecehash
      === crypto.createHash('md5').update(message.data).digest('hex');
    */
    var isHashCorrect = true;

    if (!message.data) { //EOF
      that.state = that.DownloadState.DOWNLOAD_OVER;
      global.log.info("forwardDownloader downloadOver1");
      res_api.record_uploader(that.hash, that.my_uid);
      downloaders[that.hash].downloadOver();
      return;
    }

    if(isHashCorrect) {
      var file = randomAccessFile(that.file_to_save_tmp, that.filesize);
      try {
        file.write(
            message.pieceindex * that.piecesize,
          message.data,
          function (error) {
            file.close();
            that.pieceindex++;

            if (message.piecesize < that.piecesize) {
              that.state = that.DownloadState.DOWNLOAD_OVER;
              global.log.info("forwardDownloader downloadOver2");
            }
            
            that.updatePartsLeft(message.pieceindex);

            // downloadOver() must be after updatePartsLeft()
            if (that.state == that.DownloadState.DOWNLOAD_OVER) {
              res_api.record_uploader(that.hash, that.my_uid);
              downloaders[that.hash].downloadOver();
            }

            // Calculate speed
            var download_Bs = that.filesize - (that.pieces_left.length - that.pieceindex) * that.piecesize;
            download_Bs = download_Bs < 0 ? that.pieceindex * that.piecesize : download_Bs;
            var progress = download_Bs / that.filesize;
            var downloadSpeed = (function (nowTime) {
              var speed = that.piecesize / (nowTime - that.lastTime);
              that.lastTime = nowTime;
              return speed;
            }(Date.now() / 1000));

            if (that.state === that.DownloadState.DOWNLOADING) {
              if (that.pieces_left.length) {
                that.downloadProgressCallback(download_Bs, progress, downloadSpeed);

                // Get the next part(block)
                // Which uploader should I use?
                that.downloader.send(that.uploaderUidList[that.uploaderindex], {
                  hash: that.hash,
                  filesize: that.filesize,
                  pieceindex: that.pieces_left[that.pieceindex],
                  piecesize: that.piecesize
                });
              }
            }
          }
        );
      } catch(e) {
        if (e.code === 'ENOSPC') {
          that.e.emit("downloadErr", hash);
          that.downloadOverCallback(SPACEFULL);
          downloaders[that.hash].cancelFileDownload();
        }
      }
    }
    else {
      global.log.info('hash incorrect');
    }
  };

  this.downloadOverCallback = downloadOverCallback;
  this.downloadProgressCallback = downloadProgressCallback;
};


forwardDownloader.prototype.__proto__ = EventEmitter.prototype;


forwardDownloader.prototype.updatePartsLeft = function(pieceindex) {
  var partsToRemove = downloaders[this.hash].partsToRemove;
  if (this.state === this.DownloadState.DOWNLOAD_OVER) {
    var blockindex = this.parts_left[this.parts_left.length-1];
    //global.log.info("REMOVING1 ... " + blockindex);
    partsToRemove.push(blockindex);
    res_api.remove_part_from_parts_left(this.hash, partsToRemove, true);  // compact
    partsToRemove.length = 0;

    this.pieceindex = 0;
    this.pieces_left = [];
    this.parts_left = [];
    this.complete_parts = [];
  } else {
    var index = this.pieces_left.indexOf(pieceindex);
    if(index > -1) {
      var piecenum = this.BLOCKSIZE / this.piecesize;
      if((this.pieceindex + 1) % piecenum === 0) {
        index = Math.floor(this.pieceindex / piecenum) - 1;
        this.blockindex =  this.parts_left[index];

        this.complete_parts.push(this.blockindex);
        //global.log.info("REMOVING2 ... " + this.blockindex);
        partsToRemove.push(this.blockindex);
        if (partsToRemove.length >= downloaders[this.hash].MAX_LEN) {
          res_api.remove_part_from_parts_left(this.hash, partsToRemove);
          partsToRemove.length = 0;
        }
      }
    }
  }
};


forwardDownloader.prototype.initPieces = function(parts_left) {
  this.pieceindex = 0;
  this.parts_left = parts_left;
  this.pieces_left = (function makePieces(that) {
    var pieces = [];
    that.parts_left.forEach(function(blockindex) {
      var piecenum = that.BLOCKSIZE/that.piecesize;
      for(var pieceindex = 0; pieceindex < piecenum; pieceindex++) {
        pieces.push(blockindex * piecenum + pieceindex);
      }
    });
    return pieces;
  }(this));
  this.pieces_flag = (function initPiecesFlag(that) {
    var flags = [];
    for(var pieceindex in that.pieces_left) {
      flags.push(0); // Set flag to 1 when piece downloaded
    }
    return flags;
  }(this));
};


forwardDownloader.prototype.startFileDownload = function(parts_left) {
  //global.log.info('startFileDownload: ' + parts_left);
  this.state = this.DownloadState.DOWNLOADING;
  this.lastTime = Date.now() / 1000;
  this.initPieces(parts_left);

  var that = this;
  that.response = null;
  //global.log.info('forwardDownloader parts_left: ' + parts_left);
  that.downloader.send(this.uploaderUidList[this.uploaderindex], {
    hash: that.hash,
    filesize: that.filesize,
    pieceindex: that.pieces_left[that.pieceindex],
    piecesize: that.piecesize //Download block piece by piece
  });

  setTimeout(function() {
    if(that.response == null) {
      global.log.info('Timeout!');
      that.downloader.onError('Timeout!');
    }
  }, 10000);
};


forwardDownloader.prototype.pauseFileDownload = function() {
  this.state = this.DownloadState.PAUSED;
};


forwardDownloader.prototype.resumeFileDownload = function() {
  this.state = this.DownloadState.DOWNLOADING;
  this.startFileDownload(this.parts_left);
};


forwardDownloader.prototype.cancelFileDownload = function() {
  this.state = this.DownloadState.CANCELED;
  if(fs.existsSync(this.file_to_save)) {
    fs.unlinkSync(this.file_to_save);
    global.log.info('Deleted ' + this.file_to_save);
  }
  else if(fs.existsSync(this.file_to_save_tmp)) {
    fs.unlinkSync(this.file_to_save_tmp);
    global.log.info('Deleted ' + this.file_to_save_tmp);
  }

  res_api.remove_record_from_parts_left(this.hash);

  this.pieceindex = 0;
  this.pieces_left = [];
  this.parts_left = [];
  this.complete_parts = [];
};


forwardDownloader.prototype.on('pause', function() {
  this.pauseFileDownload();
});


forwardDownloader.prototype.on('resume', function() {
  this.resumeFileDownload();
});


forwardDownloader.prototype.on('cancel', function() {
  this.cancelFileDownload();
});
