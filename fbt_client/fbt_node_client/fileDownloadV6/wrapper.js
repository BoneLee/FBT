var server = require("./server");
var router = require("./router");
var requestHandlers = require("./requestHandlers");

var handle = {};
handle["/about"] = requestHandlers.about;
//use xxxxxx/download?file=filename&size=filesize&hash=filehash to download file
handle["/download"] = requestHandlers.downloadFile;
//such as: http://192.168.1.107:8887/download?file=stallman.jpg&size=46311&hash=789
//with ipv6: http://[::1]:8886/download?file=stallman.jpg&size=46311&hash=789
//server.start(router.route, handle, '::', 8887);

function runAt(host, port, config) {
  if('resourceDB' in config){
      requestHandlers.setResourceDB(config['resourceDB']);
  }
  server.start(router.route, handle, host, port, config);
}

exports.runAt = runAt;
exports.getDownloadingFiles = function() {
    return requestHandlers.getDownloadingFiles();
};