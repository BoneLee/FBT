function isPrivate(addr) {
  return addr.match(/^10\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
    addr.match(/^192\.168\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
    addr.match(/^172\.(1[6-9]|2\d|30|31)\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
    addr.match(/^127\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
    addr.match(/^169\.254\.([0-9]{1,3})\.([0-9]{1,3})/) != null ||
    addr.match(/^fc00:/) != null || addr.match(/^fe80:/) != null;
}

function isPublic(addr) {
  return !isPrivate(addr);
}

function isLoopback(addr) {
  return /^127\.0\.0\.1/.test(addr)
    || /^fe80::1/.test(addr)
    || /^::1/.test(addr);
}

function address(name, family) {
    if (family !== 'IPv4' && family !== 'IPv6') {
      throw new Error('family must be IPv4 or IPv6');
    }
    if (name !== 'public' && name !== 'private') {
      throw new Error('name must be private or pubic');
    }

    var ipAddresses = [];

    var interfaces = require('os').networkInterfaces();
    for (var devName in interfaces) {
        var iface = interfaces[devName];
        for (var i = 0; i < iface.length; i++) {
            var alias = iface[i];
            if (alias.family == family && !alias.internal && !isLoopback(alias.address)){//NO loopback!NO internal address!
              if(name == 'public' && isPublic(alias.address)){
                ipAddresses.push(alias.address);
              } else if(name == 'private' && isPrivate(alias.address)) {
                ipAddresses.push(alias.address);
              }
            }
        }
    }

    return ipAddresses;
}

//function randomChoose(items){
//	return items[Math.floor(Math.random()*items.length)];
//}

var ipv4addresses=address('private','IPv4');
var ipv6addresses=address('public','IPv6');

//console.log("ipv6addresses:"+ipv6addresses);
//console.log("ipv4addresses:"+ipv4addresses);
//
//var ipv4address = null;
//var ipv6address = null;
//if(ipv4addresses.length >0){
//    ipv4address =randomChoose(ipv4addresses);
//}
//
//if(ipv6addresses.length >0){
//    ipv6address =randomChoose(ipv6addresses);
//}
//
//exports.ipv4address=ipv4address;
//exports.ipv6address=ipv6address;
exports.ipv4addrs=ipv4addresses;
exports.ipv6addrs=ipv6addresses;
