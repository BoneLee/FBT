var webUtils = require("./webUtil");
var utils = require('./fbtUtils/fbtUtils');
var settings = require("./settings");
var path_s = require("path");
var request = webUtils.request;
var fileDownloadTypes = {
  "None": 0,
  "V4_LAN": 1,
  "V4_NAT": 2,
  "V6": 3, 
  "V4_NOT_ALLOW": 4
};
var downloadQ;
function saveDir(){
  require("fs").writeFileSync(require("path").join(global.fbt, 'dir.json'), JSON.stringify(global.dir, null, 2));
}
function continueDownload(dirId, fileHashs, fileSizes, fileNames){
  global.dir[dirId]["hashList"].concat(fileHashs);
  global.dir[dirId]["hashSize"].concat(fileSizes);
  for(var item in fileNames){
    global.dir[dirId]["nameList"][item] = fileNames[item];
  }  
  saveDir();
};

function setDownloadList(downloadL){
  downloadQ = downloadL;
}

function downloadList(){
  this.downloadQueue = {};
  this.allDownloadQueue = {};
  this.downloadingNum = 0;
  this.downloadQueueLength = 0;
  this.timeout = 0;
}

downloadList.prototype.addOrStartDir = function(hasError,fileNames,isContinue,dirName,hashList, sizeList, dirHash, dirSize, private, html, cb){
  var dirId = utils.gen_file_id(dirHash, dirSize);
  var cur_index = 0;
  //var fileIds = [];
  hashList = hashList.split(",");
  sizeList = sizeList.split(",");
  hasError = parseInt(hasError);
  if(hasError){
    this.delDirDownload(dirHash, dirSize);
    var dir = {"nameList":fileNames,"hashList":hashList, "hashSize":sizeList, "cur_index":0, "complete":0, "size": dirSize};
    global.dir[utils.gen_file_id(dirHash, dirSize)] = dir;
    saveDir();
  }
  else{
    for (var i = 0; i < hashList.length; i++) {
      if(hashList[i] in global.historys){
        delete fileNames[utils.gen_file_id(hashList[i], sizeList[i])];
        hashList.splice(i,1);
        sizeList.splice(i,1);
      }
      /*else{
        fileIds.push(utils.gen_file_id(hashList[i], sizeList[i]));
      }*/
    }
    if(hashList.length == 0){
      global.socket.emit('download', JSON.stringify({"type":1, "html":html,"error":"无需重复下载"}));
      return;
    }
    if(dirId in global.dir && dirId in this.downloadQueue){
      //用户在下载文件夹过程中又追加了下载文件
      global.log.info("append download");
      this.downloadQueue[dirId].appendFiles(hashList, sizeList, fileNames);
      return;
    }
    else if(dirId in global.dir && !isContinue){
      //用户在已经下完文件夹中的一部分后追加下载文件夹，此时可能之前下载的文件夹还处于继续下载可点击状态
      global.log.info("continue download");
      continueDownload(dirId, hashList, sizeList, fileNames);
      var downloadObj = new downloadFn(global.dir[dirId]["nameList"],global.dir[dirId]["complete"],global.dir[dirId]["hashList"], global.dir[dirId]["hashSize"], dirHash, dirSize,private, html,cb,dirName,true);
      downloadObj.doDownload(true);
      //global.window.console.log("continue download after");
      this.downloadQueue[dirId] = downloadObj;
      this.allDownloadQueue[dirId] = 1;
      var ret = {"html":html ,"dirId": dirId, "hashList": global.dir[dirId]["hashList"], "sizeList": global.dir[dirId]["hashSize"], "nameList": global.dir[dirId]["nameList"], "curIndex": global.dir[dirId]["complete"]};
      global.socket.emit("dir_download_continue", JSON.stringify(ret));
      return;
    }
    if(isContinue && (dirId in global.dir)){
      cur_index = global.dir[dirId]["cur_index"];
      hashList = global.dir[dirId]["hashList"];
      sizeList = global.dir[dirId]["hashSize"];
      fileNames = global.dir[dirId]["nameList"];
      var ret = {"html":html ,"dirId": dirId, "hashList": hashList, "sizeList": sizeList, "nameList": fileNames, "curIndex": cur_index};
      global.socket.emit("dir_download_continue", JSON.stringify(ret));
    }
    else{
      var dir = {"nameList":fileNames,"hashList":hashList, "hashSize":sizeList, "cur_index":0, "complete":0, "size": dirSize};
      global.dir[utils.gen_file_id(dirHash, dirSize)] = dir;
      saveDir();
    }
  }
  var downloadObj = new downloadFn(fileNames,cur_index,hashList, sizeList, dirHash, dirSize,private, html,cb,dirName,true);
  downloadObj.doDownload(true);
  this.downloadQueue[dirId] = downloadObj;
  this.allDownloadQueue[dirId] = 1;
};

downloadList.prototype.addOrStartFile = function(fileName,hash, size, private, html,cb){
  var fileNames = {};
  var fileId = utils.gen_file_id(hash, size);
  fileNames[fileId] = fileName;
  this.allDownloadQueue[fileId] = 1;
  (new downloadFn(fileNames,0,[hash], [size], 0, 0,private, html,cb,fileName,false)).doDownload(true);
};

downloadList.prototype.getCurHashAndSize = function(dirHash, dirSize){
  var dirId = utils.gen_file_id(dirHash, dirSize);
  var obj = this.downloadQueue[dirId];
  if(obj)
    return [obj.getCurHash(),obj.getCurSize(),obj.getCurIndex()];
  else
    return null;
}
downloadList.prototype.delFileDownload = function(fileHash, fileSize){
  var fileId = utils.gen_file_id(fileHash, fileSize);
  if(fileId in this.downloadQueue){
    this.downloadQueue[fileId].clear();
  }
}
downloadList.prototype.delDirDownload = function(dirHash, dirSize){
  var dirId = utils.gen_file_id(dirHash, dirSize);
  if(dirId in this.downloadQueue){
    this.downloadQueue[dirId].clear();
  }
  delete global.dir[dirId];
  saveDir();
}
downloadList.prototype.getFolderSize = function(dirId){
  if(dirId in this.downloadQueue) 
    return this.downloadQueue[dirId].getFolderSize();
  else
    return 0;
}

function downloadFn(fileNames, cur_index,hashList, sizeList, dirHash, dirSize, private, html,cb, dirName, isDir){
  this.hashList = hashList;
  this.sizeList = sizeList;
  this.dirHash = dirHash;
  this.dirSize = dirSize;
  this.dirId = utils.gen_file_id(dirHash, dirSize);
  this.cur_index = cur_index;
  this.private = private;
  this.cb = cb;
  this.html = html;
  this.dirName = dirName;
  this.isDir = isDir;
  this.fileNames = fileNames;
}

downloadFn.prototype.getFolderSize = function(){
  return this.sizeList.length;
};

downloadFn.prototype.appendFiles = function(fileHashs, fileSizes, fileNames){
  this.hashList.concat(fileHashs);
  this.sizeList.concat(fileSizes);
  for(var item in fileNames){
    this.fileNames[item] = fileNames[item];
  }
  global.dir[this.dirId]["hashList"] = this.hashList;
  global.dir[this.dirId]["hashSize"] = this.sizeList;
  global.dir[this.dirId]["nameList"] = this.fileNames;
  saveDir();
};

downloadFn.prototype.clear = function(){
  if(this.dirHash){
    delete downloadQ.allDownloadQueue[this.dirId];
  }
  else{
    var fileId = utils.gen_file_id(this.hashList[0], this.sizeList[0]);
    delete downloadQ.allDownloadQueue[fileId];
  }
  delete downloadQ.downloadQueue[this.dirId];
  delete this.hashList;
  delete this.sizeList;
  delete this.dirHash;
  delete this.dirSize;
  delete this.dirId;
  delete this.cur_index;
  delete this.private;
  delete this.cb;
  delete this.html;
  delete this.dirName;
  delete this.isDir;
  delete this.fileNames;
  //this = null;
};

downloadFn.prototype.getCurIndex = function(){
  return this.cur_index;
};

downloadFn.prototype.getCurHash = function(){
  if(this.cur_index < this.hashList.length)
    return this.hashList[this.cur_index];
  else
    return null;
};

downloadFn.prototype.getCurSize = function(){
  if(this.cur_index < this.sizeList.length)
    return this.sizeList[this.cur_index];
  else
    return null;
};

downloadFn.prototype.getNext = function(hasErr){
  //global.log.info(this);
  //global.log.info(hasErr);
  if(hasErr)
  {
    global.socket.emit("download_over", JSON.stringify({"dirId":this.dirId, "html":this.html}));
    global.socket.emit('download', JSON.stringify({"type":1, "html":this.html,"error":"网络不可用，暂时无法下载"}));
    //this.clear();
    return;
  }
  this.cur_index++;
  if(this.cur_index < this.hashList.length){
    global.dir[this.dirId]["cur_index"] ++;
    saveDir();
    this.doDownload(false);
  }
  else{
    if(this.isDir){
      global.socket.emit("download_over", JSON.stringify({"dirId":this.dirId, "html":this.html, "name":this.dirName}));
      global.socket.emit('download', JSON.stringify({"progress": 100, "type":2, "html": this.html ,"value":this.hashList.length + "/" + this.dirSize+" 100%"}));
      //global.socket.emit('download', JSON.stringify({"type":2, "html":'#download_progress_bar' + this.html, "actions":[3,4] ,"value":[{'width':100 + '%'},{'aria-valuenow': 100}]}));
      //global.socket.emit('download', JSON.stringify({"type":2, "html":'#text_messages_num', "actions":[1], "value":""}));
    }
    //global.socket.emit('download', JSON.stringify({"type":2, "html":'#list_tips', "actions":[2], "value":'<li><a href="#"><span class="tab">文件下载完毕：' + savedPostion + '</span></a></li>'}));
    this.clear();
  }
};

downloadFn.prototype.doDownload = function(shouldMove){
  var params = {};
  var d = {};
  d['user'] = global.uid;
  d['file_hash'] = this.hashList[this.cur_index];    
  d["size"] = this.sizeList[this.cur_index];
  d["dirHash"] = this.dirHash;
  d["dirSize"] = this.dirSize;
  d["private"] = this.private;
  d["allowV4Download"] = "0";//global.setting["allow_v4_download"]+"";
  d["cookie"] = global.cookie;
  params["headers"] = {"Cookie":JSON.stringify(global.cookie), "X-Requested-With":"XMLHttpRequest"};
  params["data"] = d;
  params["method"] = "GET";
  params["timeout"] = 30000;
  global.log.info("doDownload");
  //global.log.info(d);
  global.socket.emit('download', JSON.stringify({
    "type": 2,
    "html": this.html,
    "progress": 0,
    "value": "正在请求文件下载信息，请稍后"
  }));
  var that = this;
  var identify;
  if(this.dirHash){
    identify = this.dirId;
  }
  else{
    identify = utils.gen_file_id(this.hashList[0], this.sizeList[0]);
  }
  that.identify = identify;
  request(settings.url+"download_resource", params, function(err, data){
    if(!(that && that.identify in downloadQ.allDownloadQueue)){
      global.log.info("user has cancelled download before the server's response.");
      return;
    }
    if(err != null)
    {
      global.log.info(err.stack+"\n");
      global.socket.emit("download_error", that.identify);
    }
    else
    {
      //global.log.info(data.toString());
      var json;
      try{
        json=JSON.parse(data);
      }
      catch(e){
        global.log.info("socket msg type 0, json err");
        json = data;
      }
      if(json && json && 'type' in json && json['type']==1){
          //global.window.console.log(json.toString());
          utils.assert("file_info" in json);
          utils.assert("owners" in json);
          if(json["download_type"] == fileDownloadTypes["V4_NAT"] || json["download_type"] == fileDownloadTypes["V4_NOT_ALLOW"]){
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": that.html,
              "error": "很抱歉，该版本暂时不支持ipv4下载"
            }));
            return;
          }
          /*if(json["download_type"] == fileDownloadTypes["V4_NAT"] && process.platform === 'win32' && require('os').release()[0] <= '5'){
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": that.html,
              "error": "很抱歉，暂时不支持xp系统下的ipv4下载"
            }));
            return;
          }
          if(json["download_type"] == fileDownloadTypes["V4_NAT"] && process.versions['node-webkit'].indexOf("0.8") != -1){
            global.socket.emit('download', JSON.stringify({
              "type": 1,
              "html": that.html,
              "error": "很抱歉，该版本暂时不支持ipv4下载"
            }));
            return;
          }*/
          //{"owners": [], "file_info": {"file_hash": "714371632", "file_name": "README.txt", "file_size": "3906"}, "err": 0}
          var fileId = utils.gen_file_id(that.hashList[that.cur_index],that.sizeList[that.cur_index]);
          var file_info = {"file_id":fileId,"file_hash": that.hashList[that.cur_index], "file_name": that.fileNames[fileId], "file_size": that.sizeList[that.cur_index]};
          file_info["owners"]=json["owners"];
          file_info["html"] = that.html;
          file_info["hash"] = that.hashList[that.cur_index];
          file_info["download_type"] = json["download_type"];
          file_info["private"] = that.private;
          //global.log.info(file_info);
          //global.window.console.log("check disk");

          that.cb(null,file_info, shouldMove, that.dirHash, that.dirSize, that);

          /*
          //检测磁盘空间 TODO
          var diskspace = require(path_s.join(global.exec_path,'diskspace'));
          var dir = global.setting.downloadSaveDir;
          if(process.platform === 'win32') {
              global.log.info('Windows! dir: ' + dir);
              dir = dir[0];//on windows
          }
          diskspace.check(dir, function(err, total, free, status) {
            if(status == 'READY' && free < parseInt(file_info['file_size'])) {
              global.socket.emit('download', JSON.stringify({"type":1, "html":msg["html"],"error":"磁盘空间不足"}));
              global.log.info('downloadInfo NOT OK(no full space): ' + free + ' < ' + file_info['file_size']);
            }
            else {
              if(status != 'READY') {
                global.log.info('diskspace module not READY!');
                //global.log.info(global.setting.downloadSaveDir);
                //global.log.info(dir);
                global.log.info(err);
                //global.log.info(total);
                global.log.info(free);
                //global.log.info(status);
              }
              //global.window.console.log("check disk right");
              that.cb(null,file_info, shouldMove, that.dirHash, that.dirSize, that);
              //global.log.info("downloadInfo ok");
              global.log.info('downloadInfo OK: ' + free + ' < ' + file_info['file_size']);
            }
         });
         */
      }else{
        if(json["error"] == "no fb coin")
        {
          var file_info = {"html":that.html,"hash":that.hashList[that.cur_index]};
          that.cb(1, file_info, shouldMove, that.dirHash, that.dirSize, null);
        }
        else{
          global.log.info("downloadInfo json err:"+data.toString());
          global.socket.emit('download', JSON.stringify({
            "type": 1,
            "html": that.html,
            "error": "获取下载信息失败，请稍后重试"
          }));
        }
        //that.clear();
      }
    }
  });
};

exports.downloadList = downloadList;
exports.setDownloadList = setDownloadList;
