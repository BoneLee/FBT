var cipher=require('./encrypt');
var fs = require("fs");
var path = require("path");
function inform(msg){
    if(global.socket)
        global.socket.emit("inform", msg);
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
function getDirnameByHash(dirHash){
    for(var item in global.historys){
      if("dirHash" in global.historys[item] && global.historys[item]["dirHash"] == dirHash){
        return global.historys[item]["dirName"];
      }
    }
    return null;
}
function getLocalHistory(){
  var ret = {};
  for(var item in global.historys){
    var tmp = {};
    tmp["time"] = global.historys[item]["time"];
    tmp["private"] = global.historys[item]["private"];
    if("rid" in global.historys[item] && global.historys[item]['rid'])
        global.reward[global.historys[item]["fid"]] = global.historys[item]['rid'];
    if("dirHash" in global.historys[item])
    {
        if(!(global.historys[item]["dirHash"] in ret)){
            tmp["size"] = global.historys[item]["dirSize"];
              var dirId = gen_file_id(global.historys[item]["dirHash"], tmp["size"]);
              if(dirId in global.dir){
                var size = (global.dir[dirId]["hashList"]).length; 
                var complete = parseInt(global.dir[dirId]["complete"]); 
                if(complete == size){
                    tmp["progress"] = 100;
                }
                else   
                    tmp["progress"] = complete/size*100;
              }
              else{
                tmp["progress"] = 0;
                global.log.info("history and dir recode error, dirID:"+dirId);
              }
              ret[global.historys[item]["dirHash"]] = tmp;
        }
        else
            continue;
    }
    else{
      if("size" in global.historys[item])
        tmp["size"] = global.historys[item]["size"];
      else
        tmp["size"] = 0;
      tmp["progress"] = global.historys[item]["progress"];
      ret[item] = tmp;
    }
  }
  return ret;
}
function gen_file_id(file_hash, file_size){
    return file_hash + "_" + file_size;
}
function getBytes(str) {//thanks to http://ixti.net/development/node.js/2011/10/26/get-utf-8-string-from-array-of-bytes-in-node-js.html
    var bytes = [], char;
    str = encodeURI(str);
    while (str.length) {
        char = str.slice(0, 1);
        str = str.slice(1);
        if ('%' !== char) {
            bytes.push(char.charCodeAt(0));
        } else {
            char = str.slice(0, 2);
            str = str.slice(2);
            bytes.push(parseInt(char, 16));
        }
    }
    return bytes;
}

function gbkToUnicode(str) {//user uploaded file name is GBK. you have to encode it to utf8
//return new Buffer(unescape(encodeURIComponent(str)),'utf8').toString();
    return new Buffer(getBytes(str)).toString('utf8');
}
// debug assert
var assert = function(condition, message) { 
    if (!condition){
        global.log.info("Assert failed" + (typeof message !== "undefined" ? ": " + message : ""));
        //throw Error("Assert failed" + (typeof message !== "undefined" ? ": " + message : ""));
    }
};


//python range
function range(lowEnd,highEnd){
	var arr = [];
	while(lowEnd < highEnd){
	   arr.push(lowEnd++);
	}
	return arr;
}

//remove element item in array arr
function removeArrayItem(arr, item) {
    if(!arr)
        return;
    var removeCounter = 0;

    for (var index = 0; index < arr.length; index++) {       
        if ( JSON.stringify(arr[index]) === JSON.stringify(item) ) {
            arr.splice(index, 1);
            removeCounter++;
            index--;
        }
    }

    return removeCounter;
}


//rangdom choose item in array items
function randomChoose(items){
	return items[Math.floor(Math.random()*items.length)];
}

function find(arr, obj){  
     for(var i = 0;i<arr.length;i++){  
        if(arr[i] == obj){  
           return i;  
         }  
     }  
     return -1;  
   }  

//if an array is empty
function isEmpty(arr){
	return arr.length==0;
}

function first(arr){
	assert(!isEmpty(arr));
	return arr[0];
}

//length of array
function len(arr){
	return arr.length;
}

function length_of_hash(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
}

// Get the size of an object
//var size = Object.size(myArray);

//if a var is defined
//function defined(variable){
//	return typeof(variable) !== 'undefined';
//}

function isFunction(f){
	return typeof(f)==='function';
}

function getUserHome() {
  return process.env[(process.platform == 'win32') ? 'USERPROFILE' : 'HOME'];
}
function decryptResourceList(resource_list){
    for(var num in resource_list){//resource is a list, not a hash dict
        resource_list[num]['tags']=cipher.decrypt(resource_list[num]['tags']);
        resource_list[num]['file_name']=cipher.decrypt(resource_list[num]['file_name']);
        /*var comments=resource_list[num]['comments'];
        for(var i=0;i<comments.length;++i){
            comments[i]['content']=cipher.decrypt(comments[i]['content']);
        }
        resource_list[num]['comments']=comments;*/
    }
}
function download_app(host, p, name, dir){
  var newVersionDownloadUrl = require(path.join(global.exec_path, 'url-join'))(host, p);
  var file_name = name;
  var file = fs.createWriteStream(path.join(dir,file_name));
  global.update_name = path.join(dir,file_name);
  var request = require(path.join(global.exec_path, 'request'));
  var r = request(newVersionDownloadUrl).pipe(file);
  r.on('finish', function(){
    //global.window.console.log("update complete");
    global.socket.emit("update");
    file.end();
  });
}

(function(){
    var fbt = path.join(getUserHome(),".fbt");
    var nedb = path.join(getUserHome(),".fbt","nedb_data");
    if(fs.existsSync(fbt)){
        if(!fs.existsSync(nedb))
        {
            try{
                fs.mkdirSync(nedb);
            }catch(e) {//pass error
            }
        }
    }
    else{
        try{
            fs.mkdirSync(fbt);
            fs.mkdirSync(nedb);
        }catch(e) {//pass error
        }
    }
    global.fbt = fbt;
})();
function moveToFbt(){
    /*var m = path.join(global.fbt, 'node_modules');
    var exec_path;
    if (process.platform === "darwin")
        exec_path = path.join(path.dirname(__dirname), "node_modules");
    else
        exec_path = path.join(path.dirname(process.execPath), "node_modules");
    var flag = path.join(path.dirname(process.execPath), "flag");
    var flag_e = fs.existsSync(flag);
    if(!fs.existsSync(m) || flag_e)
    {      
        var fs_sync = require(path.join(exec_path, 'fs-sync'));  
        //fs_sync.remove(m);
        fs_sync.copy(exec_path, m, {"force":true});
        if(flag_e)
            fs.unlinkSync(flag);
    }*/
    if (process.platform === "darwin")
        global.exec_path = path.join(path.dirname(__dirname), "node_modules");
    else
        global.exec_path = path.join(path.dirname(process.execPath), "node_modules");
}
//global.logOpened=0;
if(!global.logOpened){
    moveToFbt();
    var Log = require(path.join(global.exec_path,'log'));
    global.log = new Log('debug', fs.createWriteStream(path.join(global.fbt,'fbt.log')));
    global.logOpened=1;
}

function isPathInUsb(path, callback) {
    var result = false;
    switch (process.platform) {
        case 'win32' :
            var path_drive = path[path.indexOf(':')-1];
            require('child_process').exec('USB_detect.bat', function(err,out,stderr) {
                var usbdrive_list = out.toString().split('\n');
                usbdrive_list.some(function(usbdrive_string){
                    if (usbdrive_string.indexOf(':') !== -1) {
                        var usbdrive = usbdrive_string[usbdrive_string.indexOf(':')-1];
                        if (path_drive.toLowerCase() === usbdrive.toLowerCase()) {
                            result = true;
                            return true;  // 退出遍历
                        }
                    }
                });
                callback(result);
            });
            break;
        case 'linux' :
            if (path.indexOf('/media') === 0) {
                result = true;
            }
            callback(result);
            break;
        case 'darwin' :
            if (path.indexOf('/Volume') === 0) {
                result = true;
            }
            callback(result);
            break;
        default :
            callback(result)
    }
}

var isWindows = process.platform === 'win32';
function normalizeArray(parts, allowAboveRoot) {
    // if the path tries to go above the root, `up` ends up > 0
    var up = 0;
    for (var i = parts.length - 1; i >= 0; i--) {
        var last = parts[i];
        if (last === '.') {
            parts.splice(i, 1);
        } else if (last === '..') {
            parts.splice(i, 1);
            up++;
        } else if (up) {
            parts.splice(i, 1);
            up--;
        }
    }

    // if the path is allowed to go above the root, restore leading ..s
    if (allowAboveRoot) {
        for (; up--; up) {
            parts.unshift('..');
        }
    }

    return parts;
}
var normalizeUNCRoot = function(device) {
    return '\\\\' + device.replace(/^[\\\/]+/, '').replace(/[\\\/]+/g, '\\');
};
if (isWindows) {

    var splitDeviceRe =
        /^([a-zA-Z]:|[\\\/]{2}[^\\\/]+[\\\/]+[^\\\/]+)?([\\\/])?([\s\S]*?)$/;

    exports.fbtNormalize = function(path) {
        var result = splitDeviceRe.exec(path),
            device = result[1] || '',
            isUnc = device && device.charAt(1) !== ':',
            isAbsolute = !!result[2] || isUnc, // UNC paths are always absolute
            tail = result[3],
            trailingSlash = /[\\\/]$/.test(tail);

        // If device is a drive letter, we'll normalize to upper case.
        if (device && device.charAt(1) === ':') {
          device = device[0].toUpperCase() + device.substr(1);
        }

        // Normalize the tail path
        tail = normalizeArray(tail.split(/[\\\/]+/).filter(function(p) {
          return !!p;
        }), !isAbsolute).join('\\');

        if (!tail && !isAbsolute) {
          tail = '.';
        }
        if (tail && trailingSlash) {
          tail += '\\';
        }

        // Convert slashes to backslashes when `device` points to an UNC root.
        // Also squash multiple slashes into a single one where appropriate.
        if (isUnc) {
          device = normalizeUNCRoot(device);
        }

        return device + (isAbsolute ? '\\' : '') + tail;
    };
} else {
    exports.fbtNormalize = function (path) {
        var isAbsolute = path.charAt(0) === '/',
            trailingSlash = path.substr(-1) === '/';

        // Normalize the path
        path = normalizeArray(path.split('/').filter(function (p) {
            return !!p;
        }), !isAbsolute).join('/');

        if (!path && !isAbsolute) {
            path = '.';
        }
        if (path && trailingSlash) {
            path += '/';
        }

        return (isAbsolute ? '/' : '') + path;
    };
}

exports.find = find;
exports.assert=assert;
exports.range=range;
exports.removeArrayItem=removeArrayItem;
exports.randomChoose=randomChoose;
exports.isEmpty=isEmpty;
exports.len=len;
exports.first=first;
exports.isFunction=isFunction;
exports.length_of_hash=length_of_hash;
exports.getUserHome=getUserHome;
exports.gbkToUnicode = gbkToUnicode;
exports.decrypt_resource_list = decryptResourceList;
exports.download_app = download_app;
exports.isPathInUsb = isPathInUsb;
exports.gen_file_id = gen_file_id;
exports.isExist = isExist;
exports.getLocalHistory = getLocalHistory;
exports.getDirnameByHash = getDirnameByHash;
exports.inform = inform;
