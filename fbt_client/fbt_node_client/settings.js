//205.147.105.205
global.token = "";
exports.token = global.token;

// 修改服务器URL直接切换注释即可

/*exports.url = "http://211.149.202.64:8888/";
exports.host = "211.149.202.64";
exports.origin = "http://211.149.202.64";*/
/*exports.url = "http://211.149.207.145:8888/";
exports.host = "211.149.207.145";
exports.origin = "http://211.149.207.145";*/

exports.url = "http://service.friendsbt.com:8888/";
exports.host = "service.friendsbt.com";
exports.origin = "http://service.friendsbt.com";

exports.port = "8888";

/*exports.url = "http://120.132.66.67:8090/";
exports.host = "120.132.66.67";
exports.origin = "http://120.132.66.67";

exports.port = "8090";*/

exports.upyun = "http://fbt-image.b0.upaiyun.com";
exports.upyun_files = "http://fbt-files.b0.upaiyun.com";
exports.studyHost = "http://xinghuan.com";
exports.studyUrl = "http://xinghuan.com/#/qahome/%E6%A0%A1%E5%9B%AD/1";

var path = require('path');

var RES_INFO_PATH = path.join(global.fbt, "nedb_data",'res_info');
var RES_HASH_PATH = path.join(global.fbt, "nedb_data",'res_hash');
var PARTS_LEFT_PATH = path.join(global.fbt, "nedb_data",'parts_left');
var seed = 0xAAAA;
var BLOCK_SIZE = 4096;  // bytes
var errTips = {
  "duplicatedDownload": 1,
  "historyDownload": 2,
  "spaceFull": 3,
  "invalidOwners": 4,
  "unknown": 5,
  "remove": 6,
  "v4_not_provided": 7,
  "v4_not_allowed": 8,
  "xp_v4": 9,
  "v4_failed": 10,
  "download_dir_create_failed":11,
  "argument_err": 12,
};

exports.RES_INFO_PATH = RES_INFO_PATH;
exports.RES_HASH_PATH = RES_HASH_PATH;
exports.PARTS_LEFT_PATH = PARTS_LEFT_PATH;
exports.seed = seed;
exports.BLOCK_SIZE = BLOCK_SIZE;
exports.errTips = errTips;
