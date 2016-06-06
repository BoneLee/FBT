//var $ = require('jquery');
var settings = require("./settings");
var fs = require('fs');
var path_s = require("path");
var Datastore = require(path_s.join(global.exec_path, 'nedb'));
var utils = require('./res/utils');
var res_api = require('./res/res_api');
var querystring = require('querystring');
var sets = require("./setting/fbtSetting.js");
var fbtUtils = require('./fbtUtils/fbtUtils');
var mkdirp = require(path_s.join(global.exec_path, 'mkdirp'));

//init the nedb
var RES_INFO_PATH = settings.RES_INFO_PATH,
    RES_HASH_PATH = settings.RES_HASH_PATH,
    PARTS_LEFT_PATH = settings.PARTS_LEFT_PATH;

global.res_info_collection = new Datastore({
  filename: RES_INFO_PATH,
  autoload: true
});

global.res_hash_collection = new Datastore({
  filename: RES_HASH_PATH,
  autoload: true
});

/*
global.parts_left_collection = new Datastore({
  filename: PARTS_LEFT_PATH,
  autoload: true
});
global.parts_left.persistence.setAutocompactionInterval(1800000);
*/

global.res_info_collection.ensureIndex({
  fieldName: 'rootdir'
}, function(err) {
  if (err)
    global.log.error('error creating index rootdir:', err);
});

var request = function(url, args, callback) {
  var urllib = require(path_s.join(global.exec_path, 'urllib'));
  args["timeout"] = 30000;
  args["data"] = args["data"] || {};
  args["data"]["from"] = "client";
  args["data"]["version"] = "2.0";
  /*if (!("uid" in args["data"]))
    args["data"]["uid"] = global.uid;*/
  if (global.token)
    args["data"]["token"] = global.token;
  //global.window.console.log(url);
  urllib.request(url, args, function(err, data, res) {
    return callback(err, data, res);
  });
};
//remove element item in array arr
function removeItem(arr, item) {
  if (!arr)
    return;
  var removeCounter = 0;

  for (var index = 0; index < arr.length; index++) {
    if (arr[index] === item) {
      arr.splice(index, 1);
      removeCounter++;
      index--;
    }
  }

  return removeCounter;
}

function uploadDel() {
  var tmp = {};
  tmp["del"] = global.uploadDeleteHash.join(',');
  tmp["size"] = global.uploadDeleteSize.join(',');
  tmp["isDir"] = global.uploadDeleteDir.join(',');
  global.uploadDeleteHashTmp = global.uploadDeleteHash;
  global.uploadDeleteSizeTmp = global.uploadDeleteSize;
  global.uploadDeleteDir.Tmp = global.uploadDeleteDir;
  global.uploadDeleteHash = [];
  global.uploadDeleteSize = [];
  global.uploadDeleteDir = [];
  tmp["op"] = 3;
  tmp["uid"] = global.uid;
  var params = {};
  tmp["cookie"] = global.cookie;
  params["headers"] = {
    "Cookie": JSON.stringify(global.cookie),
    "X-Requested-With": "XMLHttpRequest"
  };
  params["data"] = tmp;
  params["method"] = "POST";
  params["timeout"] = 30000;
  global.log.info("upload del");
  global.log.info(params);
  request(settings.url + "res/delete", params, function(err, data) {
    global.log.info("delete res");
    if (err != null) {
      global.log.info(err.stack + "\n");
    } else {
      var result;
      try {
        result = JSON.parse(data);
      } catch (e) {
        result = data;
      }
      data = result;
      if ("type" in data && data["type"] == 0) {
        for (var i = 0; i < global.uploadDeleteHashTmp.length; i++) {
          global.uploadDeleteHash.push(global.uploadDeleteHashTmp[i]);
          global.uploadDeleteSize.push(global.uploadDeleteSizeTmp[i]);
          global.uploadDeleteDir.push(global.uploadDeleteDirTmp[i]);
        }
      }
      if (global.uploadDeleteHash.length != 0) {
        global.uploadDeleteInterval = setTimeout(uploadDel, 2000);
      } else
        delete global.uploadDeleteInterval;
      delete global.uploadDeleteSizeTmp;
      delete global.uploadDeleteHashTmp;
      delete global.uploadDeleteDirTmp;
    }
  });
}

function uploadDirDel(dirId) {
  var tmp = {};
  tmp["uid"] = global.uid;
  var params = {};
  tmp["cookie"] = global.cookie;
  tmp["dirId"] = dirId;
  params["headers"] = {
    "Cookie": JSON.stringify(global.cookie),
    "X-Requested-With": "XMLHttpRequest"
  };
  params["data"] = tmp;
  params["method"] = "POST";
  params["timeout"] = 30000;
  global.log.info("upload dir del");
  global.log.info(params);
  request(settings.url + "res/delete/dir", params, function(err, data) {
    global.log.info("delete dir res");
    if (err != null) {
      global.log.info(err.stack + "\n");
    } else {
      global.log.info("delete dir: "+dirId);
    }
  });
}

function pushAndStart(hash, size, isDir) {
  global.log.info("pushAndStart");
  if (global.uploadDeleteHash) {
    if(!(hash in global.uploadDeleteHash)){
      global.uploadDeleteHash.push(hash);
      global.uploadDeleteSize.push(size);
      global.uploadDeleteDir.push(isDir);
    }
  } else {
    global.uploadDeleteHash = [];
    global.uploadDeleteHash.push(hash);
    global.uploadDeleteSize = [];
    global.uploadDeleteSize.push(size);
    global.uploadDeleteDir = [];
    global.uploadDeleteDir.push(isDir);
  }
  if (!global.uploadDeleteInterval)
    global.uploadDeleteInterval = setTimeout(uploadDel, 2000);
}

function isExist(hash, isDir){
  if(hash in global.historys)
    return true;
  if(isDir){
    for(var item in global.historys){
      if("dirHash" in global.historys[item] && global.historys[item]["dirHash"] == hash)
        return true;
    }
  }
  return false;
}

function fileDel(hash, size){
  var tmp = hash + "";
  var shouldRemove = true;
  var dirHash = 0;
  var dirSize = 0;
  if(tmp in global.historys && "dirHash" in global.historys[tmp]){
    dirHash = global.historys[tmp]["dirHash"];
    dirSize = global.historys[tmp]["dirSize"];
    var dir_id = fbtUtils.gen_file_id(dirHash, dirSize);
    var file_id = fbtUtils.gen_file_id(hash, size);
    var hashList = global.dir[dir_id]["hashList"];
    var sizeList = global.dir[dir_id]["sizeList"];
    fbtUtils.removeArrayItem(hashList, tmp);
    fbtUtils.removeArrayItem(sizeList, size+"");
    if(hashList.length === 0){
      delete global.dir[dir_id];
      sets.saveDir();
    }
  }
  delete global.historys[tmp];
  global.log.info("save file remove");
  sets.saveHistory();
  if(dirHash && isExist(dirHash, true)){
    shouldRemove = false;
  }
  global.log.info(hash);
  return [shouldRemove, dirHash, dirSize];
}

function fileChangeCallback(path, res_size, isSubfile) {
  path = fbtUtils.fbtNormalize(path);
  global.log.info("fileChangeCallback" + path);
  removeItem(global.res_list, path);
  res_api.get_res_hash(path, function(err, hash) {
    /*res_api.get_res_size(path, function(err, res_size){
      if(err){
        res_size = 0;
        global.log.info("remove res error " + path);
      }
    });*/
    var obj = fileDel(hash, res_size);
    if(obj[0]){
      var html = "";
      if(obj[1]){
        html = obj[1]+"m"+obj[2];
      }
      else{
        html = hash + "m" + res_size;
      }
      global.socket.emit("his_del", JSON.stringify({
        "html": html
      }));
    }
    res_api.remove_res(path);
    if (err) {
      global.log.info(err);
      return;
    }
    if(isSubfile)
      isSubfile = "1";
    else
      isSubfile = "0";
    pushAndStart(hash, res_size, isSubfile);
  });
}

function initResCallback(hash, size, isSubfile) {
  fileDel(hash, size);
  if(isSubfile)
    isSubfile = "1";
  else
    isSubfile = "0";
  pushAndStart(hash, size, isSubfile);
}
var initRes = function() {
  utils.setCallback(fileChangeCallback, initResCallback);
  var res_main = require('./res/res_main');
  //upload the what the resource change
  res_main.init(fileChangeCallback);
};
/*exports.xhrProvider = function (onprogress) {
  return function () {
    var xhr = $.ajaxSettings.xhr();
    if (onprogress && xhr.upload) {
      xhr.upload.addEventListener('progress', onprogress, false);
    }
    return xhr;
  };
};
exports.ajaxRequest = function (url, params, callback) {
  var processData = true;
  if (params.content) {
    processData = false;
  }
  var playload = params.playload;
  if (playload !== 'string') {
    params.dataType = 'json';
  }
  params.timeout = 30000;
  var xhr = xhrProvider(params.progress);
  var self = this;
  $.ajax({
    url: url,
    type: params.type || 'GET', 
    headers: params.headers || {}, 
    data: params.content || params.data, 
    processData: processData,
    timeout: params.timeout, 
    dataType: params.dataType,
    xhr: xhr,
    success: function (data, textStatus, res) {
      return callback(null, data);
    }, 
    error: function (res, textStatus, err) {
      return callback(textStatus, err);
    }
  });
};*/
exports.fileChangeCallback = fileChangeCallback;
exports.request = request;

function start_sock() {
  global.log.info("check socket creating ?");
  if (global.socket) {
    global.log.info("setInterval, send uid to client");
    global.socket.emit("start_sock", JSON.stringify({
      "uid": global.uid,
      "user": global.user,
    }));
    //注释v4
    //global.socket.emit("initpeer", global.uid); // PeerJs initialization, create Peer for download/upload
    clearInterval(global.start_socket);
    delete global.start_socket;
  }
}
function reportServerError(){
  return JSON.stringify({type: 0, "error": "服务君可能出了点故障，正在被抢修中"});
}
exports.webUtil = function(req, res, method, url, fn) {
  var params = {};
  var d;
  if (method == "GET")
    d = req.query || req.body;
  else
    d = req.body || req.query;
  //global.log.info(d);
  if (req.params.actualPath == "login" && d && "password" in d) {
    global.log.info("save user and password");
    global.setting["user"] = d["user"];
    global.setting["pwd"] = d["password"];
    sets.saveSetting();
  }
  if (req.params.actualPath == "registration" && d && "refer" in d) {
    var id = require('os').hostname();
    if (global.identify)
      id = global.identify;
    d["identify"] = id;
  }
  if (global.cookie) {
    d["cookie"] = global.cookie;
    params["headers"] = {
      "Cookie": JSON.stringify(global.cookie),
      "X-Requested-With": "XMLHttpRequest"
    };
  }
  params["data"] = d;
  params["method"] = method;
  params["timeout"] = 30000;
  //global.window.console.log(params);
  //global.window.console.log(fn);
  request(url, params, function(err, data, response) {
    //global.log.info(params);
    //global.window.console.log(err);
    //global.window.console.log(url);
    //global.window.console.log(data.toString());
    if (err != null || data.toString().indexOf("500 internal server error") != -1) {
      res.end(reportServerError());
      //throw err;
    } else {
      if ('function' == typeof fn || !fn)
        global.log.info(url + data.length);
      var header = response.headers;
      var result;
      try {
        result = JSON.parse(data);
      } catch (e) {
        result = data;
      }
      data = result;
      if (req.params.actualPath == "login" && data && data["type"] == 1) {
        var nick_name = data["result"]["nick_name"];
        var param = {};
        var cookies = header["set-cookie"];
        for (var item in cookies) {
          var tmp = cookies[item].split(";")[0].split("=");
          param[tmp[0]] = tmp[1];
        }
        global.nick_name = nick_name;
        global.uid = param["fbt_user_id"];
        global.user = param["fbt_user"];
        global.log.info("uid:" + global.uid);
        //注释v4
        //require('./fileDownloadV4/forwardUploader.js');
        if (global.socket){
          global.socket.emit("start_sock", JSON.stringify({
            "uid": param["fbt_user_id"],
            "user": param["fbt_user"]
          }));
          //注释v4
          //global.socket.emit("initpeer", global.uid); // PeerJs initialization, create Peer for download/upload
        }
        else {
          global.start_socket = setInterval(start_sock, 100);
        }
        global.cookie = param;
        initRes();
        var p = {};
        p["data"] = {
          "cookie": param
        };
        p["headers"] = {
          "Cookie": JSON.stringify(param),
          "X-Requested-With": "XMLHttpRequest"
        };
        //global.window.console.log(p);
        request(settings.url, p, function(err, datas, r) {
          if (err || (datas && datas.toString().length == 0)) {
            res.end(reportServerError());
            return;
          }
          //global.window.console.log(datas.toString());
          global.log.info("login" + datas.length);
          var result;
          try {
            result = JSON.parse(datas);
          } catch (e) {
            global.log.info("login req");
            result = datas;
          }
          datas = result;
          //global.window.console.log("result");
          //global.window.console.log(result.toString());
          if (datas && datas["type"] == 1) {
            datas["result"]["nick_name"] = nick_name;
            global.main_data = datas["result"];
            var sel = Math.ceil(Math.random()*4);
            if(global.setting["allow_bg"] == 0)
              sel = -1;
            global.main_data["bg"] = sel;
            global.socket.emit('index', JSON.stringify(global.main_data));
            res.header("set-cookie", cookies);
            res.header("Content-Type", "application/json");
            res.end(JSON.stringify({"type": 1}));
          } else {
            res.header("Content-Type", "application/json");
            res.end(JSON.stringify(datas));
          }
        });
        request(settings.studyUrl, {}, function(err,datas,r){
          //global.log.info(datas.toString());
        });
      } else {
        if ('function' == typeof fn) {
          global.log.info("html");
          fn(data);
        } else {
          if (fn) {
            var code = (response.statusCode + "").substr(0, 1);
            //global.log.info(response);
            if (code == "4" || code == "5") {
              var default_pic = path_s.join(__dirname, "static", "images", "file_type", req.type + ".png");
              fs.readFile(default_pic, function(err, dataFromFile) {
                global.log.info("default pic", err);
                header["content-length"] = dataFromFile.length;
                res.writeHead(200, header);
                res.end(dataFromFile);
              });
            } else {
              var reqUrl = req.originalUrl;
              if (reqUrl.indexOf("?v=") > -1 || reqUrl.indexOf("?type=") > -1) {
                reqUrl = reqUrl.split('?')[0];
              }
              if (reqUrl.indexOf('upaiyun') > -1) {
                reqUrl = reqUrl.substr(reqUrl.indexOf("/static"));
              }
              var localStorePath = path_s.join(global.fbt, reqUrl);
              header["content-length"] = data.length;
              res.writeHead(200, header);
              res.end(data);
              if (!fs.existsSync(path_s.dirname(localStorePath))) {
                mkdirp.sync(path_s.dirname(localStorePath));
              }
              fs.writeFile(localStorePath, data, function(err) {
                if (err) {
                  global.log.error("write image to local error:", err);
                } else {
                  global.log.info("add cache: ", localStorePath);
                }
              });
            }
          } else {
            global.log.info("json");
            //global.log.info(data);
            try {
              result = JSON.parse(data);
            } catch (e) {
              result = data;
            }
            res.header("Content-Type", "application/json");
            if (result)
              res.end(JSON.stringify(result));
            else
              res.end(JSON.stringify({}));
          }
        }
      }
    }
  });
};
