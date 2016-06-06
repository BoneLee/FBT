var path = require('path');

global.exec_path = path.join(path.dirname(__dirname), 'node_modules');
var urllib =  require(path.join(global.exec_path, 'urllib'));

(function test(){
  var testImageUrl = "http://fbt-image.b0.upaiyun.com/sync/test.png";
  urllib.request(testImageUrl, {}, function(err, data, res){
    console.log("res.status should be 403: ", res.status);

    var imageUrlWithToken = require('../fbtUtils/upyun').getUpyunToken(testImageUrl);

    urllib.request(imageUrlWithToken, {}, function(err, data, res) {
      console.log("res.status should be 200: ", res.status);
    });
  });

  testImageUrl = "/sync/test.png";
  var imageUrlWithToken = require('../fbtUtils/upyun').getUpyunToken(testImageUrl);

  urllib.request(imageUrlWithToken, {}, function(err, data, res) {
    console.log("res.status should be 200: ", res.status);
  });
})();
