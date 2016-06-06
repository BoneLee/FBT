//try {
//    require('nw.gui').Window.get().showDevTools();
//}
//catch(e){
//
//}


var res_api = require('./res_api'),
    utils = require('./utils');

function init(fileChangeCallback) {
  global.res_list = [];
  global.monitors = {};  // {path1: monitor1, path2: monitor2}
  res_api.check_allres_update();
  res_api.watch_allres(fileChangeCallback);
}


function clear() {
  utils.clear_db(global.monitors);
  console.log("all cleared");
}

exports.init = init;
exports.clear = clear;
