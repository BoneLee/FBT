var tcpServer = require("./tcpFileServer");

function runAt(host, port, config) {
  if('resourceDB' in config){
      tcpServer.setResourceDB(config['resourceDB']);
  }
  tcpServer.startServer(host, port, config);
}

exports.runAt = runAt;
exports.getDownloadingFiles = function() {
    return tcpServer.getDownloadingFiles();
};