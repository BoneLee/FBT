var paths = require('path');
var io = require(paths.join(global.exec_path, 'socket.io-client'));

/*
 * chatRoom settings
 */
var chatRoom = {};
chatRoom.JOIN = 'JOIN'; // clients join chatroom
chatRoom.SEND = 'SEND'; // client sends message to server
chatRoom.RECV = function(uid) {
  return 'RECV' + uid;
}; // server turns message to specified client
chatRoom.NOTE = function(uid) {
  return 'NOTE' + uid; // server sends message to specified client
};

/*
 * chatRoomTalker defination
 */
var chatRoomTalker = module.exports = function(crAddress, uid) {
  this.crAddress = crAddress;
  this.uid = uid;
  this.socket = io.connect(crAddress);
  this.socket.emit(chatRoom.JOIN, this.uid);

  var that = this;
  this.socket.on(chatRoom.RECV(uid), function(talk) {
    that.onMessage(talk.sUid, talk.message);
  });
  this.socket.on(chatRoom.NOTE(uid), function(note) {
    var error = note;
    that.onError(error);
  });

  this.socket.on('disconnect', function() {
    global.log.info('Disconnect');
  });
};


chatRoomTalker.prototype.send = function(dUid, message) {
  var talk = {
    sUid: this.uid,
    dUid: dUid,
    message: message
  };
  this.socket.emit(chatRoom.SEND, talk);
};


chatRoomTalker.prototype.onMessage = function(sUid, message) {
  global.log.info('Override chatRoomTalker onMessage method');
  process.exit(1);
};


chatRoomTalker.prototype.onError = function(error) {
  global.log.info('Override chatRoomTalker onError method');
  process.exit(1);
};
