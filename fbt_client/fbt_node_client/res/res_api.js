var utils = require('./utils'),
  nodeUtil = require('util'),
  fbtUtils = require('../fbtUtils/fbtUtils'),
  fs = require('fs'),
  path = require('path'),
  filewalker = require(path.join(global.exec_path, 'filewalker')),
  watch = require(path.join(global.exec_path, 'watch')),
  xxhash = require(path.join(global.exec_path, 'xxhashjs')),
  async = require(path.join(global.exec_path, 'async')),
  settings = require('../settings');

var RES_INFO_PATH = settings.RES_INFO_PATH;

function add_res_upload(filepath, upload_id, todo) {
  try {
    //DEBUG
    global.log.info("monitors before adding: ");
    /*for (var file in global.monitors) {
        global.log.info(global.monitors[file]);
    }*/
    utils.store_res_hash(filepath, upload_id, settings.seed, todo);
    /*utils.store_res_hash(filepath, upload_id, settings.seed, function(){
      todo();
      utils.store_res_info(filepath, global.monitors);
    });*/
  } catch (err) {
    global.log.info(err.message);
  }
}

function get_path_from_hash(hash, isDir, callback) {
  global.res_hash_collection.findOne({
    'verify': parseInt(hash)
  }, function(err, doc) {
    if (doc == null) {
      callback(null);
      return;
    }

    if (isDir == false) {
      callback(doc.path);
    } else {
      global.res_info_collection.findOne({
        'path': doc.path
      }, function(err, doc){
        callback(doc.isFolderRes == true ? doc.rootdir : null);
      });
    }
  });
}

function get_res_info(filename) {
  global.res_info_collection.find({
    'name': filename
  }, function(err, docs) {
    utils.update_page_content(docs, 'get_res_file_info:\n');
  });
}

function get_res_size(path, callback) {
  global.res_info_collection.find({
    'path': path
  }, function(err, docs) {
    if (err) {
      global.log.info(err.message);
      callback(err);
    }
    if (docs !== null) // 有可能数据库中的数据之前已经被删了
      callback(null, docs["size"]);
    else
      callback(err);
  });
}

function get_allres_info() {
  return global.res_info_collection.find({}, function(err, docs) {
    if (err)
      global.log.info(err.message);
    //global.log.info(docs);
  });
}

function get_res_hash(path, callback) {
  global.res_hash_collection.findOne({
    'path': path
  }, function(err, docs) {
    if (err) {
      global.log.info(err.message);
      callback(err,0);
    }
    if (docs !== null) // 有可能数据库中的数据之前已经被删了
      callback(null,docs["verify"]);
  });
}

function get_allres_hash() {
  return global.res_hash_collection.find({}, function(err, docs) {
    if (err)
      global.log.info(err.message);
  });
}

function getPathUsingHashAndSize(hash, size, callback) {
  global.res_hash_collection.find({
    'verify': parseInt(hash)
  }, function(err, docs) {
    if (docs === null) {
      global.log.error("getPathUsingHashAndSize: no such file in res_hash");
    } else {
      var callback_called = false;
      docs.forEach(function(doc) {
        var filepath = doc.path;
        global.res_info_collection.findOne({
          path: filepath
        }, function(err, doc) {
          if (doc === null) {
            global.log.error("getPathUsingHashAndSize: no such file in res_info");
          } else {
            if (doc.size === parseInt(size)) {
              if (callback_called == false) {
                callback(filepath, doc.size);
                callback_called = true;
              }
            }
          }
        });
      });
    }
  });
}

function remove_res(filepath) {
  utils.remove_res_infohash(filepath, global.monitors);
}


function check_allres_update() {
  /*
  在开始监视文件之前必须检查文件在FBT客户端关闭的这段时间内的更改, 若有更改, 必须提示用户(其它操作待定)
   */
  if (!fs.existsSync(RES_INFO_PATH)) {
    global.log.info("no res exists, stop checking update");
    return;
  }
  global.res_info_collection.find({}, function(err, docs) {
    docs.forEach(function(res_info) {
      setImmediate(function(){
        global.res_hash_collection.findOne({
          'path': res_info.path
        }, function(err, res_hash) {
          utils.check_res_update(res_info, res_hash);
        });
      });
    });
  });
}


function watch_allres(callback) {

  if (!fs.existsSync(RES_INFO_PATH)) {
    global.log.info("no res exists, stop watching res");
    return;
  }

  global.res_info_collection.find({}, function(err, docs) {
    if (err)
      global.log.info(err.message);
    global.roots = global.roots || {}; // collect rootdir
    docs.forEach(function(doc) {
      //global.log.info(JSON.stringify(doc));
      fs.exists(doc.path, function(exists) {
        if (exists) {
          if (!('rootdir' in doc)) {
            global.log.info("start watching file:", doc.path);
            utils.createMonitor(doc, global.monitors, callback);
          } else {
            // res has rootdir field, don't watch file but rootdir
            if (!global.roots[doc.rootdir]) {
              utils.myWatchTree(doc.rootdir);
            }
            global.roots[doc.rootdir] = true;
          }
        } else {
          // file deleted but record left in db
        }
      });
    });
  });
}

function insertResource(fileHash, filePosition, callback, isDir) {
  fs.exists(filePosition, function(exists) {
    if (exists) {
      utils.store_res_hash_download(filePosition, fileHash, settings.seed, function(isRight, newDoc) {
        if (isRight) {
          if (isDir) {
            global.roots = global.roots || {};
            var rootdir = fbtUtils.fbtNormalize(path.dirname(filePosition));
            utils.store_res_info_in_folder(filePosition, rootdir);
            if (rootdir in global.roots) {
              watch.unwatchTree(rootdir);
              setTimeout(function(){
                utils.myWatchTree(rootdir);
              }, 200);
            } else {
              utils.myWatchTree(rootdir);
              global.roots[rootdir] = true;
            }
          } else {
            utils.store_res_info(filePosition, global.monitors);
            var xxfileHash = newDoc.verify;
            global.log.info("downloadfile hash: " + newDoc.verify);
            if (xxfileHash != fileHash) {
              global.log.warn("downloaded file hash and xxhash is different:" + filePosition);
            }
          }
          callback(true);
        } else {
          callback(false);
        }
      });
      //global.resourceDB[fileHash]=filePosition;
    } else {
      //impossiable error
      throw Error("file position not exist. fileHash:" + fileHash + " filePosition:" + filePosition);
    }
  });
}

function get_parts_left(hash, callback) {
  global.parts_left_collection.findOne({
      hash: parseInt(hash)
    },
    function(err, doc) {
      if (err) {
        global.log.error(err);
      }
      callback(doc ? doc.parts_left : null);
    }
  );
}

function update_parts_left(hash, parts_left) {
  parts_left = parts_left.concat();
  global.parts_left_collection.update({
      hash: parseInt(hash)
    }, {
      $set: {
        parts_left: parts_left
      }
    }, {
      'multi': true,
      'upsert': true
    },
    function(err, numReplaced) {
      if (numReplaced !== 1) {
        global.log.info("found duplicate parts_left docs");
      }
      if (numReplaced > 1) {
        global.log.info("dups in update_parts_left: " + numReplaced);
      }
    }
  );
}

function remove_record_from_parts_left(hash) {
  global.parts_left_collection.remove({
      hash: parseInt(hash)
    }, {
      'multi': true
    },
    function(err, numReplaced) {
      if (numReplaced === 0) {
        global.log.info("no such record in parts_left");
      }
      if (numReplaced > 1) {
        global.log.info("dups in remove_record: " + numReplaced);
      }
    }
  );
}

function remove_part_from_parts_left(hash, indexOrIndexArray, downloadOver) {
  if (nodeUtil.isArray(indexOrIndexArray)) {
    indexOrIndexArray = indexOrIndexArray.concat();
    global.parts_left_collection.update({
        hash: parseInt(hash)
      }, {
        $pull: {
          parts_left: {$in: indexOrIndexArray}
        }
      }, {
        'multi': true
      },
      function (err, numReplaced) {
        if (numReplaced === 0) {
          global.log.warning("no such record in parts_left");
        }
        if (numReplaced > 1) {
          global.log.warning("dups in remove_parts: " + numReplaced);
        }
        if (downloadOver) {
          global.parts_left_collection.persistence.compactDatafile();
        }
      }
    );
  } else if (typeof(indexOrIndexArray) === 'number') {
    global.parts_left_collection.update({
        hash: parseInt(hash)
      }, {
        $pull: {
          parts_left: indexOrIndexArray
        }
      }, {
        'multi': true
      },
      function (err, numReplaced) {
        if (numReplaced === 0) {
          global.log.warning("no such record in parts_left");
        }
        if (numReplaced > 1) {
          global.log.warning("dups in remvoe_parts: " + numReplaced);
        }
        if (downloadOver) {
          global.parts_left_collection.persistence.compactDatafile();
        }
      }
    );
  } else {
    global.log.error("Wrong indexOrIndexArray type: " +
                    typeof(indexOrIndexArray));
  }
}

function get_uploaders(hash, callback) {
  global.parts_left_collection.findOne({
      hash: parseInt(hash)
    },
    function(err, doc) {
      if (err) {
        global.log.error(err);
      }
      callback(doc ? doc.uploaders : null);
    });
}

function record_uploader(hash, uploader_id) {
  global.parts_left_collection.update({
      hash: parseInt(hash)
    }, {
      $addToSet: {
        uploaders: uploader_id
      }
    }, // append to Array
    {
      'multi': true,
      'upsert': true
    },
    function(err, numReplaced) {
      if (numReplaced !== 1) {
        global.log.info("found duplicate parts_left docs");
      }
      if (numReplaced > 1) {
        global.log.warning("dups in record_uploader: " + numReplaced);
      }
    }
  );
}

function BatchUploader(fileCount, files, size, hashOneOverCallback, uploadDir, files_tobe_unwatch, upload_id) {
  this.fileCount = fileCount;
  this.files = files;
  this.size = size;
  this.hashOneOverCallback = hashOneOverCallback;
  this.uploadDir = uploadDir;
  this.finishHashCount = 0;
  this.files_tobe_unwatch = files_tobe_unwatch;
  this.index = 0;
  this.hash = 0;
  this.file = 0;
  this.upload_id = upload_id;
}

BatchUploader.allObj = {};
BatchUploader.prototype.addSingleRes = function() {
  if (this.index > this.fileCount - 1) return;
  var file = this.files[this.index];
  var that = this;
  var hashvalue;
  try {
    var hasher = new xxhash(settings.seed);
    fs.createReadStream(file)
      .on('data', function(data) {
        hasher.update(data);
      })
      .on('end', function() {
        global.log.info("hash finish: ", file);
        hashvalue = parseInt(hasher.digest());
        that.hash = hashvalue;
        that.hashOneOverCallback({
            'path': fbtUtils.fbtNormalize(file),
            'verify': hashvalue
          },
          that.size[file], that.store_res_in_folder, that.upload_id
        );
      });
  } catch (err) {
    global.log.info(err.message);
  }
};

BatchUploader.prototype.store_res_in_folder = function(upload_id) {
  var that = BatchUploader.allObj[upload_id];
  var f = that.files[that.index];
  utils.store_res_info_in_folder(f, that.uploadDir);
  global.res_hash_collection.update({
      'path': fbtUtils.fbtNormalize(f)
    }, {
      'path': fbtUtils.fbtNormalize(f),
      'verify': that.hash
    }, {
      'multi': true,
      'upsert': true
    },
    function(err, numReplaced) {
      if (numReplaced !== 1) {
        global.log.info("found duplicate hash docs when storing");
      }
    }
  );
  that.finishHashCount++;
  if (that.fileCount === that.finishHashCount) {
    // hash finish, start watching files
    // first, unwatch files_tobe_unwatch
    global.log.info('files_tobe_unwatch:\n' + that.files_tobe_unwatch.join('\n'));
    that.files_tobe_unwatch.forEach(function(filepath) {
      watch.unwatchTree(path.dirname(filepath));
      delete global.monitors[filepath];
    });
    // then watch tree
    utils.myWatchTree(that.uploadDir);
    delete BatchUploader.allObj[upload_id];
    delete that.fileCount;
    delete that.files;
    delete that.size;
    delete that.hashOneOverCallback;
    delete that.uploadDir;
    delete that.finishHashCount;
    delete that.files_tobe_unwatch;
    delete that.index;
    delete that.hash;
    delete that.file;
    return;
  }
  that.index++;
  that.addSingleRes();
};

function batchUpload(uploadDir, hashOneOverCallback, notifyCallback, upload_id) {
  /*
   批量上传文件
   统计完文件数量之后就调用notifyCallback,告知上层文件是否超过 Limit
   hash完一个文件调用hashOneOverCallback
   */
  var fileCount = 0;
  var files = [];
  var size = {};

  filewalker(uploadDir)
    .on('file', function(p, s, ap) {
      // don't upload file which has already been uploaded or downloaded
      if (global.res_list.indexOf(fbtUtils.fbtNormalize(ap)) !== -1) return;
      // ignore hidden files (filename start with dot)
      if (path.basename(p)[0] !== '.') {
        fileCount++;
        files.push(ap);
        size[ap] = s.size;
      }
    })
    .on('error', function(err) {
      global.log.error('error batch uploading');
      global.log.error(err);
    })
    .on('done', function() {
      if (fileCount > 500) {
        notifyCallback(true, fileCount); // too many files
        global.log.error('Too many files in directory, batch upload fail');
        return;
      } else {
        notifyCallback(false, fileCount);
      }
      // sort files according to name, TODO: apply sort function using basename
      files.sort();

      global.res_info_collection.find({}, function(err, docs) {
        /*
         there are files in uploadDir that have been uploaded before,
         set a 'rootdir' field for those files (rootdir=uploadDir),
         next time FBT launchs, we know those files are in uploadDir,
         thus we only need to watch uploadDir instead of watching files respectively.
         */
        var files_tobe_unwatch = [];
        docs.forEach(function(doc) {
          if (doc.path.indexOf(uploadDir) !== -1) {
            files_tobe_unwatch.push(doc.path);
            global.res_info_collection.update({
                path: doc.path
              }, {
                $set: {
                  'rootdir': uploadDir
                }
              }, {},
              function(err, numReplaced) {
                if (err)
                  global.log.error('update doc error', err.message);
                else if (numReplaced > 1)
                  global.log.warning('found duplicate doc when updating');
                else if (numReplaced === 0)
                  global.log.warning('missing doc when updating');
                else
                  global.log.info('update root:', doc.path, '\nnew root:', uploadDir);
              }
            );
          }
        });
        var u = new BatchUploader(fileCount, files, size, hashOneOverCallback, uploadDir, files_tobe_unwatch, upload_id);
        BatchUploader.allObj[upload_id] = u;
        u.addSingleRes();
      });
    })
    .walk();
}

function dirUpload(uploadDir, upload_id, hashOverCallback) {
  /*
   upload directory, different from batchUpload
   */
  //global.window.console.log("call dirUpload");
  uploadDir = fbtUtils.fbtNormalize(uploadDir);   // unify Windows drive letter
  var fileCount = 0;
  var files = [];
  var size = {};
  var uploadFileInfo = [];
  var fileTotalBytes = 0;
  var uploadError = false; // if upload has error
  filewalker(uploadDir)
    .on('file', function(p, s, ap) {
      //global.window.console.log("found file: " + ap);
      if (global.res_list.indexOf(fbtUtils.fbtNormalize(ap)) !== -1) return;
      if (path.basename(p)[0] !== '.') {
        fileCount++;
        files.push(ap);
        if (s.size === 0) {
          uploadError = "size0";
        }
        size[ap] = s.size;
        fileTotalBytes += s.size;
      }
    })
    .on('dir', function(p){
      uploadError = "subdir";   // don't allow subdir
    })
    .on('error', function(err) {
      global.log.error('error directory uploading');
      global.log.error(err);
    })
    .on('done', function() {
      var ret;
      if (uploadError === "size0") {
        ret = {
          "type": 1,
          "error": "不能上传大小为0的资源！！",
          "id": upload_id
        };
        global.socket.emit("upload", JSON.stringify(ret));
        return; // if error occurs, stop upload
      }
      if (uploadError === "subdir") {
        ret = {
          "type": 1,
          "error": "文件夹中不能包含子文件夹！！",
          "id": upload_id
        };
        global.socket.emit("upload", JSON.stringify(ret));
        return; // if error occurs, stop upload
      }
      if (fileCount > 500) {
        hashOverCallback("exceed_limit");
        global.log.error('Too many files in directory, dir upload fail');
        return;
      }
      // sort files according to name, TODO: apply sort function using basename
      files.sort();

      global.res_info_collection.find({}, function(err, docs) {
        var files_tobe_unwatch = [];
        var userDirId = null;
        docs.forEach(function(doc) {
          if (doc.path.indexOf(uploadDir) !== -1) {
            files_tobe_unwatch.push(doc.path);
            if ('userDirId' in doc) {
              userDirId = doc.userDirId;  // I've uploaded this folder before
            }
            global.res_info_collection.update({
                path: doc.path
              }, {
                $set: {
                  'rootdir': uploadDir,
                  'isFolderRes': true
                }
              }, {},
              function(err, numReplaced) {
                if (err)
                  global.log.error('update doc error', err.message);
                else if (numReplaced > 1)
                  global.log.warning('found duplicate doc when updating');
                else if (numReplaced === 0)
                  global.log.warning('missing doc when updating');
                else
                  global.log.info('update root:', doc.path, '\nnew root:', uploadDir);
              }
            );
          }
        });
        /*
         阻止用户上传他下载的文件夹
         如果文件是文件夹中的文件, 且userDirId 不存在, 那么说明该文件夹是下载的别人的,
         这时不允许上传
         如何知道一个文件夹是新上传的。利用global.roots
         global.roots = global.roots || {};
         起始/下载/上传 都会更新global.roots
         */
        if (uploadDir in global.roots) {  // if not, is a new folder
          if (userDirId == null) {
            ret = {
              "type": 1,
              "error": " 不允许上传下载的文件夹！！",
              "id": upload_id
            };
            global.socket.emit("upload", JSON.stringify(ret));
            return;
          }
        } else {
          require('assert').equal(userDirId, null,
            "userDirId should be null if folder hasn't been uploaded before");
          userDirId = global.uid + '_' + (new Date()).getTime();
        }

        var hashProgress = 0;
        var hashedFileCount = 0;
        async.eachSeries(files, function(file, callback) {
          var hasher = new xxhash(settings.seed);
          try {
            fs.createReadStream(file)
              .on('data', function(data) {
                hasher.update(data);
              })
              .on('end', function() {
                global.log.info("hash finish: ", file);
                var hashvalue = parseInt(hasher.digest());
                uploadFileInfo.push({
                  name: path.basename(file),
                  path: file,
                  hash: hashvalue,
                  size: size[file]
                });
                hashedFileCount++;
                if (hashedFileCount == files.length) {
                  hashProgress = "99%";
                } else {
                  hashProgress = hashedFileCount / files.length;
                  hashProgress = (100 * hashProgress).toFixed(2) + '%';
                }
                global.socket.emit("upload", JSON.stringify({
                  "id": upload_id, "type":3, "progress": hashProgress
                }));
                setImmediate(function() { // free memory
                  callback();
                });
              });
          } catch (e) {
            setImmediate(function() { // free memory
              callback(e.message);
            });
          }
        }, function(err) {
          if (err) {
            global.log.info("A file failed to process when dir uploading");
            global.log.info(err);
            hashOverCallback(err);
          } else {
            global.log.info('files_tobe_unwatch:\n' + files_tobe_unwatch.join('\n'));
            files_tobe_unwatch.forEach(function(filepath) {
              watch.unwatchTree(path.dirname(filepath));
              if (filepath in global.monitors) {
                global.monitors[filepath].stop();
                setTimeout(function(){
                  delete global.monitors[filepath];
                }, 2000);
              }
            });

            hashOverCallback(null, uploadFileInfo, userDirId, function() {
              global.roots = global.roots || {};
              global.roots[uploadDir] = true;
              utils.myWatchTree(uploadDir, files);
              var hash_docs = [];
              var info_docs = [];
              uploadFileInfo.forEach(function(fileInfo) {
                var stats = fs.statSync(fileInfo.path);
                info_docs.push({
                  'name': fileInfo.name,
                  'rootdir': uploadDir,
                  'isFolderRes': true,
                  'userDirId': userDirId,
                  'path': fbtUtils.fbtNormalize(fileInfo.path),
                  'size': stats['size'],
                  'mtime': stats['mtime'].getTime()
                });
                hash_docs.push({
                  'path': fbtUtils.fbtNormalize(fileInfo.path),
                  'verify': fileInfo.hash
                })
              });
              // No file is in db since res_list checking assures this
              global.res_info_collection.insert(info_docs, function(err) {
                if (err) {
                  global.log.error('dirUpload store to res_info error:', err);
                }
              });
              global.res_hash_collection.insert(hash_docs, function(err) {
                if (err) {
                  global.log.error('dirUpload store to res_hash error:', err);
                }
              })
            });
          }
        });
      });
    })
    .walk()
}

function changeResLocation(isDir, oldPath, newPath, oldRootdir, newRootdir) {
  /*
  1. 数据库update
  2. unwatch/watch
  isDir=true，oldPath和newPath都必须是array，是文件夹中所有文件的路径列表
  isDIr=false, oldPath和newPath就是普通字符串
   */
  console.assert(path.basename(oldPath) == path.basename(newPath), "移动位置后文件名不同！");

  if (isDir) {
    console.assert(oldPath.length == newPath.length, "路径列表长度不同！");
    for (var i=0; i<oldPath.length; i++) {
      utils.updateResPath(oldPath[i], newPath[i], oldRootdir, newRootdir);
    }
    watch.unwatchTree(oldRootdir);
    setTimeout(function(){
      utils.myWatchTree(newRootdir, newPath);
    }, 2000);
  } else {
    // 非文件夹文件的watch更新放在updateResPath里，因为需要doc
    utils.updateResPath(oldPath, newPath);
  }
}

exports.insertResource = insertResource;
exports.get_path_from_hash = get_path_from_hash;
exports.get_res_hash = get_res_hash;
exports.add_res_upload = add_res_upload;
exports.get_res_info = get_res_info;
exports.get_allres_info = get_allres_info;
exports.get_allres_hash = get_allres_hash;
exports.getPathUsingHashAndSize = getPathUsingHashAndSize;
exports.remove_res = remove_res;
exports.check_allres_update = check_allres_update;
exports.watch_allres = watch_allres;
exports.update_parts_left = update_parts_left;
exports.get_parts_left = get_parts_left;
exports.get_uploaders = get_uploaders;
exports.remove_record_from_parts_left = remove_record_from_parts_left;
exports.remove_part_from_parts_left = remove_part_from_parts_left;
exports.record_uploader = record_uploader;
exports.batchUpload = batchUpload;
exports.dirUpload = dirUpload;
exports.get_res_size = get_res_size;