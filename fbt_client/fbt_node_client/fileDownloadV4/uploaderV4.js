var fs = require('fs');
var settings = require('./settings');
var utils = require('./utils');
var res_api = require('../res/res_api');
var BLOCK_SIZE = settings.BLOCK_SIZE;


var fds = {};
var bf1 = Buffer(settings.partsize);

exports.initV4Upload = function(downloader_uid, hash, filesize){
  if (parseInt(process.versions['node-webkit'].split('.')[1]) < 10) {
    // don't support V4 upload
    return;
  }
  var totalFullBlocks = parseInt(filesize / BLOCK_SIZE);
  var realLastBlockSize = filesize - BLOCK_SIZE * totalFullBlocks;
  global.log.info('totalblock:' + totalFullBlocks.toString());
  global.log.info('lastblocksize:' + realLastBlockSize.toString());
  res_api.getPathUsingHashAndSize(hash, filesize, function(path){
    if (!fds[path]) {
      fds[path] = fs.openSync(path, 'r');
    }
    setTimeout(function(){
      global.socket.emit('connect_downloader', {
        'my_uid': global.uid,
        'downloader_uid': downloader_uid,
        'fileInfo': {
          'totalFullBlocks': totalFullBlocks,
          'realLastBlockSize': realLastBlockSize,
          'hash': hash,
          'path': path,
          'size': filesize
        }
      });
    }, 2000);
  });
};

global.socket.on("closefd", function(path){
  if (fds[path]) {
    fs.close(fds[path], function(err){
      if (err) {
        global.log.error(err);
      } else {
        global.log.info("uploader close fd");
        delete fds[path];
      }
    });
  }
});

global.socket.on('send_data_blocks', function(msg) {
  /*
  last_block_size = BLOCK_SIZE, unless the last block of file will be sent here
  msg {path, start, end, lastBlockSize, downloader, hash, test}
   */
  var fd = fds[msg.path];
  var index = msg.start;
  var bytesIndex = 0;   // slice start bytes index
  var dataNode2DOM;
  fs.read(fd, bf1, 0, settings.partsize, index*BLOCK_SIZE, function(err, bytesRead, data){
    if (err) {
      global.log.info("read index ", index, "error");
      console.log(err);
    } else {
      while (true) {
        if (index >= msg.end) {
          dataNode2DOM = {
            content: utils.toArrayBuffer(data.slice(bytesIndex, bytesIndex + msg.lastBlockSize)),
            hash: msg.hash,
            index: index,
            downloader: msg.downloader,
            test: msg.test
          };
          // 如果start=end, 说明是单独的重传请求, 这时 rangeLastBlock 应该为false
          // 否则下载端接到这个块之后会认为一个part传完了, 但其实只是重传, 该part-complete消息
          // 应该之前就emit过了
          dataNode2DOM.rangeLastBlock = (msg.start !== msg.end);
          global.socket.emit('send_block', dataNode2DOM);
          break;
        } else {
          dataNode2DOM = {
            content: utils.toArrayBuffer(data.slice(bytesIndex, bytesIndex + BLOCK_SIZE)),
            hash: msg.hash,
            index: index,
            downloader: msg.downloader,
            test: msg.test,
            rangeLastBlock: false
          };
          global.socket.emit('send_block', dataNode2DOM);
          index++;
          bytesIndex += BLOCK_SIZE;
        }
      }
    }
  });
});

