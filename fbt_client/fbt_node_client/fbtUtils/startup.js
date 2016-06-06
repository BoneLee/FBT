var fbtLogger=require('fs').createWriteStream('fbt.log');
process.fbtLoggerut.write=function(string, encoding, fd) {fbtLogger.write(string);};
