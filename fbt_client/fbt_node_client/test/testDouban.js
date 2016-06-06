var path = require('path');
var fs = require('fs');

global.exec_path = path.join(path.dirname(__dirname), 'node_modules');

var Log = require('log')
global.log = new Log('debug', fs.createWriteStream('douban.log'));

(function test(){
  require('../fbtUtils/douban').getInfo("宿醉", function(info){
    console.log(info);

  });
})();
