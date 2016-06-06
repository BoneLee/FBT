var fs = require('fs');
var settings = require('./settings');
var utils = require('./utils');
var res_api = require('../res/res_api');
var paths = require('path');
var randomAccessFile = require(paths.join(global.exec_path, 'random-access-file'));

var chatRoomTalker = require('./chatRoom-talker.js');
var uploader = new chatRoomTalker(settings.forwardServerAddr, global.uid);
uploader.onError = function(error) {
  global.log.error(error);
};

uploader.onMessage = function(sUid, message) {
  global.log.info(message);
  var filehash = message.hash;
  var filesize = message.filesize;
  var pieceindex = message.pieceindex;
  var piecesize = message.piecesize;

  res_api.getPathUsingHashAndSize(filehash, filesize, function(path) {
    // TODO: 这个地方之后最好把fd保存起来, 类似于我的fds, 关键是最后要知道何时把fd给关掉
    var file = randomAccessFile(path);
    var isLastPiece = (filesize-pieceindex*piecesize < piecesize);
    var readsize = isLastPiece ? filesize-pieceindex*piecesize : piecesize;

    if(readsize <= 0) {
      uploader.send(sUid, {
        hash: filehash,
        filesize: filesize,
        pieceindex: pieceindex,
        piecesize: readsize,
        piecehash: null,
        data: null //EOF
      });
      return;
    }

    file.read(pieceindex*piecesize, readsize, function(error, data) {
      if(error) {
        global.log.info(sUid + ' wants file:' + filehash + ' pieceindex:' + pieceindex + ' readsize:' + readsize);
        global.log.error(error);
        return;
        //return process.exit(1);
      }

      uploader.send(sUid, {
        hash: filehash,
        filesize: filesize,
        pieceindex: pieceindex,
        piecesize: readsize,
        piecehash: 11111,
        data: data
      });
      file.close();
    });
  });
};
