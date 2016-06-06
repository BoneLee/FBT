//var $ = require('jquery');

exports.setWindow = function(window) {
  global.window = window;
  global.window.console.log("init window succeed");
};

function check(win, callback) {
  var net = require('net');
  var tester = net.createServer()
    .once('error', function(err) {
      if (err.code != 'EADDRINUSE') return err; {
        win.alert("很抱歉，在同一台电脑上我们暂时只支持一个客户端的运行，点击后退出。");
        //process.emit('exit');
        process.exit(1);
      }
    })
    .once('listening', function() {
      tester.once('close', function() {
          main();
          callback();
        })
        .close();
    })
    .listen(12345);
}
exports.check = check;
////////////

var utils = require('./fbtUtils/fbtUtils');
var child_process = require('child_process');
var doubanUtil = require('./fbtUtils/douban');

var fs = require("fs");
var path_s = require("path");

var httpServer = require('./fileDownloadV6/run.js');

function isEmpty(map) {
  for (var key in map) {
    if (map.hasOwnProperty(key)) {
      return false;
    }
  }
  return true;
}
var uploadList = {};
uploadList.uploadNum = 0;
uploadList.uploadQueue = {};
uploadList.uploadQueueLegnth = 0;
uploadList.timeout = 0;
uploadList.hashToPath = {};
uploadList.addOrStart = function(uploadFn, key) {
  uploadList.uploadQueue[key] = uploadFn;
  uploadList.uploadQueueLegnth++;
  if (!global.uploadInterval) {
    global.uploadInterval = setInterval(uploadList.startTask, 10000);
    uploadList.timeout = 0;
  }
  global.socket.once("cancel-upload"+key, function(upload_id){
    global.log.info("cancel upload");
    uploadList.delOrStart();
    uploadList.delUpload(upload_id);
  });
};
uploadList.delOrStart = function() {
  uploadList.uploadNum--;
};
uploadList.delUpload = function(key) {
  if (key in uploadList.uploadQueue) {
    global.log.info(key + " into upload del");
    uploadList.uploadQueue[key].clear();
    delete uploadList.uploadQueue[key];
    uploadList.uploadQueueLegnth--;
  } else {
    global.log.info(key + " upload del error");
  }
};
uploadList.getUpload = function(key) {
  if (key in uploadList.uploadQueue) {
    return uploadList.uploadQueue[key];
  } else {
    global.log.info(key + " upload get error");
    return "";
  }
};
uploadList.getActiveUpload = function() {
  for (var key in uploadList.uploadQueue) {
    if (uploadList.uploadQueue[key].isActive()) {
      return key;
    }
  }
  global.log.info("no active upload");
  return "";
};
uploadList.startTask = function() {
  if (uploadList.uploadNum < 2 && uploadList.uploadQueueLegnth > 0) {
    var u = uploadList.getActiveUpload();
    if (u) {
      uploadList.uploadNum++;
      uploadList.uploadQueue[u].doUpload();
    }
  }
  if (uploadList.uploadQueueLegnth == 0) {
    uploadList.timeout++;
    if (uploadList.timeout == 20) {
      clearInterval(global.uploadInterval);
      delete global.uploadInterval;
    }
  } else {
    uploadList.timeout = 0;
  }
};
var downloadList = require("./downloadList.js");
var dl = new downloadList.downloadList();
downloadList.setDownloadList(dl);

var all_friends = [];
////////////
function main() {
  var settings = require("./settings");
  var res_api = require('./res/res_api');
  var res_main = require("./res/res_main");
  var res_util = require('./res/utils');
  var webUtils = require("./webUtil");
  var cipher = require('./fbtUtils/encrypt.js');
  var upyunToken = require('./fbtUtils/upyun.js');
  var webUtil = webUtils.webUtil;
  var request = webUtils.request;
  var fileChangeCallback = webUtils.fileChangeCallback;
  var sets = require("./setting/fbtSetting.js");
  var ejs = require(path_s.join(global.exec_path, "ejs"));
  var fileUploadV4;
  var mime = require(path_s.join(global.exec_path, 'mime-types'));

  global.main_data = {
    "msg": "",
    "count": 0,
    "user": ""
  };
  global.isV4 = false;
  var loadBase64Image = function(url, callback) {
    // Make request to our image url
    request(url, {}, function(err, body, res) {
      //global.log.info(res);
      if (!err && res.statusCode == 200) {
        // So as encoding set to null then request body became Buffer object
        var base64prefix = 'data:' + res.headers['content-type'] + ';base64,',
          image = body.toString('base64');
        if (typeof callback == 'function') {
          callback(image, base64prefix);
        }
      } else {
        if (err)
          global.log.info(err.stack);
        else
          global.log.info(res.statusCode);
        callback("", "");
      }
    });
  };
  global.upload_img = {};

  function getResourceType(mainType, subType) {
    var resourceMainType = {
      0: "电影",
      1: "剧集",
      2: "学习",
      3: "音乐",
      4: "动漫",
      5: "游戏",
      6: "综艺",
      7: "体育",
      8: "软件",
      9: "其他"
    };
    var resourceSubType = {
      0: "标清",
      1: "高清",
      2: "超高清"
    };
    var type = [0, 1, 3, 4, 6, 7];
    if ((mainType in type) && (subType >= 0 && subType <= 2)) {
      return resourceMainType[mainType] + " " + resourceSubType[subType];
    } else {
      return resourceMainType[mainType];
    }
  }

  function checkTime(i) {
    if (i < 10)
      i = "0" + i;
    return i;
  }

  function toLocalTime(utcSeconds) {
      //var utcSeconds = 1234567890;
      var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
      if (!utcSeconds) {
        return "未知时间";
      }
      d.setUTCSeconds(parseInt(utcSeconds));
      var month = checkTime(d.getMonth() + 1); //Months are zero based
      var year = d.getFullYear();
      var day = checkTime(d.getDate());
      var hour = checkTime(d.getHours());
      var minute = checkTime(d.getMinutes());
      var second = d.getSeconds();
      return year + "-" + month + "-" + day + " " + hour + ":" + minute;
    }
    //upload
  function upload(active, type, docPath, upload_id, dirName, name, p, callback) {
    this.name = name;
    this.dirName = dirName;
    this.storeToDb = 0;
    this.p = p;
    this.upload_id = upload_id;
    this.docPath = docPath;
    this.type = type;
    this.active = active;
    this.totalFile = 0;
    this.totalFileTemp = 0;
    if (callback)
      this.callback = callback;
  }
  upload.prototype.isActive = function() {
    return this.active;
  };
  upload.prototype.setTotalFile = function(num) {
    this.totalFile = num;
    this.totalFileTemp = num;
  };
  upload.prototype.clear = function() {
    delete this.name;
    delete this.dirName;
    delete this.storeToDb;
    delete this.p;
    delete this.upload_id;
    delete this.docPath;
    delete this.type;
    delete this.active;
    delete this.totalFile;
    delete this.totalFileTemp;
    if (this.callback)
      delete this.callback;
  };
  upload.prototype.setData = function(doc, size, storeToDb, upload_id) {
    var that = uploadList.getUpload(upload_id);
    if (that) {
      var name = path_s.basename(utils.fbtNormalize(doc["path"]));
      global.log.info(name + "upload callback");
      that.p["hash"] = doc["verify"];
      that.p["fileSize"] = size;
      that.p["name"] = cipher.encrypt(name);
      if(global.isV4){
        that.p["isV4"] = "1";
      }
      else{
        that.p["isV4"] = "0";
      }
      that.name = name;
      that.docPath = doc["path"];
      that.storeToDb = storeToDb;
      uploadList.hashToPath[doc["verify"] + ""] = upload_id;
      that.active = true;
    } else {
      global.log.info("upload error" + upload_id);
    }
  };
  upload.prototype.doUpload = function() {
    global.log.info(this.name, " upload start");
    this.active = false;
    if (this.type == 0) {
      global.socket.emit('s_upload', JSON.stringify(this.p));
    } else {
      var params = {};
      this.p["cookie"] = global.cookie;
      if(global.isV4){
        this.p["isV4"] = "1";
      }
      else{
        this.p["isV4"] = "0";
      }
      params["headers"] = {
        "Cookie": JSON.stringify(global.cookie),
        "X-Requested-With": "XMLHttpRequest"
      };
      params["data"] = this.p;
      params["method"] = "POST";
      params["timeout"] = 30000;
      var that = this;
      var url = settings.url + "res/upload/file";
      if(this.callback){
        url = settings.url + "res/upload/dir";
      }
      //global.log.info(params);
      request(url, params, function(err, data) {
        global.log.info(that.name + "upload finish");
        uploadList.delOrStart();
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        if (result && "type" in result && result["type"] == 1) {
          global.res_list.push(that.docPath);
          global.socket.emit("upload", JSON.stringify({
            "id": that.upload_id,
            "type": 3,
            "progress": "100%"
          }));
          var succMsg = "上传成功，仅对好友可见，感谢您的分享！";
          if (params['data']["isPublic"] == 1) {
              succMsg = "上传成功，等待审核，感谢您的分享！审核结果将显示在右上角的通知栏。";
          }
          global.socket.emit("upload", JSON.stringify({
            "id": that.upload_id,
            "type": 1,
            "msg": "《" + that.name + "》" + succMsg
          }));
          if (that.callback)
            that.callback();
          else
            res_util.store_res_info(that.docPath, global.monitors);
        } else
          global.socket.emit("upload", JSON.stringify({
            "id": that.upload_id,
            "error": that.name + "上传失败",
            "type": 1
          }));
        uploadList.delUpload(that.upload_id);
      });
    }
  };
  upload.prototype.uploadCallback = function(data) {
    global.log.info(data + "upload finish");
    uploadList.delOrStart();
    if (parseInt(data) == 0) {
      var ret = {
        "type": 0,
        "error": this.name + "上传失败",
        "id": this.upload_id
      };
      global.socket.emit("upload", JSON.stringify(ret));
    } else {
      if (this.totalFile - this.totalFileTemp == 20) {
        this.totalFile -= 20;
        setTimeout(this.storeToDb(this.upload_id), 20000);
      } else
        this.storeToDb(this.upload_id);
      global.res_list.push(this.docPath);
    }
    this.totalFileTemp--;
    if (this.totalFileTemp == 0) {
      var ret = {
        "type": 1,
        "msg": this.dirName + "上传完成"
      };
      global.socket.emit("upload", JSON.stringify(ret));
      uploadList.delUpload(this.upload_id);
    }
  };
  /*download*/
  var uploadOwner = function(fileHash, usersDownloadFrom, fileName, fileSize, dirHash, dirSize) {
    global.log.info("uploadOwner");
    var fileId = utils.gen_file_id(fileHash, fileSize);
    var d = {};
    d['user'] = global.uid;
    d['file_hash'] = fileHash;
    d["file_name"] = fileName;
    d["file_size"] = fileSize;
    d["cookie"] = global.cookie;
    d["downloadFrom"] = usersDownloadFrom;
    if (dirHash) {
      d["dirHash"] = dirHash;
      d["dirSize"] = dirSize;
      fileId = utils.gen_file_id(dirHash, dirSize);
    } else {
      d["dirHash"] = "";
      d["dirSize"] = "";
    }
    if(fileId in global.reward)
      d['rid'] = global.reward[fileId];
    //global.log.info(usersDownloadFrom);
    var params = {};
    params["headers"] = {
      "Cookie": JSON.stringify(global.cookie),
      "X-Requested-With": "XMLHttpRequest"
    };
    params["data"] = d;
    params["method"] = "GET";
    params["timeout"] = 30000;
    global.log.info("add owner");
    //global.log.info(JSON.stringify(params));
    request(settings.url + "download_over", params, function(err, data) {
      if (err != null) {
        global.log.info(err.stack + "\n");
        global.socket.emit("net");
        return;
      } else {
        var json;
        try {
          json = JSON.parse(data);
        } catch (e) {
          global.log.info("uploadOwner, json err");
          json = data;
        }
        global.log.info(json);
        if (json && json['type'] == 1) {
          //{"owners": [], "file_info": {"file_hash": "714371632", "file_name": "README.txt", "file_size": "3906"}, "err": 0}
          global.log.info("add an owner ok file hash:" + fileHash + " owner:" + uid);
        } else {
          global.log.info("add owner json err:" + json);
        }
      }
    });
  };
  var fileDownload;

  function downloadFileCallback(err, fileDownloadInfo, shouldMove, dirHash, dirSize, that) {
    global.log.info("fileDownloadInfo");
    if (err) {
      var noFBCoin = 1;
      if (err == noFBCoin) {
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "F币不足，无法下载！"
        }));
      } else {
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "获取下载信息失败"
        }));
        that && that.getNext(false);
        return;
      }
      return;
    }
    //global.window.console.log("download file");
    var dirId = utils.gen_file_id(dirHash, dirSize);
    var html = fileDownloadInfo["html"];
    //var preSpeed = 0;
    //var p_preSpeed = 0;
    var pre_progress = 0;
    var hash = fileDownloadInfo["hash"];
    var isPrivateDownload = fileDownloadInfo["private"];
    //------------------------------------------------------//
    //FROM SERVER
    var remoteFile = fileDownloadInfo["file_name"];
    var fileSize = fileDownloadInfo["file_size"];
    var fileHash = fileDownloadInfo["file_hash"];
    var fileInfo = {
      file: remoteFile,
      size: fileSize,
      hash: fileHash
    };
    var fileOwners = fileDownloadInfo["owners"];
    var downloadType = fileDownloadInfo["download_type"]; //
    //global.log.info("downloadType:"+downloadType);
    var fileDownloadTypes = {
      "None": 0,
      "V4_LAN": 1,
      "V4_NAT": 2,
      "V6": 3, 
      "V4_NOT_ALLOW": 4
    };
    //------------------------------------------------------//
    var unit = ["B", "KB", "MB", "GB"];
    var divide = [1, 1024, 1024 * 1024, 1024 * 1024 * 1024];
    var fix = [0, 0, 1, 2];
    var curUnit = 0;
    for (var i = 3; i >= 0; i--) {
      if (fileSize > divide[i]) {
        curUnit = i;
        break;
      }
    }
    var fileSizeMB = (fileSize / divide[curUnit]).toFixed(fix[curUnit]);

    var t_hash = hash + "";
    if (!(t_hash in global.historys)) {
      /*if (shouldMove)
        global.socket.emit('download_start', html);*/
      if (dirHash){
        var rid = '';
        if(dirId in global.reward){
          rid = global.reward[dirId];
        }
        global.historys[t_hash] = {
          "dirName": that.dirName,
          "private": isPrivateDownload,
          "size": fileSize,
          "dirHash": dirHash,
          "dirSize": dirSize,
          "download": 0,
          "name": remoteFile,
          "time": (new Date()).getTime(),
          "fileHash": t_hash,
          "progress": 0,
          "block": 0,
          "fileSize": fileSizeMB + unit[curUnit],
          'rid': rid,
          'fid': dirId
        };
      }
      else{
        var rid = '';
        var fileId = utils.gen_file_id(fileHash, fileSize);
        if(fileId in global.reward){
          rid = global.reward[fileId];
        }
        global.historys[t_hash] = {
          "private": isPrivateDownload,
          "size": fileSize,
          "download": 0,
          "name": remoteFile,
          "time": (new Date()).getTime(),
          "fileHash": t_hash,
          "progress": 0,
          "block": 0,
          "fileSize": fileSizeMB + unit[curUnit],
          "rid": rid,
          "fid": fileId
        };
      }
      global.log.info("save download start");
      sets.saveHistory();
    }

    if (fileOwners.length == 0 || downloadType == fileDownloadTypes["None"]) {
      global.socket.emit('download', JSON.stringify({
        "type": 1,
        "html": html,
        "error": "暂时无有效在线用户"
      }));
      that && that.getNext(false);
      return;
    }
    else if(downloadType == fileDownloadTypes["V4_NOT_ALLOW"]){
      global.socket.emit('download', JSON.stringify({
        "type": 1,
        "html": html,
        "error": "该资源下载需要到设置里启用V4下载"
      }));
      //global.socket.emit('inform_sticky', "该资源下载需要到设置里启用V4下载");
      return;
    }
    //TODO
    //FIXME
    //var saveDir=require('path').join(__dirname,'downloads');
    //var saveDir='F:/node-webkit-bin/my-sample/downloads';
    //MUST SET THIS
    var saveDir = null; //'D:/';//default to save to D:/
    //global.log.info(global.setting);
    if ("downloadSaveDir" in global.setting) {
      saveDir = global.setting["downloadSaveDir"];
      if (dirHash) {
        saveDir = path_s.join(saveDir, that.dirName);
      }
    } else {
      global.socket.emit('download', JSON.stringify({
        "type": 1,
        "html": html,
        "error": "无效下载目录，请设置"
      }));
      return;
    }
    var downloadOverCallback = function(err, savedPostion, fileHash, fileSize, usersDownloadFrom) {
      global.log.info("downloadOverCallback");
      /*if (err && err != settings.errTips["historyDownload"] && err != settings.errTips["argument_err"] && that) {
        that.getNext(true);
      }*/
      if (err == settings.errTips["remove"]) {
        if (global.historys[hash + ""]) {
          delete global.historys[hash + ""];
          global.log.info("save download remove");
          sets.saveHistory();
          global.socket.emit("his_del", JSON.stringify({
            "html": html
          }));
        }
        that && that.getNext(false);
        return;
      } else if (err == settings.errTips["spaceFull"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": fileSizeMB + unit[curUnit] + "  磁盘空间不足"
        }));
        that && that.getNext(true);
        return;
      } else if (err == settings.errTips["invalidOwners"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html,
          "invalid": 1
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "对方网络出现故障，暂时无法下载，请稍后重试"
        }));
        that && that.getNext(false);
        return;
      } else if (err == settings.errTips["v4_not_provided"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "很抱歉，暂时不支持您所用系统下的ipv4下载"
        }));
        that && that.getNext(true);
        return;
      } else if (err == settings.errTips["v4_not_allowed"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "很抱歉，您设置了不允许ipv4下载，可到设置里更改"
        }));
        that && that.getNext(true);
        return;
      } else if (err == settings.errTips["xp_v4"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "很抱歉，暂时不支持xp系统下的ipv4下载"
        }));
        that && that.getNext(true);
        return;
      } else if (err == settings.errTips["download_dir_create_failed"]) {
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "当前下载目录不存在，请到设置里更改"
        }));
        that && that.getNext(true);
        return;
      } else if (err && err != settings.errTips["historyDownload"] && err != settings.errTips["argument_err"]) {
        global.log.info("err in file download:" + err); //TODO FIXME
        global.socket.emit("download_over", JSON.stringify({
          "dirId":that.dirId,
          "html": html
        }));
        global.socket.emit('download', JSON.stringify({
          "type": 1,
          "html": html,
          "error": "网络不可用，暂时无法下载，请稍后重试"
        }));
        that && that.getNext(false);
        return;
      } else {
        global.log.info("send downloadOverCallback");
        var tmp = hash + "";
        var dirFlag = "dirHash" in global.historys[tmp];
        if(err == settings.errTips["argument_err"]){
          if (!dirFlag) {
            global.socket.emit("download_over", JSON.stringify({
              "dirId":that.dirId,
              "html": html
            }));
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": html,
              "error": "文件信息可能损坏了，请重试"
            }));
          }
          that && that.getNext(false);
          return;
        }
        if (tmp in global.historys) {
          //global.historys[tmp]["download"] = 0;
          global.historys[tmp]["progress"] = 100;
          global.log.info("saveHistory in downloadOverCallback(else)");
          sets.saveHistory();
        }
        if (dirFlag) {
          var dir_id = utils.gen_file_id(global.historys[tmp]["dirHash"], global.historys[tmp]["dirSize"]);
          global.dir[dir_id]["complete"] ++;
          sets.saveDir();
          global.socket.emit("single_download_over", JSON.stringify({
            "fileId": utils.gen_file_id(fileHash, fileSize),
            "dirId": dirId,
            "html": html
          }));
        } else {
          global.socket.emit('download', JSON.stringify({
            "type": 2,
            "html": html,
            "progress": 100,
            "value": fileSizeMB + unit[curUnit] + "  已完成"
          }));
          global.socket.emit("download_over", JSON.stringify({
            "dirId": dirId,
            "html": html,
            "name": remoteFile
          }));
          /*global.socket.emit('download', JSON.stringify({
            "type": 2,
            "html": '#download_progress_bar' + html,
            "actions": [3, 4],
            "value": [{
              'width': 100 + '%'
            }, {
              'aria-valuenow': 100
            }]
          }));*/
          /*global.socket.emit('download', JSON.stringify({
            "type": 2,
            "html": '#text_messages_num',
            "actions": [1],
            "value": ""
          }));*/
        }
        //alert("file download success. save to "+savedPostion);
        //TODO FIXME
        //add resource to DB
        global.log.info("add res to db");
        var isDir = false;
        if(dirHash)
          isDir = true;
        if(err == settings.errTips["historyDownload"]){
          if (that) {
            that.getNext(false);
          }
          return;
        }
        if (that) {
          that.getNext(false);
        }
        res_api.insertResource(hash, savedPostion, function(downloadSucceed) {
          if (downloadSucceed) {
            //资源下载完毕上传供水者到服务器
            global.res_list.push(utils.fbtNormalize(savedPostion));
            uploadOwner(hash, usersDownloadFrom, remoteFile, fileSize, dirHash, dirSize);
            //upload owners
          } else {
            fs.unlink(savedPostion, function() {});
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": html,
              "error": "下载出现问题,请重新下载"
            }));
          }
        }, isDir);
      }
    };
    var downloadProgressCallback = function(downloadedBytes, progress, downloadSpeed) {
      var downloadedBlocks = (downloadedBytes / divide[curUnit]).toFixed(fix[curUnit]);
      downloadSpeed = downloadSpeed / 1024;
      if (downloadSpeed > 100) {
        downloadSpeed = downloadSpeed / 1024;
        if (downloadSpeed > 50)
          downloadSpeed = 50;
        /*downloadSpeed = p_preSpeed * 0.2 + preSpeed * 0.3 + downloadSpeed * 0.5;
        p_preSpeed = preSpeed;
        preSpeed = downloadSpeed;*/
        downloadSpeed = downloadSpeed.toFixed(1) + "M/s";
      } else {
        /*p_preSpeed = preSpeed;
        preSpeed = downloadSpeed / 1024;*/
        downloadSpeed = downloadSpeed.toFixed(0) + "K/s";
      }
      var progressVal = (progress * 100).toFixed(2);
      var dirProgressVal = 0;
      var tmp = hash + "";
      if (tmp in global.historys) {
        global.historys[tmp]["progress"] = progressVal;
        global.historys[tmp]["block"] = downloadedBlocks;
        if (global.historys[tmp]["download"] == 0) {
          global.historys[tmp]["download"] = 1;
          pre_progress = progressVal;
          global.log.info("save progress first");
          sets.saveHistory();
        }
        else if(progressVal - pre_progress >= 10){ 
          pre_progress = progressVal;
          global.log.info("save progress");
          sets.saveHistory();
        }
        //sets.saveHistory();
        //global.window.console.log(tmp);
        //global.window.console.log(global.historys[tmp]);
        if ("dirHash" in global.historys[tmp]) {
          //global.window.console.log("dir");
          var dir_id = utils.gen_file_id(global.historys[tmp]["dirHash"], global.historys[tmp]["dirSize"]);
          var folderSize = parseInt(dl.getFolderSize(dir_id));
          if(folderSize){
            var p = (parseInt(global.dir[dir_id]["complete"]) / folderSize)*100;
            dirProgressVal = (progressVal/folderSize + p).toFixed(2);
            global.socket.emit("single_download_progress", JSON.stringify({
              "progress": progressVal,
              "fileId": utils.gen_file_id(fileHash, fileSize),
              "dirId": dirId
            }));
            global.socket.emit('download', JSON.stringify({
              "type": 2,
              "html": html,
              "progress": dirProgressVal,
              "value": fileSizeMB + unit[curUnit] + "  " + dirProgressVal + "% " + downloadSpeed
            }));
            /*global.socket.emit('download', JSON.stringify({
              "type": 2,
              "html": '#download_progress_bar' + html,
              "actions": [3, 4],
              "value": [{
                'width': dirProgressVal + '%'
              }, {
                'aria-valuenow': dirProgressVal
              }]
            }));*/
          }
        } else {
          global.socket.emit('download', JSON.stringify({
            "type": 2,
            "html": html,
            "progress": progressVal,
            "value": fileSizeMB + unit[curUnit] + "  " + progressVal + "% " + downloadSpeed
          }));
          /*global.socket.emit('download', JSON.stringify({
            "type": 2,
            "html": '#download_progress_bar' + html,
            "actions": [3, 4],
            "value": [{
              'width': progressVal + '%'
            }, {
              'aria-valuenow': progressVal
            }]
          }));*/
        }
      }
    };
    var downloadQueueAddedCallback = function(err, fileName) {
      /*  if(err){
          global.socket.emit('download', JSON.stringify({"type":1, "html":html,"error":"无需重复下载"}));
        }*/
    };
    if (shouldMove)
      global.socket.emit('download_start', html);
    fileDownload.addToDownloadQueue(global.uid, fileInfo, fileOwners, downloadType, saveDir, downloadOverCallback, downloadProgressCallback, downloadQueueAddedCallback);
  }

  function pauseFileDownload(fileHash, size) {
    //var fileHash = '0';
    fileDownload.pauseFileDownload(fileHash, size);
  }

  function resumeFileDownload(fileHash, size) {
    //$('#download_progress').html("恢复下载中");
    //var fileHash = '0';
    fileDownload.resumeFileDownload(fileHash, size);
  }

  function cancelFileDownload(whichHtmlElement, fileHash, size, dirHash, dirSize) {
    //var fileHash = '0';
    //global.window.console.log(dirHash);
    global.log.info("cancelFileDownload");
    var isDir = false;
    if(dirHash)
      isDir = true;
    fileDownload.removeFileDownloadFromQueue(isDir, size, fileHash,
      function(err) {
        global.log.info("cancelFileDownload callback");
        var tmp = fileHash + "";
        if (!err) {
          if (tmp in global.historys) {
            delete global.historys[tmp];
            sets.saveHistory();
            global.log.info("save download cancel");
          }
          if (dirHash) {
            //global.window.console.log("dirHash");
            dl.delDirDownload(dirHash, dirSize);
            for(var item in global.historys){
              if("dirHash" in global.historys[item] && global.historys[item]["dirHash"] == dirHash){
                delete global.historys[item]
              }
            }
            sets.saveHistory();
            global.log.info("save download cancel dir"); 
            /*global.socket.emit('download', JSON.stringify({
              "type": 6,
              "html": whichHtmlElement,
              "error": 0,
              "hash": dirHash,
              "size": dirSize
            }));*/
          } else {
            /*global.socket.emit('download', JSON.stringify({
              "type": 6,
              "html": whichHtmlElement,
              "error": 0,
              "hash": fileHash,
              "size": size
            }));*/
            dl.delFileDownload(fileHash, size);
          }
        } else {
          global.log.info(err);
          /*if (dirHash) {
            global.socket.emit('download', JSON.stringify({
              "type": 6,
              "html": whichHtmlElement,
              "error": 1,
              "hash": dirHash,
              "size": dirSize
            }));
          } else {
            global.socket.emit('download', JSON.stringify({
              "type": 6,
              "html": whichHtmlElement,
              "error": 1,
              "hash": fileHash,
              "size": size
            }));
          }*/
        }
      }
    );
  }

  function isOSWin64() {
    return process.arch === 'x64' || process.env.hasOwnProperty('PROCESSOR_ARCHITEW6432');
  }

  function initWin(){
    process.mainModule.exports.winResize(1140, 640);
    process.mainModule.exports.winMoveTo(100, 20);
  }

  function checkUpdate() {
    fs.readFile(path_s.join(__dirname, "package.json"), function read(err, data) {
      if (err) {
        global.log.info("can't update");
      } else {
        var version = (JSON.parse(data))["version-code"];
        var arch = 32;
        if (isOSWin64())
          arch = 64;
        var w = require('os').release()[0];
        var tmp = {
          "v": version,
          "platform": process.platform,
          "arch": arch,
          "type": w
        };
        var params = {};
        params["data"] = tmp;
        params["method"] = "GET";
        //global.window.console.log("check update");
        request(settings.url+"check_update", params, function(err, data){
          if(err){
            global.log.info(err.stack+"\n");
            global.socket.emit("net");
            return;
          }
          var tmp;
          try {
            tmp = JSON.parse(data);
          } catch (e) {
            tmp = data;
          }
          if (tmp && tmp["type"] == 1 && tmp["path"] && tmp["name"]){
            //global.window.console.log("find update");
            global.socket.emit('inform', "发现新版本，开始下载");
            utils.download_app(settings.upyun_files,
              tmp["path"], tmp["name"], global.setting["downloadSaveDir"]);
          }
        });
      }
    });
  }

  function reportError() {
    var e = path_s.join(global.fbt, 'error.txt');
    var log = path_s.join(global.fbt, 'fbt.log');
    fs.exists(e, function(exists) {
      if (exists) {
        var data = (fs.readFileSync(e, 'utf-8')).toString();
        var data_log = (fs.readFileSync(log, 'utf-8')).toString();
        var tmp = {
          "error": data,
          "log": data_log
        };
        var params = {};
        params["data"] = tmp;
        params["method"] = "POST";
        request(settings.url + "report", params, function(err, data) {
          if (err) {
            global.log.info(err.stack + "\n");
            global.socket.emit("net");
            return;
          }
          fs.unlinkSync(e);
        });
      }
    });
  }

  function getDoubanInfo(data){
    doubanUtil.getInfo(data, function get(info) {
      if (info) {
        loadBase64Image(info["ilink"], function(image, prefix) {
          info["img"] = image;
          info["link"] = prefix + image;
          global.socket.emit("douban", JSON.stringify(info));
        });
      } else
        global.socket.emit("douban", "");
    });
  }

  function openDir(filepath){
    path_s.exists(filepath, function(exist) {
      if (exist) {
        try {
          process.mainModule.exports.open_dir(filepath);
        } catch (e) {
          var commands = {
            'win32': "explorer \"",
            'linux': "nautilus \"",
            'darwin': "open \""
          };
          if (commands[process.platform])
            child_process.exec(commands[process.platform] + global.setting["downloadSaveDir"] + "\"");
        }
      } else {
        var commands = {
          'win32': "explorer \"",
          'linux': "nautilus \"",
          'darwin': "open \""
        };
        if (commands[process.platform])
          child_process.exec(commands[process.platform] + global.setting["downloadSaveDir"] + "\"");
      }
    });
  }

  function init() {
    var express = require(path_s.join(global.exec_path, "express"));
    var app = express();
    var http = require('http').Server(app);
    var io = require(path_s.join(global.exec_path, 'socket.io'))(http);
    app.use(express.static(__dirname + '/static'));
    app.set("views", __dirname + "/views/");
    app.set("view engine", "jade");
    app.set("view options", {
      layout: false
    });

    function error(err, req, res, next) {
      msg = {};
      msg["type"] = 0;
      msg["error"] = err.message || err.stack;
      msg = JSON.stringify(msg);
      global.log.info(msg);
      res.writeHead(500);
      res.end("很抱歉，软件运行过程中出现了未知的错误，请重启。");
    }
    app.use(express.bodyParser());
    app.use(express.cookieParser());
    //app.use(express.session());
    app.use(express.logger());
    app.use(error);
    app.enable('view cache');
    app.get("/getdouban", function(req, res){
      getDoubanInfo(req.query.douban);
    });
    app.get("/beingDownloadedFiles", function(req, res) {
        var files = httpServer.getDownloadingFiles();
        res.end(JSON.stringify(files));
    });
    app.get("/error", function(req, res) {
      res.render("error");
    });
    app.get("/index", function(req, res){
      reportError();
      var html = fs.readFileSync("views/index.html", "utf-8");
      res.end(html);
    });
    /*app.get("/login", function(req, res) {
      //global.log.info(req);
      
      var auto = 1;
      if("shouldReconnect" in req.query){
        auto = 0;
      }
      
      var html = fs.readFileSync("static/partials/login.html", "utf-8");
      res.end(html);
    });*/
    app.get("/ipv6", function(req, res) {
      //res.render("ipv6");
      webUtil(req, res, "GET", settings.origin + ":80/tv", function(data) {
        res.end(data);
      });
    });
    app.get("/fmall", function(req, res) {
      //res.render("ipv6");
      webUtil(req, res, "GET", "http://www.friendsbt.com/fmall", function(data) {
        res.end(data);
      });
    });
    app.get("/fb", function(req, res) {
      res.render("fb");
    });
    /*///////for reward test
    app.get("/home", function(req, res) {
      var html = fs.readFileSync("YYYUI/index.html", "utf-8");
      res.end(html);
    });
    app.get("/statics/*", function(req, res) {
      var reqUrl = req.originalUrl;
      var path = "YYYUI/static" + reqUrl.replace("/statics", "");      
      if(reqUrl.indexOf("/img/") != -1){
        res.sendfile(path);
        return;
      }
      var html = fs.readFileSync(path, "utf-8");
      res.end(html);
    });
    ////////for reward test
    app.get("/registration", function(req, res) {
      res.render("registration");
    });*/
    app.get("/friend_res", function(req, res) {
      //res.render("friendRes", data=global.main_data, uid=req.query.uid);
      var isPublic = req.query.public;
      var isPrivateDownload;
      if(!isPublic)
        isPrivateDownload = 1;
      else
        isPrivateDownload = 0;
      var url = settings.url + "myFriend?uid=" + req.query.uid;
      global.log.info("res url " + url);
      webUtil(req, res, "GET", url, function(data) {
        //global.window.console.log("res: "+data.toString());
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        res.header("Content-Type", "application/json");
        res.end(JSON.stringify(result["result"]));
        /*if (!result) {
          res.end("<center><h3>列表资源为空！</h3></center>");
          return;
        }
        res.render('friendRes', {
          isPrivateDownload: isPrivateDownload,
          uid: req.query.uid,
          result: result["result"]
        }, function(err, html) {
          if (err) {
            global.log.info(err.stack + "\n");
            //global.socket.emit("net");
            res.end("nul");
            return;
          } else {
            res.end(html);
          }
        });*/
      });
    });
    app.get("/myInfo", function(req, res) {
      webUtil(req, res, "GET", settings.url + "myInfo", function(data) {
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        /*if (!result) {
          res.end("<center><h3>列表资源为空！</h3></center>");
          return;
        }*/
        if("user" in result["result"] && "icon" in result["result"]["user"]){
          result["result"]["user"]["icon"] = result["result"]["user"]["icon"].split("?")[0];
        }
        //test for angular
        res.header("Content-Type", "application/json");
        res.end(JSON.stringify(result["result"]));
        /*res.render("myInfo", {
          result: result["result"]
        }, function(err, html) {
          if (err) {
            global.log.info(err.stack + "\n");
            //global.socket.emit("net");
            res.end("nul");
          } else {
            res.end(html);
          }
        });*/
      });
    });
    app.get("/mySpace", function(req, res) {
      webUtil(req, res, "GET", settings.url + "mySpace", function(data) {
        //global.window.console.log(data);
        //global.window.console.log(data.toString());
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        if (!result) {
          //res.end("<center><h3>列表资源为空！</h3></center>");
          return;
        }
        global.log.info("space finish");
        if("icon" in result["result"]){
          result["result"]["icon"] = result["result"]["icon"].split("?")[0];
        }
        var friends = result["result"]["friends"];
        for (var i = 0; i < friends.length; i++) {
          all_friends.push(parseInt(friends[i]["uid"]));
        }
        //test for angular
        res.header("Content-Type", "application/json");
        res.end(JSON.stringify(result["result"]));
        /*res.render("mySpace", {
          result: result["result"]
        }, function(err, html) {
          if (err) {
            global.log.info(err.stack + "\n");
            //global.socket.emit("net");
            res.end("nul");
            return;
          } else {
            res.end(html);
          }
        });*/
      });
    });
    app.get("/fbrank", function(req, res) {
      //global.log.info(req.originalUrl)
      webUtil(req, res, "GET", settings.url + "fbrank", function(data) {
        //global.log.info(data);
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        res.end(JSON.stringify(result));
      });
    });
    app.get("/coin", function(req, res) {
      res.render("coin");
    });
    app.get("/setting/:do", function(req, res) {
      if (req.params.do == "init") {
        global.setting["platform"] = process.platform;
        global.setting["version"] = parseInt(process.versions['node-webkit'].split('.')[1]);
        res.end(JSON.stringify(global.setting));
      } else if (req.params.do == "save") {
        var path = req.query["path"];
        global.setting["boot"] = req.query["boot"];
        global.setting["tray"] = req.query["tray"];
        global.setting["auto_log"] = req.query["auto_log"];
        global.setting["allow_v4_download"] = req.query["allow_v4_download"];
        global.setting["allow_bg"] = req.query["allow_bg"];
        global.setting["voice"] = req.query["voice"];
        global.setting["chat_robot"] = req.query["chat_robot"];
        global.setting["friends_online_inform"] = req.query["friends_online_inform"];
        var speed = window.parseInt(req.query["upload_speed"]);
        if (speed > 20)
          speed = 20;
        global.setting["upload_speed"] = (speed * 1024 * 1024).toFixed(0);
        if (path.length > 0 && fs.existsSync(path)) {
          global.setting["downloadSaveDir"] = path;
          global.log.info("setting");
          global.log.info(global.setting);
          //sets.saveSetting();
          res.end(JSON.stringify({
            "type": 1
          }));
        } else {
          res.end(JSON.stringify({
            "type": 0
          }));
        }
        sets.startOnBoot(req.query["boot"]);
        if (parseInt(req.query["boot"]) == 1) {
          global.setting["auto_log"] = 1;
          //global.setting["tray"] = 1;
        }
        sets.saveSetting();
      }
    });
    app.post("/getDirDetail", function(req, res) {
      //global.window.console.log("getDirDetail");
      webUtil(req, res, "POST", settings.url + "getDir", function(data) {
        //global.window.console.log(data.toString());
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        res.end(JSON.stringify(result));
      });
    });
    app.post("/getFileName", function(req, res) {
      webUtil(req, res, "POST", settings.url + "getFileName", function(data) {
        var json;
        try {
          json = JSON.parse(data);
        } catch (e) {
          json = data;
          //json = $.parseJSON(data);
        }
        //global.log.info(json["type"]+"test");
        if (json && 'type' in json && json["type"] == 1) {
          res.end(JSON.stringify(json));
        } else {
          res.end(JSON.stringify({
            "type": 0
          }));
        }
      });
    });
    //0 is add, 1 is del, 2 is clear, 3 is init res, 4 is get res list, 5 is comment, 6 is score,
    //7 is search,8 is friend
    app.post("/res", function(req, res) {
      var p = req.body || req.query;
      var d = parseInt(p["op"]);
      var upload_id = (new Date()).getTime() + "";
      if (d == 0) {
        res.end(JSON.stringify({
          type: 1
        }));
        fs.exists(p["path"], function(exists) {
          if (exists) {
            var stats;
            try {
              stats = fs.statSync(p["path"]);
            } catch (e) {
              global.log.info("state error");
              global.log.info(e);
              var ret = {
                "type": 0,
                "error": "文件状态存在问题，请检查",
                "id": upload_id
              };
              global.socket.emit("upload", JSON.stringify(ret));
              return;
            }
            /*if("ext_info" in p){
                p["ext_info"]["img"] = global.upload_img[p["ext_info"]["id"]];
                delete global.upload_img[p["ext_info"]["id"]];
                p["ext_info"] = JSON.stringify(p["ext_info"]);
                global.log.info(p);
              }*/
            //global.log.info(p);
            //p["isDir"] = 0;
            if ("isDir" in p && (p["isDir"] == 1 || p["isDir"] == '1')) {
              //upload dir
              /*if (utils.find(global.res_list, utils.fbtNormalize(p["path"])) != -1) {
                var ret = {
                  "type": 1,
                  "error": "请不要重复上传",
                  "id": upload_id
                };
                global.socket.emit("upload", JSON.stringify(ret));
                return;
              }*/
              var name = path_s.basename(utils.fbtNormalize(p["name"]));
              global.socket.emit("upload", JSON.stringify({
                "id": upload_id,
                "type": 2,
                "name": name,
                "size": 1
              }));
              //global.window.console.log("upload dir");
              res_api.dirUpload(p["path"], upload_id, function(err, uploadFileInfo, userDirId, callback) {
                //global.window.console.log("upload dir call back");
                if (err)
                  global.log.info(err);
                if (err == 'exceed_limit') {
                  var ret = {
                    "type": 1,
                    "error": "文件数量多于500，请检查文件目录选择是否正确",
                    "id": upload_id
                  };
                  global.socket.emit("upload", JSON.stringify(ret));
                  return;
                } else if (err) {
                  var ret = {
                    "type": 1,
                    "error": "很抱歉，上传过程中出现了错误，请重试",
                    "id": upload_id
                  };
                  global.socket.emit("upload", JSON.stringify(ret));
                  return;
                }
                else if(uploadFileInfo.length === 0){
                  global.socket.emit("upload", JSON.stringify({
                    "id": upload_id,
                    "type": 3,
                    "progress": 100
                  }));
                  global.socket.emit("upload", JSON.stringify({
                    "id": upload_id,
                    "type": 1,
                    "msg": "急速秒传"
                  }));
                  return;
                }
                p["op"] = 8;
                p["fileInfo"] = JSON.stringify(uploadFileInfo);
                p["name"] = cipher.encrypt(name);
                p["desc"] = cipher.encrypt(p["desc"]);
                p["label"] = cipher.encrypt(p["label"]);
                p["userDirId"] = userDirId;
                var u = new upload(true, 1, p["path"], upload_id, "", name, p, callback);
                //global.log.info(u);
                uploadList.addOrStart(u, upload_id);
              });
            } else {
              if (stats.isDirectory()) {
                p["desc"] = cipher.encrypt(p["desc"]);
                p["label"] = cipher.encrypt(p["label"]);
                var dirName = path_s.basename(utils.fbtNormalize(p["name"]));
                var u = new upload(false, 0, "", upload_id, dirName, "", p);
                uploadList.addOrStart(u, upload_id);
                res_api.batchUpload(p["path"], uploadList.getUpload(upload_id).setData, function(hasError, totalFile) {
                  if (hasError) {
                    var ret = {
                      "type": 1,
                      "error": "文件数量多于500，请检查文件目录选择是否正确",
                      "id": upload_id
                    };
                    global.socket.emit("upload", JSON.stringify(ret));
                    uploadList.delUpload(upload_id);
                    return;
                  }
                  if (totalFile == 0) {
                    var ret = {
                      "type": 1,
                      "error": "请不要重复上传",
                      "id": upload_id
                    };
                    global.socket.emit("upload", JSON.stringify(ret));
                    uploadList.delUpload(upload_id);
                    return;
                  } else {
                    uploadList.getUpload(upload_id).setTotalFile(totalFile);
                    global.socket.emit("upload", JSON.stringify({
                      "id": upload_id,
                      "type": 2,
                      "name": path_s.basename(utils.fbtNormalize(p["name"])),
                      "size": totalFile
                    }));
                  }
                }, upload_id);
              } else {
                if (utils.find(global.res_list, utils.fbtNormalize(p["path"])) != -1) {
                  var ret = {
                    "type": 1,
                    "error": "请不要重复上传",
                    "id": upload_id
                  };
                  global.socket.emit("upload", JSON.stringify(ret));
                  return;
                }
                var name = path_s.basename(utils.fbtNormalize(p["name"]));
                var extension_name = "";
                if (p["path"].indexOf(".") != -1) {
                  extension_name = p["path"].split(".").pop();
                  if (name.indexOf(extension_name) === -1) {
                    // 原来的 name 中不存在扩展名, 就添加扩展名, 说明用户又填了个中文名称
                    name = name + '.' + extension_name;
                  }
                }
                global.socket.emit("upload", JSON.stringify({
                  "id": upload_id,
                  "type": 2,
                  "name": name,
                  "size": 1
                }));
                res_api.add_res_upload(p["path"], upload_id, function(doc) {
                  p["op"] = 2;
                  p["hash"] = doc["verify"];
                  p["fileSize"] = stats['size'];
                  p["name"] = cipher.encrypt(name);
                  p["desc"] = cipher.encrypt(p["desc"]);
                  p["label"] = cipher.encrypt(p["label"]);
                  var u = new upload(true, 1, doc["path"], upload_id, "", name, p);
                  uploadList.addOrStart(u, upload_id);
                });
              }
            }
          } else {
            var ret = {
              "type": 0,
              "error": "文件不存在",
              "id": upload_id
            };
            global.socket.emit("upload", JSON.stringify(ret));
          }
        });
      } else if (d == 1) {
        res_api.remove_res(p["path"]);
        var i = 0;
        var l = global.res_list.length;
        for (; i < l; i++) {
          if (global.res_list[i] == p["path"])
            break;
        }
        global.res_list.splice(i, 1);
        res.end("ok");
      } else if (d == 2) {
        res_main.clear();
        res.end("ok");
      } else if (d == 4) {
        req.query = req.body;
        var url = settings.url + "res";
        if (parseInt(req.query["sort_by"]) == 2)
          url = settings.url + "res/online";
        webUtil(req, res, "GET", url, function(data) {
          //webUtil(req, res, "POST", url, function(data){
          var json;
          try {
            json = JSON.parse(data);
          } catch (e) {
            json = data;
            //json = $.parseJSON(data);
          }
          //global.log.info(json["type"]+"test");
          if (json && 'type' in json && json["type"] == 1) {
            var result = json["result"];
            var resource_list = result["res"];
            var size = result["size"];
            utils.decrypt_resource_list(resource_list);
            var len = resource_list.length;
            //filter the history
            var num = len;
            while (num--) {
              var fileHash = resource_list[num]['file_hash'] + "";
              var isDir = false;
              if ("file_hashes" in resource_list[num])
                isDir = true;
              if (utils.isExist(fileHash, isDir)){
                /*resource_list.splice(num, 1);
                size --;*/
                resource_list[num]["downloaded"] = 1;
              }
              else{
                resource_list[num]["downloaded"] = 0;
              }
            }
            /*var path = __dirname + "/views/resourceList.ejs",
              str = fs.readFileSync(path, "utf-8");
            var ret = ejs.render(str, {
              m_uid: 0,
              isMyInfo: false,
              flag: "m",
              isHis: false,
              isPrivateDownload: 0,
              resourceList: resource_list,
              toLocalTime: toLocalTime,
              getResourceType: getResourceType
            });
            if (resource_list)
              res.end(JSON.stringify({
                "size": size,
                "len": len,
                "type": 1,
                "resource_list": resource_list,
                "html": ret,
                "his_html": "",
                "his_list": ""
              }));
            else
              res.end(JSON.stringify({
                "type": 1
              }));
          } else {
            global.log.info("res list json err:", json);
            res.end(JSON.stringify({
              "type": 0,
              "resource_list": {},
              "html": "获取资源失败"
            }));
          }*/
            res.end(JSON.stringify({
              "size": size,
              "type": 1,
              "resource_list": resource_list,
              "isPrivateDownload": 0,
              "m_uid": 0
            }));
          } else {
            global.log.info("get res json err:", json.toString());
            res.end(JSON.stringify({
              "type": 0,
            }));
          }
        });
      } else if (d == 10) {
        var local = utils.getLocalHistory();
        var hash_list = [];
        var size_list = [];
        for (var item in local) {
          hash_list.push(item);
          size_list.push(parseInt(local[item]["size"]));
        }
        var his_count = hash_list.length;
        if (his_count == 0) {
          res.end(JSON.stringify({
            "type": 1,
            "resource_list": []
          }));
        } else {
          hash_list = hash_list.join();
          size_list = size_list.join();
          var params = {};
          var d = {};
          d["user"] = global.uid;
          d["file_hashes"] = hash_list;
          d["file_sizes"] = size_list;
          d["count"] = his_count;
          d["cookie"] = global.cookie;
          params["headers"] = {
            "Cookie": JSON.stringify(global.cookie),
            "X-Requested-With": "XMLHttpRequest"
          };
          params["data"] = d;
          params["method"] = "POST";
          params["timeout"] = 30000;
          request(settings.url + "view_resource_download", params, function(err, datas) {
            if (err != null) {
              res.end(JSON.stringify({
                "type": 0,
                "his_html": "",
                "his_list": ""
              }));
              return;
              //throw err;
            }
            var json;
            try {
              json = JSON.parse(datas);
            } catch (e) {
              json = datas;
              //json = $.parseJSON(data);
            }
            //global.log.info(json["type"]+"test");
            if (json && 'type' in json && json["type"] == 1) {
              his_list = json["result"];
              if (his_list) {
                utils.decrypt_resource_list(his_list);
                //var path = __dirname + "/views/resourceList.ejs",
                //  str = fs.readFileSync(path, "utf-8");
                his_list.sort(function(a, b) {
                  return local["" + b['file_hash']]['time'] - local["" + a['file_hash']]['time']
                });
                //var his_render = "";
                var size = 0;
                var ret = [];
                for (var num in his_list) {
                  var fileHash = his_list[num]['file_hash'];
                  if (local[fileHash + ""]) {
                    var progress = parseInt(local[fileHash + ""]["progress"]);
                    var isPrivateDownload = parseInt(local[fileHash + ""]["private"]);
                    if (progress < 100) {
                      his_list[num]["isContinue"] = true;
                      his_list[num]["progress"] = progress;
                      his_list[num]["time"] = local[fileHash + ""]["time"];
                    } else {
                      his_list[num]["finish"] = true;
                      his_list[num]["time"] = local[fileHash + ""]["time"];
                    }
                    his_list[num]["isPrivateDownload"] = isPrivateDownload;
                    size ++;
                    ret.push(his_list[num]);
                    /*his_render += ejs.render(str, {
                      m_uid: 0,
                      isMyInfo: false,
                      flag: "m",
                      isHis: true,
                      isPrivateDownload: isPrivateDownload,
                      resourceList: [his_list[num]],
                      toLocalTime: toLocalTime,
                      getResourceType: getResourceType
                    });*/
                  }
                }
                res.end(JSON.stringify({
                  "size": size,
                  "type": 1,
                  "resource_list": ret
                }));
                /*res.end(JSON.stringify({
                  "type": 1,
                  "his_html": his_render,
                  "his_list": his_list
                }));*/
              } else
                res.end(JSON.stringify({
                  "type": 1,
                  "resource_list": []
                }));
            } else {
              global.log.info("his res list json err:", datas.toString());
              res.end(JSON.stringify({
                "type": 0,
                "his_html": "获取资源失败",
                "his_list": ""
              }));
            }
          });
        }
      } else if (d == 5) {
        p["comment"] = cipher.encrypt(p["comment"]);
        p["nick_name"] = global.nick_name;
        req.query = {};
        req.body = p;
        webUtil(req, res, "POST", settings.url + "res", function(data) {
          //global.log.info(data);
          var result;
          try {
            result = JSON.parse(data);
          } catch (e) {
            result = data;
          }
          res.end(JSON.stringify(result));
        });
      } else if (d == 6) {
        webUtil(req, res, "POST", settings.url + "res", function(data) {
          //global.log.info(data);
          var result;
          try {
            result = JSON.parse(data);
          } catch (e) {
            result = data;
          }
          res.end(JSON.stringify(result));
        });
      } else if (d == 7) {
        p["key_word"] = cipher.encrypt(p["key_word"]);
        req.query = {};
        req.body = p;
        webUtil(req, res, "POST", settings.url + "res/search", function(data) {
          var json;
          try {
            json = JSON.parse(data);
          } catch (e) {
            json = data;
          }
          if (json && 'type' in json && json["type"] == 1) {
            var result = json["result"];
            var resource_list = result["res"];
            var size = result["size"];
            utils.decrypt_resource_list(resource_list);
            var len = resource_list.length;
            //filter the history
            var num = len;
            while (num--) {
              var fileHash = resource_list[num]['file_hash'] + "";
              var isDir = false;
              if ("file_hashes" in resource_list[num])
                isDir = true;
              if (utils.isExist(fileHash, isDir)){
                /*resource_list.splice(num, 1);
                size --;*/
                resource_list[num]["downloaded"] = 1;
              }
              else{
                resource_list[num]["downloaded"] = 0;
              }
            }
            //var path = __dirname + "/views/resourceList.ejs",
            //  str = fs.readFileSync(path, "utf-8");
            /*var ret = ejs.render(str, {
              m_uid: 0,
              isMyInfo: false,
              flag: "m",
              isHis: false,
              isPrivateDownload: 0,
              resourceList: resource_list,
              toLocalTime: toLocalTime,
              getResourceType: getResourceType
            });*/
            if (resource_list)
              res.end(JSON.stringify({
                "size": size,
                "len": len,
                "type": 1,
                "resource_list": resource_list,
                "isPrivateDownload": 0
              }));
            else
              res.end(JSON.stringify({
                "type": 1
              }));
          } else {
            global.log.info("search json err:", json);
            res.end(JSON.stringify({
              "type": 0,
              "resource_list": {},
              "html": "获取资源失败"
            }));
          }
        });
      } else if (d == 8) {
        var isMyInfo = false;
        if (p["uid"] == p["friend"])
          isMyInfo = true;
        webUtil(req, res, "POST", settings.url + "view_user_resource", function(data) {
          var json;
          try {
            json = JSON.parse(data);
          } catch (e) {
            json = data;
            //json = $.parseJSON(data);
          }
          if (json && 'type' in json && json["type"] == 1) {
            var result = json["result"];
            var resource_list = result["res"];
            var size = result["size"];
            utils.decrypt_resource_list(resource_list);
            if(!isMyInfo){
              var len = resource_list.length;
              //filter the history
              var num = len;
              while (num--) {
                var fileHash = resource_list[num]['file_hash'] + "";
                var isDir = false;
                if ("file_hashes" in resource_list[num])
                  isDir = true;
                if (utils.isExist(fileHash, isDir)){
                  resource_list[num]["downloaded"] = 1;
                }
                else{
                  resource_list[num]["downloaded"] = 0;
                }
              }
            }
            /*var path = __dirname + "/views/resourceList.ejs",
              str = fs.readFileSync(path, "utf-8");
            var isPrivateDownload = parseInt(p["isPrivateDownload"]);
            if(all_friends.indexOf(parseInt(p["friend"])) != -1)
              isPrivateDownload = 1;
            var ret = ejs.render(str, {
              m_uid: p["friend"],
              isMyInfo: isMyInfo,
              flag: "f",
              isHis: false,
              isPrivateDownload: isPrivateDownload,
              resourceList: resource_list,
              toLocalTime: toLocalTime,
              getResourceType: getResourceType
            });
            if (resource_list)
              res.end(JSON.stringify({
                "size": size,
                "type": 1,
                "resource_list": resource_list,
                "html": ret
              }));
            else
              res.end(JSON.stringify({
                "type": 1
              }));*/
            var isPrivateDownload = 1;
            if("isPrivateDownload" in p)
              isPrivateDownload = parseInt(p["isPrivateDownload"]);
            if(isPrivateDownload == 0 && all_friends.indexOf(parseInt(p["friend"])) != -1)
              isPrivateDownload = 1;
            res.end(JSON.stringify({
              "size": size,
              "type": 1,
              "resource_list": resource_list,
              "isPrivateDownload": isPrivateDownload,
              "m_uid": p["friend"]
            }));
          } else {
            global.log.info("get friend res json err:", json);
            res.end(JSON.stringify({
              "type": 0,
            }));
          }
        });
      } else if (d == 9) {
        req.query = req.body;
        webUtil(req, res, "GET", settings.url + "view_friends_resources", function(data) {
          var json;
          try {
            json = JSON.parse(data);
          } catch (e) {
            json = data;
          }
          if (json && 'type' in json && json["type"] == 1) {
            var result = json["result"];
            var resource_list = result["res"];
            var size = result["size"];
            utils.decrypt_resource_list(resource_list);
            var len = resource_list.length;
            //filter the history
            var num = len;
            while (num--) {
              var fileHash = resource_list[num]['file_hash'] + "";
              var isDir = false;
              if ("file_hashes" in resource_list[num])
                isDir = true;
              if (utils.isExist(fileHash, isDir))
                resource_list[num]['downloaded'] = 1;
              else
                resource_list[num]["downloaded"] = 0;
            }
            /*var path = __dirname + "/views/resourceList.ejs",
              str = fs.readFileSync(path, "utf-8");
            resource_list.sort(function(a, b) {
              return b['mtime'] - a['mtime'];
            });
            var ret = ejs.render(str, {
              m_uid: 0,
              isMyInfo: false,
              flag: "p",
              isHis: false,
              isPrivateDownload: 1,
              resourceList: resource_list,
              toLocalTime: toLocalTime,
              getResourceType: getResourceType
            });*/
            if (resource_list)
              res.end(JSON.stringify({
                "size": size,
                "len": len,
                "type": 1,
                "resource_list": resource_list,
                isPrivateDownload: 1
              }));
            else
              res.end(JSON.stringify({
                "size": 0,
                "len": 0,
                "type": 1,
                "resource_list": [],
                isPrivateDownload: 1
              }));
          } else {
            global.log.info("get friend res json err:" + json);
            res.end(JSON.stringify({
              "type": 0,
              "resource_list": {},
              "html": "获取资源失败"
            }));
          }
        });
      }
    });
  app.get("/static/*", function(req, res) {
      var reqUrl = req.originalUrl;
      //global.log.info(req.originalUrl.indexOf("/user_icon/"+global.uid) !== -1);
      //global.log.info(upyunToken.getUpyunToken(settings.upyun + reqUrl));
      //get the picture
      var isUserIcon = (req.originalUrl.indexOf("/user_icon/") !== -1);
      if (reqUrl.indexOf("?v=") !== -1) {
        var tmp = reqUrl.split('?');
        reqUrl = tmp[0];
        if (!isUserIcon)
          req.type = tmp[1].split("&")[1];
      } else {
        var tmp = reqUrl.split('?');
        reqUrl = tmp[0];
        if (!isUserIcon)
          req.type = tmp[1];
      }
      if (!isUserIcon)
        req.type = req.type.split("=")[1];
      else
        req.type = 10;
      //global.window.console.log(reqUrl);
      if(req.originalUrl.indexOf("/user_icon/"+global.uid) !== -1){
        //global.window.console.log(upyunToken.getUpyunToken(settings.upyun + reqUrl));
        webUtil(req, res, "GET", upyunToken.getUpyunToken(settings.upyun + reqUrl), true);
        return;
      }
      var localStorePath = path_s.join(global.fbt, reqUrl);
      fs.exists(localStorePath, function(exists) {
        if (exists) {
          fs.readFile(localStorePath, function(err, data) {
            if (err) {
              global.log.error("read image from local error:", err);
              if (req.originalUrl.indexOf("static") > 0)
              //webUtil(req, res, "GET", settings.url + req.originalUrl.replace("/",""), true);
                webUtil(req, res, "GET", upyunToken.getUpyunToken(settings.upyun + reqUrl), true);
              global.log.info(settings.upyun + reqUrl);
            } else {
              var header = {
                'Content-Type': mime.lookup(path_s.extname(reqUrl)),
                'Content-Length': fs.statSync(localStorePath).size
              };
              res.writeHead(200, header);
              res.end(data);
//              global.log.info("use cache:", reqUrl);
            }
          });
        } else {
          if (req.originalUrl.indexOf("static") > 0)
          //webUtil(req, res, "GET", settings.url + req.originalUrl.replace("/",""), true);
            webUtil(req, res, "GET", upyunToken.getUpyunToken(settings.upyun + reqUrl), true);
          global.log.info(settings.upyun + reqUrl);
        }
      });
    });
    app.post("/:actualPath", function(req, res) {
      webUtil(req, res, "POST", settings.url + req.params.actualPath, false);
    });
    app.get("/reset", function(req, res) {
      webUtil(req, res, "GET", settings.url + "reset_password", function(data) {
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        res.end(JSON.stringify(result));
      });
    });
    app.get("/logout", function(req, res) {
      webUtil(req, res, "GET", settings.url + "logout", function() {
        logout();
      });
    });
    app.get("/token", function(req, res) {
      request(settings.url + "token", {}, function(err, data) {
        //global.log.info(err);
        if (err != null) {
          res.end(JSON.stringify({type: 0, "error": "服务君可能出了点故障，正在被抢修中"}));
          return;
          //throw err;
        } else {
          //global.log.info(data.toString());
          try {
            var tmp;
            try {
              tmp = JSON.parse(data);
            } catch (e) {
              tmp = data;
            }
            if (tmp) {
              global.token = tmp["result"];
              tmp["platform"] = process.platform;
              res.cookie('_xsrf', tmp["result"]);
              res.writeHead(200, {
                "Content-Type": "application/json"
              });
              res.end(JSON.stringify(tmp));
            } else {
              res.end(JSON.stringify({
                "type": 0
              }));
            }
          } catch (e) {
            global.log.info(e);
            return;
          }
        }
      });
    });
    app.get("/startServer/:server", function(req, res) {
      var s = req.params.server;
      global.log.info("start server " + s);
      if (s == "local") {
        httpServer.start({
          fbtHost: settings.host,
          fbtPort: settings.port,
          fbtUser: global.uid,
          resourceDB: global.res_hash_collection
        });
      } else if (s == "nat") {
        global.log.info("hash:", req.query.hash);
        global.log.info("size:", req.query.size);
        //注释v4
        //fileUploadV4.initV4Upload(req.query.for, req.query.hash, req.query.size);
      }
      res.end("ok");
      global.log.info("server start");
    });
    app.get("/inform", function(req, res) {
      webUtil(req, res, "GET", settings.url + "tip_off_resource", function(data) {
        var result;
        try {
          result = JSON.parse(data);
        } catch (e) {
          result = data;
        }
        res.end(JSON.stringify(result));
      });
    });
    app.get("/html/:addr", function(req, res) {
      var path = __dirname + "/views/" + req.params.addr,
        str = fs.readFileSync(path, "utf-8");
      res.end(str);
    });
    app.get("/editIcon", function(req, res) {
      var p = req.query;
      var dataurl = p["path"];
      var base64Image = decodeURIComponent(dataurl.replace(/^data:image\/\w+;base64,/, ''));
      p["data"] = base64Image;
      var m = dataurl.match(/^data:image\/(\w+);base64,/);
      if (m == null) {
        return res.end(JSON.stringify({
          "type": 0,
          "error": "文件读取发生错误"
        }));
      }
      p["ext"] = '.' + m[1];
      p["path"] = Date.parse(new Date()) + ""; //random filename
      req.query = {};
      req.body = p;
      global.log.info("Edit icon");
      //global.log.info(p);
      webUtil(req, res, "POST", settings.url + "myInfo", function(data) {
        var json;
        try {
          json = JSON.parse(data);
        } catch (e) {
          json = data;
          //json = $.parseJSON(data);
        }
        res.end(JSON.stringify(json));
      });
    });
    app.get("/get_file_info", function(req, res){
      webUtil(req, res, "GET", settings.url + "get_file_info", function(data) {
        var json;
        try {
          json = JSON.parse(data);
        } catch (e) {
          json = data;
          //json = $.parseJSON(data);
        }
        if (json && 'type' in json && json["type"] == 1) {
          var result = json["result"];
          var fileHash = result['file_hash'] + "";
          var isDir = false;
          if ("file_hashes" in result)
            isDir = true;
          if (utils.isExist(fileHash, isDir))
            result['downloaded'] = 1;
          else
            result["downloaded"] = 0;
          if("file_name" in result){
            var tmp = [result];
            utils.decrypt_resource_list(tmp);
            json["result"] = tmp[0];
          }
        }
        res.end(JSON.stringify(json));
      });
    });
    app.get("/:actualPath", function(req, res) {
      if(req.path == "/get_university")
        webUtil(req, res, "GET", settings.studyHost + req.originalUrl, false);
      else
        webUtil(req, res, "GET", settings.url + req.originalUrl.substring(1), false);
    });
    //type 0 is download, 1 is error, 2 is action, 3 is pause, 4 is resume, 5 is cancel
    //6 is cancel callback
    //action 0 is html, 1 is inc, 2 is append, 3 is css, 4 is attr
    /*io.configure(function () { 
      io.set("transports", ["xhr-polling"]); 
      io.set("polling duration", 10); 
    });*/
    io.on('connection', function(socket) {
      global.socket = socket;
      global.reward = {};
      global.isMaxWin = false;
      if(parseInt(process.versions['node-webkit'].split('.')[1]) > 8){
        initWin();
      }
      //注释V4
      //fileUploadV4 = require('./fileDownloadV4/uploaderV4.js');
      fileDownload = require('./downloadController.js');
      global.log.info("socket create");
      //global.window.console.log("socket connect");
      socket.on('download', function(msg) {
        //type 0 is download
        //global.log.info("socket msg" + msg);
        msg = JSON.parse(msg);
        if(msg["rid"]) 
          global.reward[utils.gen_file_id(msg["hash"], msg["size"])] = msg["rid"];
        if (msg["fileHashs"]) {
          var isContinue = false;
          if ("continue" in msg)
            isContinue = true;
          dl.addOrStartDir(msg["hasError"],msg["fileNames"], isContinue, msg["dirName"], msg["fileHashs"], msg["fileSizes"], msg["hash"], msg["size"], msg["private"], msg["html"], downloadFileCallback);
        } else {
          if (!("continue" in msg) && !parseInt(msg["hasError"]) && global.historys[msg["hash"] + ""]) {
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": msg["html"],
              "error": "无需重复下载"
            }));
            return;
          } else if ("progress" in msg && parseInt(msg["progress"]) > 0) {
            var block = global.historys[msg["hash"] + ""]["block"];
            var size = global.historys[msg["hash"] + ""]["fileSize"];
            var progress = global.historys[msg["hash"] + ""]["progress"];
            global.socket.emit('download', JSON.stringify({
              "type": 2,
              "html": msg["html"],
              "progress": progress,
              "value": size + "  " + progress + "%"
            }));
            /*global.socket.emit('download', JSON.stringify({
              "type": 2,
              "html": '#download_progress_bar' + msg["html"],
              "actions": [3, 4],
              "value": [{
                'width': progress + '%'
              }, {
                'aria-valuenow': progress
              }]
            }));*/
          }
          // FIXME: arguments html
          dl.addOrStartFile(msg["dirName"], msg["hash"], msg["size"], msg["private"], msg["html"], downloadFileCallback);
        }
      });
      socket.on('pauseFileDownload', function(msg) {
        msg = JSON.parse(msg);
        global.log.info("download pause");
        if (msg["isDir"]) {
          var obj = dl.getCurHashAndSize(msg["hash"], msg["size"]);
          if(obj){
            msg["hash"] = obj[0];
            msg["size"] = obj[1];
            if (msg["hash"] + "" in global.historys || obj[2] != 0) {
              pauseFileDownload(msg["hash"], msg["size"]);
            }
          }
          /*else{
            utils.inform("oops~暂停貌似出了点问题，可以试试重启");
          }*/
        } else if (msg["hash"] + "" in global.historys) {
          pauseFileDownload(msg["hash"], msg["size"]);
        }
      });
      socket.on('resumeFileDownload', function(msg) {
        msg = JSON.parse(msg);
        global.log.info("download resume");
        if (msg["isDir"]) {
          var obj = dl.getCurHashAndSize(msg["hash"], msg["size"]);
          if(obj){
            msg["hash"] = obj[0];
            msg["size"] = obj[1];
            if (msg["hash"] + "" in global.historys || obj[2] != 0) {
              resumeFileDownload(msg["hash"], msg["size"]);
            }
          }
          /*else{
            utils.inform("oops~继续下载貌似出了点问题，可以试试重启");
          }*/
        } else if (msg["hash"] + "" in global.historys) {
          resumeFileDownload(msg["hash"], msg["size"]);
        }
      });
      socket.on('cancelFileDownload', function(msg) {
        global.log.info("download cancel" + msg);
        msg = JSON.parse(msg);
        var dirHash = 0;
        var dirSize = 0;
        if (msg["isDir"]) {
          dirHash = msg["hash"];
          dirSize = msg["size"];
          var obj = dl.getCurHashAndSize(msg["hash"], msg["size"]);
          if(obj){
            msg["hash"] = obj[0];
            msg["size"] = obj[1];
          }
          /*else{
            utils.inform("oops~删除貌似出了点问题，可以试试重启");
          }*/
        }
        cancelFileDownload(msg["html"], msg["hash"], msg["size"], dirHash, dirSize);
      });
      socket.on("friend", function(msg) {
        msg = JSON.parse(msg);
        global.log.info("render friend");
        var path = __dirname + "/views/friendItem.ejs",
          str = fs.readFileSync(path, "utf-8");
        all_friends.push(parseInt(msg["uid"]));
        var ret = ejs.render(str, msg);
        var online = msg["online"];
        global.socket.emit("friend", JSON.stringify({
          "html": ret,
          "online": online
        }));
      });
      socket.on("delFriend", function(msg){
        var uid = parseInt(msg);
        utils.removeArrayItem(all_friends, uid);
      });
      /*socket.on("history",function(msg){
        global.log.info("recieve a history event");
        delete global.historys[msg+""];
        sets.saveHistory();
      });*/
      socket.on("download_err",function(msg){
        global.log.info("recieve a history event");
        delete global.historys[msg+""];
        global.log.info("save download err");
        sets.saveHistory();
      });
      socket.on("first", function(msg) {
        //global.window.console.log("first");
        global.setting["first"] = 0;
        sets.saveSetting();
      });
      socket.on("s_first", function(msg) {
        global.setting["s_first"] = 0;
        sets.saveSetting();
      });
      socket.on('close', function() {
        global.log.info("socket end");
      });
      socket.on('update', function() {
        global.log.info(global.update_name);
        var commands = {
          'win32': "\"",
          'linux' :"x-terminal-emulator -e bash \"",
          'darwin' :"open \""
        };
        if(commands[process.platform]) {
          child_process.exec(commands[process.platform]+global.update_name+"\"",function(){});
          setTimeout(update_exit, 2000);
        }
      });
      socket.on("s_upload", function(msg) {
        msg = JSON.parse(msg);
        var h = msg["hash"] + "";
        if (h in uploadList.hashToPath) {
          var u = uploadList.getUpload(uploadList.hashToPath[h]);
          if (u)
            u.uploadCallback(msg["suc"]);
          delete uploadList.hashToPath[h];
        }
      });
      socket.on('tick', function() {
        //global.log.info("recieve a tick event");
        fileDownload.cleanup();
        //sets.saveHistory();
      });
      socket.on("douban", function(data) {
        getDoubanInfo(data);
      });
      socket.on("init", function() {
        global.nat_type = null;
        var NW_VERSION = process.versions['node-webkit'];
        checkUpdate();
        /*if (process.platform == 'win32') {
          var spawn = child_process.spawn;
          spawn('cmd.exe', ['/c', 'init.bat', process.pid]);
          var p = "\"" + path_s.join(path_s.dirname(process.execPath), "fbt.exe") + "\"";
          spawn('cmd.exe', ['/c', 'avoidFw.bat', p]);
        }*/
        // load download state
        global.parts_left = {};
        /*
        (function loadDownloadState() {
          global.parts_left_collection.find({},
            function(err, docs) {
              doc: [
                  {hash: hash1, parts_left: [1,2,3]}
                  {hash: hash2, parts_left: [1,2,3]}
              ]
              docs.forEach(function(doc) {
                global.parts_left[doc.hash] = doc.parts_left;
              });
            }
          );
        })();
        */
      });
      socket.on("open_dir", function(msg) {
        msg = JSON.parse(msg);
        var fileName = "";
        var hash = "" + msg['file_hash'];
        var filepath = "";
        if("isDir" in msg){
          res_api.get_path_from_hash(hash, msg['isDir'], function(path){
            if(path)
              openDir(path);
            else
              global.socket.emit("inform", "本地木有找到该资源诶，可能你是在其他电脑登录吧");
          });
        }
        else{
          if(hash in global.historys){
            filename = global.historys["" + msg['file_hash']]['name'];
          }
          else{
            filename = utils.getDirnameByHash(hash);
          } 
          filepath = path_s.join(global.setting["downloadSaveDir"], filename);
          openDir(filepath);
        }
        //global.log.info(filepath);
        
      });
      socket.on('file_name', function(msg) {
        global.socket.emit("file_name", path_s.basename(msg));
      });
      socket.on('winmin', function(){
        process.mainModule.exports.winMin();
      });
      socket.on('winmax', function(){
        if(global.isMaxWin)
          process.mainModule.exports.winUnMax();
        else
          process.mainModule.exports.winMax();
        global.isMaxWin = !global.isMaxWin;
      });
      socket.on('winclose', function(){
        process.mainModule.exports.winClose();
      });
      socket.on('winopen', function(url){
        process.mainModule.exports.winOpen(url);
      });
      socket.on('winopenex', function(url){
        process.mainModule.exports.winOpenEx(url);
      });
      /*socket.on("jieba", function(data){
        var segment = require(path_s.join(global.exec_path,"nodejieba"));
        var d1 = path_s.join(global.exec_path,"nodejieba","dict","jieba.dict.utf8");
        var d2 = path_s.join(global.exec_path,"nodejieba","dict","hmm_model.utf8");
        segment.loadDict(d1, d2);
        //global.log.info(d1);
        segment.cut(data, function(wordList) {
            global.log.info(wordList);
            global.socket.emit("jieba", ",".join(wordList));
        });
      });*/
    });
    http.listen(12345);
    global.log.info("express start");
    /*require(path_s.join(global.exec_path, 'getmac')).getMac(function(err, macAddress) {
      if (err) return;
      global.identify = '';
      for (var index = 0, jk = macAddress.length; index < jk; index++) {
        global.identify += macAddress.charCodeAt(index);
      }
    });*/
  }
  init();

  function update_exit() {
    process.exit(1);
  }
}
