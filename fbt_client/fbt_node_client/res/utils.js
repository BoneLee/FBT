/*
res_hash 存储格式
{
    path: filepath,
    verify: hash
}
final_hash 由分块 hash 的结果连起来做 hash 生成
direct_file_hash 直接hash文件得到, 用于检验文件是否被修改

res_info 存储格式
{
    name: filename,
    path: filepath,
    size: filesize,
    mtime: last modified time,
    rootdir: uploadDir,  // 也没有这个field
    isFolderRes: true,  // 如果不是文件夹里的文件，就没有这个field
}

parts_left 存储格式
{
    hash: hash
    parts_left: [3,4,5,6]
}

根据path确保每个文件的【唯一性】, 这一点已经由store时的update操作保证,
所以别的操作都可已直接用findOne({'path':path})

凡是涉及数据库操作, 一律将path先规范化, path.normalize(path), Win和Unix分别用\和/

服务器端可以存储res_hash或者res_info的_id来对应本地资源
 */

var fs = require('fs'), 
    path = require('path'),
    fbtUtils = require('../fbtUtils/fbtUtils'),
    watch = require(path.join(global.exec_path,'watch')),
    xxhash = require(path.join(global.exec_path,'xxhashjs')),
    ratelimit = require(path.join(global.exec_path,'ratelimit'));
    settings = require('../settings');


var fileChangeCallback;
var initResCallback;
var BLOCK_SIZE = settings.BLOCK_SIZE;
function setCallback(cb,cb1){
  //global.log.info(cb);
  //global.log.info(cb1);
  fileChangeCallback = cb;
  initResCallback = cb1;
}


function store_res_hash(filepath, upload_id, seed, todo) {
  try {
    // add verify field
    var hasher = new xxhash(seed);
    var hashedDataBytes = 0;
    var lastHasedDataBytes = 0;
    var fileTotalBytes = fs.statSync(filepath)['size'];
    var hashProgress = 0;
    var rs = fs.createReadStream(filepath);
    ratelimit(rs, global.setting["upload_speed"]);
    rs.on('data', function(data) {
      hasher.update(data);
      hashedDataBytes += data.length;
      if (hashedDataBytes >= fileTotalBytes) {
        global.socket.emit("upload", JSON.stringify({
          "id": upload_id, "type":3, "progress": "99%"
        }));
      } else {
        // 超过 50M 才会往前端发消息, 频繁发会卡
        if (hashedDataBytes - lastHasedDataBytes > 5242880) {
          if (hashedDataBytes > 104857600) {
            // 第一次延迟一点发, 不然也会卡
            hashProgress = hashedDataBytes / fileTotalBytes;
            hashProgress = (100 * hashProgress).toFixed(2) + '%';
            global.socket.emit("upload", JSON.stringify({
              "id": upload_id, "type":3, "progress": hashProgress
            }));
            lastHasedDataBytes = hashedDataBytes;
          }
        }
      }
    })
    .on('end', function(){
      global.log.info("hash finish");
      var hashvalue = hasher.digest();
      var newDoc = {
        'path': fbtUtils.fbtNormalize(filepath),
        'verify': parseInt(hashvalue)
      };
      global.res_hash_collection.update(
        {'path': fbtUtils.fbtNormalize(filepath)},
        newDoc,
        {'multi': true, 'upsert': true},
        function (err, numReplaced) {
          if (numReplaced !== 1) {
            global.log.info("found duplicate hash docs when storing");
          }
          todo = (typeof(todo) === 'undefined') ? update_page_content : todo;
          todo(newDoc);
        }
      );
    });

    global.socket.once("cancel-upload"+upload_id, function(){
      global.log.info("cancel upload");
      rs.close();
    });
  }
  catch (err) {
    global.log.info(err.message);
  }
}

function store_res_hash_download(filepath, filehash, seed, todo) {
  try {
    // add verify field
    var hasher = new xxhash(seed);
    fs.createReadStream(filepath)
      .on('data', function(data) {
        hasher.update(data);
      })
      .on('end', function(){
        var hashvalue = hasher.digest();
        if (filehash != hashvalue) {
          global.log.info("hash not equal");
          todo(false);
        } else {
          global.log.info("hash equal");
          global.log.info("download complete: ", path.basename(filepath));
          var newDoc = {
            'path': fbtUtils.fbtNormalize(filepath),
            'verify': parseInt(hashvalue)
          };
          global.res_hash_collection.update(
            {'path': fbtUtils.fbtNormalize(filepath)},
            newDoc,
            {'multi': true, 'upsert': true},
            function (err, numReplaced) {
              if (numReplaced != 1) {
                global.log.info("found duplicate hash docs when storing");
              }
              todo = (typeof(todo) === 'undefined') ? update_page_content : todo;
              todo(true, newDoc);
            }
          );
        }
      });
  }
  catch (err) {
    global.log.info(err.message);
  }
}

function store_res_info(filepath, monitors, todo) {
  /*存储资源的 名字, 在用户电脑中的绝对位置, 大小, mtime*/
  var stats = fs.statSync(filepath);

  var newDoc = {
    'name': path.basename(filepath),
    'path': fbtUtils.fbtNormalize(filepath),
    'size': stats['size'],
    'mtime': stats['mtime'].getTime()
  };

  global.res_info_collection.update(
    { 'path': fbtUtils.fbtNormalize(filepath) },
    newDoc,
    { 'multi': true, 'upsert': true },
    function(err, numReplaced) {
      if (numReplaced != 1) {
        global.log.info("found duplicate info docs when storing");
      }
      global.log.info("res store finish");
      todo = (typeof(todo) === 'undefined') ? update_monitors : todo;
      var events = {
        'store': newDoc
      };
      if (todo === update_monitors)
        todo(events, monitors);
      else
        todo(newDoc);
    }
  );
}

function store_res_info_in_folder(filepath, rootdir) {
  /*
   上传文件夹时使用, 在doc中加入rootdir域, 取消monitor相关操作
   */
  var stats = fs.statSync(filepath);

  var newDoc = {
    'name': path.basename(filepath),
    'rootdir': rootdir,
    'isFolderRes': true,
    'path': fbtUtils.fbtNormalize(filepath),
    'size': stats['size'],  // size is int
    'mtime': stats['mtime'].getTime()
  };
  global.res_info_collection.update(
    { 'path': fbtUtils.fbtNormalize(filepath) },
    newDoc,
    { 'multi': false, 'upsert': true },
    function(err, numReplaced) {
      if (numReplaced != 1) {
        global.log.info("found duplicate info docs when storing");
      }
    }
  );
}

function remove_res_infohash(filepath, monitors, todo) {
  var query = {'path': fbtUtils.fbtNormalize(filepath)};
  var query_s = {'path': path.normalize(filepath)};
  //global.log.info(query.path);
  var info_no_doc = false;
  var hash_no_doc = false;
  global.res_info_collection.count({"$or":[query,query_s]}, function(err, count) {
    if (count === 0) {
      info_no_doc = true;
      global.log.info("Found no info doc when removing");
    } else if (count > 1) {
      global.log.info("Found duplicate info doc when removing");
    }
    global.res_hash_collection.count({"$or":[query,query_s]}, function(err, count) {
      if (count === 0) {
        global.log.info("found no hash doc when removing");
        hash_no_doc = true;
      } else if (count > 1) {
        global.log.info("Found duplicate hash doc when removing");
      }
      todo = (typeof(todo) === 'undefined') ? update_monitors : todo;
      if (!hash_no_doc) {
        global.res_hash_collection.remove({"$or":[query,query_s]}, {});
      }
      if (!info_no_doc) {
        global.res_info_collection.find({"$or":[query,query_s]}, function(err, docs) {
          docs.forEach(function(doc){
            global.log.info("toberemoved:", doc);
            global.res_info_collection.remove({path:doc.path}, {}, function(){
              todo({'remove': doc}, monitors);
            });
          });
        });
      }
    });
  });
}


function clear_db(monitors) {
  global.res_hash_collection.find({}, function (err, docs) {
    global.log.info("\nold hash record:\n", JSON.stringify(docs));
    global.res_hash_collection.remove({}, {multi: true}, function (err, numRemoved) {
      global.log.info("\nremoved %d hash record", numRemoved);
    });
  });
  global.res_info_collection.find({}, function (err, docs) {
    global.log.info("\nold info record:\n", JSON.stringify(docs));
    global.res_info_collection.remove({}, {multi: true}, function (err, numRemoved) {
      global.log.info("\nremoved %d info record", numRemoved);
    });
  });

  var events = {'clear': true};
  update_monitors(events, monitors);
}


// 邓波请修改update_page_content函数, 因为资源信息在callback中才能获取, 所以没法作为返回值
// 现在作为演示, 把资源信息显示在页面上, 实际中怎么用得你来考虑
// 总之传入的参数是js object形式的资源信息
function update_page_content(json, extra) {
  extra = (typeof extra === "undefined") ? '' : extra;
//    document.getElementById("body").innerHTML += extra + '<br />' + JSON.stringify(json);
  global.log.info(json, extra);
}

function createMonitor(newDoc, monitors, cb) {

  function is_watch_file(watchfile, f) {
    return fbtUtils.fbtNormalize(watchfile) === fbtUtils.fbtNormalize(f);
  }

  function createEventListener(monitor, res_path, size) {
    monitor.on("created", function (f, stat) {
      if (!is_watch_file(res_path, f)) return;
      if (f === null)
        global.log.info("on create, filename is null");
      else {
        global.log.info(f + " has been created.");
      }
    });
    monitor.on("changed", function (f, curr, prev) {
      if (!is_watch_file(res_path, f)) return;
      if (f === null)
        global.log.info("on change, filename is null");
      else {
        global.log.info(f + " has changed.");
        fileChangeCallback(f, prev['size'], false);
        monitor.stop();
      }
    });
    monitor.on("removed", function (f, stat) {
      if (!is_watch_file(res_path, f)) return;
      if (f === null)
        global.log.info("on delete, filename is null");
      else {
        global.log.info(f + " has been removed.");
        fileChangeCallback(f, size, false);
        monitor.stop();
      }
    });
  }

  var res_path = newDoc.path,
    watch_root = path.dirname(res_path);

  watch.createMonitor(watch_root, {
    'filter': function(f) {
      return (path.basename(res_path) === path.basename(f))
    },
    'ignoreUnreadableDir': true,
    'ignoreNotPermitted': true,
    'ignoreBusyOrLocked': true
  }, function(monitor){
    monitors[res_path] = monitor;
    createEventListener(monitor, res_path, newDoc.size);
  });
}


// 数据库操作之后, 更新monitors, 根据events决定是加入新monitor还是停止旧monitor
// 不会在store_res_hash中调用
function update_monitors(events, monitors) {
  switch (Object.keys(events)[0]) {
    case 'clear':
      for (var file in monitors) {
        if (monitors.hasOwnProperty(file)) {
          monitors[file].stop();  // stop需要时间, 如果马上delete会stop失败
          setTimeout(function(){
            delete monitors[file];
          }, 2000);
        }
      }
      break;
    case 'remove':
      var docRemoved = events['remove'];
      if ('rootdir' in docRemoved) {
        global.res_info_collection.count(
          {'rootdir': docRemoved.rootdir},
          function(err, count) {
            if (err)
              global.log.error('error removing res with rootdir:'+err);
            else {
              if (count == 0) {
                watch.unwatchTree(docRemoved.rootdir);
              }
            }
          }
        );
      }
      var path = docRemoved.path;
      if (path in monitors) {
        monitors[path].stop();
        setTimeout(function () {
          delete monitors[path];
        }, 2000);
        global.log.info("monitors after removing:");
      }
      break;
    case 'store':
      var newDoc = events['store'];  // newDoc is res_info
      // 一个monitor和一个文件对应, 不能监视目录, 除非资源就是一个目录!
      if (!monitors.hasOwnProperty(newDoc.path))  // monitor不存在才添加
        createMonitor(newDoc, monitors);
  }
}


function check_res_update(res_info, res_hash) {
  /*
   * this function should not operate on monitors, but only update db
   */
  var path = res_info.path;
  fs.exists(path, function(exists){
    if (exists) {
      fs.stat(path, function(err, stats){
        if (res_info.mtime != stats['mtime'].getTime()) {
          // 一旦mtime不同, 再检查hash, 如果相同, 那么只需要更新res_info的mtime
          // 否则得调用store_res_info, store_res_hash进行更新
          var hasher = new xxhash(settings.seed);
          fs.createReadStream(path)
            .on('data', function (data) {
              hasher.update(data);
            })
            .on('end', function () {
              var hashvalue = hasher.digest();
              if (res_hash && (hashvalue == res_hash.verify)) {
                global.res_list.push(res_info.path);
                global.log.info(path, " modified but not changed");
                // file content unchanged, only need to update mtime
                global.res_info_collection.update(
                  {'path': path},
                  {'$set': {'mtime': stats['mtime'].getTime()}}, {}
                );
              }
              else {
                // file content changed, remove res
                global.log.info(path, " modified and changed.");
                if (res_hash) {
                  initResCallback(res_hash.verify, res_info.size, 'isFolderRes' in res_info);
                }
                remove_res_infohash(path, global.monitors);
              }
            });
        } else {
          global.res_list.push(res_info.path);
        }
      });
    } else { // 文件不存在, 说明在客户端关闭期间已经删除, 故从数据库里也删除
      if (res_hash) {
        initResCallback(res_hash.verify, res_info.size, 'isFolderRes' in res_info);
      }
      remove_res_infohash(path, global.monitors);
      global.log.info(path + ' has been removed.');
    }
  });
}

function myWatchTree(Dir, files) {
  global.log.info("start watching dir:", Dir);
  watch.watchTree(Dir, {
    'ignoreUnreadableDir': true,
    'ignoreNotPermitted': true,
    'ignoreBusyOrLocked': true,
    'filter': function(f) {
      if (files) { // for dirUpload, should only watch files in root folder
        return files.indexOf(f) !== -1;
      } else {
        return true;
      }
    }
  }, function(f, curr, prev){
    if (typeof f == "object" && prev === null && curr === null) {
      global.log.info("watchtree traverse finish.");
    } else if (prev === null) {
      global.log.info(f + " has been created.");
    } else {
      if (curr.nlink === 0) {
        global.log.info(f + " has been removed.");
      } else {
        global.log.info(f + " has changed.");
      }
      //global.log.info(prev);
      if (prev.isFile()) {
        global.res_info_collection.findOne(
          {"$or":[
            {path: f},
            {path: fbtUtils.fbtNormalize(f)}
          ]},
          function(err, doc) {
            if (doc) {
              global.log.debug("Yes I called fileChangeCallback");
              fileChangeCallback(f, doc['size'], 'isFolderRes' in doc);
            } else {
              /*
              Note that this does not mean something is wrong,
              this could happen when:
              1. add a file into a download folder then launch FBT then remove the file
              2. add a file into an upload folder then launch FBT then remove the file
              so just ignore it and do nothing
               */
              global.log.error("file changed, but can't find in res_info");
            }
          }
        );
      }
      if (prev.isDirectory()) {
        global.log.info(f + " is dir and we don't care");
      }
    }
  });
}

function updateResPath(oldPath, newPath, oldRootdir, newRootdir) {
  global.res_info_collection.findOne(
    {'path': oldPath},
    function(err, doc) {
      if (doc) {
        var toSet = {"$set": {'path': newPath}};
        if ('rootdir' in doc) {
          toSet["$set"]['rootdir'] = newRootdir;
        } else {  // 更新monitor，针对非文件夹文件
          global.monitors[oldPath].stop();
          doc['path'] = newPath;
          setTimeout(function(){
            delete global.monitors[oldPath];
            update_monitors({'store': doc}, global.monitors);
          }, 2000);
        }
        // 更新数据库
        global.res_info_collection.update(
          {'path': oldPath}, toSet, {},
          function(err, numReplaced) {
            global.res_hash_collection.update(
              {'path': oldPath},
              {"$set": {'path': newPath}}, {},
              function(err, numReplaced) {
                global.log.info("Path updated: " + oldPath + '\n-> ' + newPath);
              }
            )
          }
        )
      } else {
        global.log.error("Fatal error, no such res when updating path.")
      }
    }
  )
}

exports.store_res_hash = store_res_hash;
exports.store_res_info = store_res_info;
exports.store_res_info_in_folder = store_res_info_in_folder;
exports.remove_res_infohash = remove_res_infohash;
exports.clear_db = clear_db;
exports.update_page_content = update_page_content;
exports.createMonitor = createMonitor;
exports.check_res_update = check_res_update;
exports.store_res_hash_download = store_res_hash_download;
exports.setCallback = setCallback;
exports.myWatchTree = myWatchTree;
exports.updateResPath = updateResPath;
