var path = require('path');
var md5 = require(path.join(global.exec_path, 'MD5'));


function getUpyunToken(imageUrl) {
  /*
  生成带token的外链, 限制黑客对图片的访问
   */
  var oriImageUrl;
  if (imageUrl.indexOf('.com') != -1) {
    oriImageUrl = imageUrl;
    imageUrl = imageUrl.substr(imageUrl.indexOf('.com') + 4);
  } else {
    if (imageUrl.charAt(0) != '/') {
      imageUrl = '/' + imageUrl;
    }
    oriImageUrl = "http://fbt-image.b0.upaiyun.com" + imageUrl;
  }
  var key = 'fbt';
  // 获取当前 Unix 时间，并且设定过期时间为10min
  var etime = parseInt(Date.now() / 1000) + 600;
  // 生成 MD5
  var tokensign = md5(key + '&' + etime + '&' + imageUrl);

  // 截取32位MD5的中间八位，拼接生成 token
  var token = '_upt=' + tokensign.substring(12, 20) + etime;
  if(oriImageUrl.indexOf("?") > 0)
    return oriImageUrl + "&" +token;
  else
    return oriImageUrl + "?" +token;
}

exports.getUpyunToken = getUpyunToken;


