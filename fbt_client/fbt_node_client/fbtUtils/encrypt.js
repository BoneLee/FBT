var crypto = require('crypto');

var secretKey = new Buffer('GFW吃屎！GFW吃屎！GFW吃屎！GFW吃屎！').slice(0,32);//32 bytes
var cryptype='aes-256-cbc'; //'aes-128-ecb'
var dataType='base64';

function generateIV(){
    return new Buffer(Date.now().toString()+Date.now().toString()).slice(0,16);
}

function encrypt(text) {
    var iv=generateIV();
    var cipher = crypto.createCipheriv(cryptype,secretKey,iv);
    return iv+cipher.update(text,'utf8',dataType) + cipher.final(dataType);
}

function decrypt(text) {
    var iv=text.substr(0,16);
    var cipher = crypto.createDecipheriv(cryptype,secretKey,iv);
    return cipher.update(text.substr(16),dataType,'utf8') + cipher.final('utf8');
}

function utf8ToBase64(text){
  return new Buffer(text,'utf8').toString('base64');
}

function base64ToUtf8(text){
  return new Buffer(text,'base64').toString('utf8');
}

function utf8ToArray(str){
  var utf8 = unescape(encodeURIComponent(str));
  var arr = [];
  for (var i = 0; i < utf8.length; i++) {
    arr.push(utf8.charCodeAt(i));
  }
  return arr;
}


function arrayToUtf8(arr){
  var buf=[];
  for (var i = 0; i < arr.length; i++) {
    buf.push(String.fromCharCode(arr[i]));
  }
  str=buf.join('');
  return decodeURIComponent(escape(str));
}

function xorEncrypt(str) {
    var buf=new Buffer(str,'utf8');
    for (var i=0; i<buf.length;i++) {
        buf[i]^=123;
    }
    return buf.toString('base64');
}

function xorDecrypt(str) {
    var buf=new Buffer(str,'base64');
    for(var i=0;i<buf.length;++i){
        buf[i]^=123;
    }
    return buf.toString('utf8');

    /*
    下面的代码能够工作，但是并不正确！
    理由很简单，"你好".length=2，实际上应该是6，用new Buffer("你好").length==6
    str=base64ToUtf8(str);
    var encoded = "";
    for (i=0; i<str.length;i++) {
        var a = str.charCodeAt(i);
        var b = a ^ 123;    // bitwise XOR with any number, e.g. 123
        encoded = encoded+String.fromCharCode(b);
    }
    return encoded;
    */
}

function waveEncrypt(str){
    return str.split('').join('~')
    /*
    var encoded = "~";
    for (i=0; i<str.length;i++) {
        if(str[i]=='~') throw new Error("~ is not allowed");
        encoded = encoded+str[i]+"~";
    }
    return encoded;
    */
}

function replaceAll(str, search, replacement){
    return str.split(search).join(replacement)
}

function waveDecrypt(str){
    return str.split('~').join('');
}

/*
exports.encrypt = encrypt;
exports.decrypt =  decrypt;
exports.xorEncrypt =  xorEncrypt;
exports.xorDecrypt =  xorDecrypt;
exports.waveEncrypt =  waveEncrypt;
exports.waveDecrypt =  waveDecrypt;
*/

exports.encrypt = waveEncrypt;
exports.decrypt =  waveDecrypt;

//console.log(xorEncrypt('FBT架构.png')); //PTkvneXNneX/VQsVHA==
//console.log(xorDecrypt('PTkvneXNneX/VQsVHA=='));

//console.log(waveEncrypt('FBT架构.png')); //PTkvneXNneX/VQsVHA==
//console.log(waveDecrypt('~F~B~T~架~构~.~p~n~g~'));
//console.log(waveEncrypt('FBT~架构.png')); //PTkvneXNneX/VQsVHA==
//console.log(waveDecrypt('~F~B~T~架~构~.~p~n~g~'));
