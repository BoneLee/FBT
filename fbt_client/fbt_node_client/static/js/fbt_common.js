function getFilename() {
    var filePath = $("#upload_panel").attr('data');

    if (!filePath) {
        $('#resourceEnName').val("请选择分享的文件，便于为您提取0day命名");
        return;
    }
    var idx1 = filePath.lastIndexOf('/') + 1;
    var idx2 = filePath.lastIndexOf('\\') + 1;
    idx1 = idx1 > idx2 ? idx1 : idx2;
    if (idx1 < 0) idx1 = 0;
    var filename = filePath.substring(idx1);
    $('#resourceEnName').empty();
    $('#resourceEnName').val(filename);
    /*var chEng = lenOfChAndEng(filename);
    if (chEng[0] > 0) {
        $('#resourceEnName').val("资源0day命名含有中文字符，请检查是否正确");
    }*/
}
function getResourceType(mainType, subType) {
    var resourceMainType = {
      0: "电影",
      1: "剧集",
      2: "学习",
      3: "音乐",
      4: "动漫",
      5: "游戏",
      6: "综艺",
      7: "体育",
      8: "软件",
      9: "其它"
    };
    var resourceSubType = {
      0: "标清",
      1: "高清",
      2: "超高清"
    };
    var type = [0, 1, 3, 4, 6, 7];
    if ((mainType in type) && (subType >= 0 && subType <= 2)) {
      return resourceMainType[mainType] + " " + resourceSubType[subType];
    } else {
      return resourceMainType[mainType];
    }
}

function checkTime(i) {
    if (i < 10)
      i = "0" + i;
    return i;
}

function toLocalTime(utcSeconds) {
  //var utcSeconds = 1234567890;
  var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
  if (!utcSeconds) {
    return "未知时间";
  }
  d.setUTCSeconds(parseInt(utcSeconds));
  var month = checkTime(d.getMonth() + 1); //Months are zero based
  var year = d.getFullYear();
  var day = checkTime(d.getDate());
  /*var hour = checkTime(d.getHours());
  var minute = checkTime(d.getMinutes());
  var second = d.getSeconds();*/
  return year + "-" + month + "-" + day;
}
function checkMainType(mType){
  if(mType == 0 || mType == 1 || mType == 4 || mType == 6)
    return true;
  return false;
}
function preHandleRes(res, shouldDecrypt){
  for (var i = 0; i < res.length; i++) {
    res[i]["resType"] = getResourceType(res[i]['main_type'],res[i]['sub_type']);
    res[i]["time"] = toLocalTime(res[i]['mtime']);
    if(checkMainType(res[i]['main_type']) && "ext_info" in res[i] && 'link' in res[i]['ext_info']){
      if(res[i]['ext_info']["link"].indexOf("?") > 0)
        res[i]["link"] = res[i]['ext_info']["link"]+"&type="+res[i]['main_type'];
      else
        res[i]["link"] = res[i]['ext_info']["link"]+"?type="+res[i]['main_type'];
    }
    else
      res[i]["link"] = "images/file_type/"+res[i]['main_type']+".png";
    if(res[i]["file_hashes"]){
      res[i]["isDir"] = true;
    }
    else
      res[i]["isDir"] = false;
  }
  if(shouldDecrypt){
    for (var i = 0; i < res.length; i++) {
      res[i]["file_name"] = waveDecrypt(res[i]["file_name"]);
      res[i]["tags"] = waveDecrypt(res[i]["tags"]);
    }
  }
}
function resizeImage(fileToUpload, callback) {
    var file = fileToUpload;
    var img = document.createElement("img");
    var reader = new FileReader();
    reader.onload = function(e)
    {
        img.src = e.target.result;
        var canvas = document.createElement("canvas");
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        var MAX_WIDTH = 70;
        var MAX_HEIGHT = 70;
        var width = img.width;
        var height = img.height;
        if (width > height) {
          if (width > MAX_WIDTH) {
            height *= MAX_WIDTH / width;
            width = MAX_WIDTH;
          }
        } else {
          if (height > MAX_HEIGHT) {
            width *= MAX_HEIGHT / height;
            height = MAX_HEIGHT;
          }
        }
        canvas.width = width;
        canvas.height = height;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        var dataurl = canvas.toDataURL("image/png");
        //document.getElementById('image').src = dataurl;     
        //console.log(dataurl);
        callback(dataurl);
    }
    reader.readAsDataURL(file);
}
function waveDecrypt(str){
    return str.split('~').join('');
}
function gen_file_id(file_hash, file_size){
    return file_hash + "_" + file_size;
}
function normalizeFileSize(fileSize){
    fileSize = window.parseInt(fileSize);
    if (fileSize<1024)
        return fileSize+"B";
    else if (fileSize<1024*1024)
        return (fileSize/1024).toFixed(0) + "KB";
    else{
        if (fileSize<1024*1024*1024)
            return (fileSize/1024/1024).toFixed(1) + "MB";
        else
            return (fileSize/1024/1024/1024).toFixed(2) + "GB";
    }
}
function updateProgressBarMessage(hash, msg, size) {
  
}
var common_html_0 = "<div id='upload_exp_info' style='margin-bottom:5px'><div class='col-xs-9'><p style='margin:0 0 3px;font-size:14px'>年份：",
common_html_1 = "</p><p style='margin:0 0 3px;font-size:14px'>国家：",
common_html_2 = "</p><p style='margin:0 0 3px;font-size:14px'>简介：",
common_html_3 = "</p></div><img style='float:right;width:100px;height:147px;margin-right:15px' src='",
common_html_4 = "'/></div>";
function executeScript(html)
{
  var reg = /<script[^>]*>([^\x00]+)$/i;
  //对整段HTML片段按<\/script>拆分
  var htmlBlock = html.split("<\/script>");
  for (var i in htmlBlock)
  {
    var blocks;//匹配正则表达式的内容数组，blocks[1]就是真正的一段脚本内容，因为前面reg定义我们用了括号进行了捕获分组
    if( (blocks = htmlBlock[i].match(reg)) )
    {
      //清除可能存在的注释标记，对于注释结尾-->可以忽略处理，eval一样能正常工作
      var code = blocks[1].replace(/<!--/, '');
      try
      {
        eval(code); //执行脚本
      }
      catch (e)
      {
      }
    }
  }
}
function htmlencode(s){  
    var div = document.createElement('div');  
    div.appendChild(document.createTextNode(s));  
    return div.innerHTML;  
}
function getCookie(name) {
  var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
  return r ? r[1] : undefined;
}

function getJsonLength(jsonData){

  var jsonLength = 0;

  for(var item in jsonData){

    jsonLength++;

  }

  return jsonLength;

}

function changeCursor(){
    document.body.style.cursor="default";
}

function clearCookie(){
    var keys=document.cookie.match(/[^ =;]+(?=\=)/g);
    if (keys) {
        for (var i =  keys.length; i--;)
            document.cookie=keys[i]+'=0;expires=' + new Date( 0).toUTCString()
    }    
}

Date.prototype.Format = function(fmt)   
{ //author: meizz   
  var o = {   
    "M+" : this.getMonth()+1,                 //月份   
    "d+" : this.getDate(),                    //日   
    "h+" : this.getHours(),                   //小时   
    "m+" : this.getMinutes(),                 //分   
    "s+" : this.getSeconds(),                 //秒   
    "q+" : Math.floor((this.getMonth()+3)/3), //季度   
    "S"  : this.getMilliseconds()             //毫秒   
  };   
  if(/(y+)/.test(fmt))   
    fmt=fmt.replace(RegExp.$1, (this.getFullYear()+"").substr(4 - RegExp.$1.length));   
  for(var k in o)   
    if(new RegExp("("+ k +")").test(fmt))   
  fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));   
  return fmt;  
}
function clone(obj){
    var objClone = {};
    for(var key in obj){
        objClone[key] = obj[key];
    }
    return objClone;
}
/*Object.prototype.Clone = function(){
    var objClone;
    if (this.constructor == Object){
        objClone = {}; 
    }else{
        objClone = []; 
    }
    for(var key in this){
        if ( objClone[key] != this[key] ){ 
            if ( typeof(this[key]) == 'object' ){ 
                objClone[key] = this[key].Clone();
            }else{
                objClone[key] = this[key];
            }
        }
    }
    objClone.toString = this.toString;
    objClone.valueOf = this.valueOf;
    return objClone; 
} */
if(typeof(String.prototype.trim) === "undefined")
{
  String.prototype.trim = function() 
  {
      return String(this).replace(/^\s+|\s+$/g, '');
  };
}

function lenOfChAndEng(temp) {
    var lenCh = 0;
    var lenEng = 0;
    for (var i = 0; i < temp.length; i++) {
        var ch = temp.charAt(i);
        if (ch > '\u4e00' && ch < '\u9fa5') {
            lenCh++;
        }
        if (/[a-zA-z]/.test(ch)) {
            lenEng++;
        }
    }
    return [lenCh, lenEng];
}
function isChinese(temp)  
{  
    var re = /[^\u4e00-\u9fa5]/;  
    if(re.test(temp)) 
        return false;  
    return true;  
}
 
//toast
function noCb(){}

/*var w;

function startWorker()
{
if(typeof(Worker)!=="undefined")
{
  if(typeof(w)=="undefined")
    {
    w=new Worker("demo_workers.js");
    }
  w.onmessage = function (event) {
    document.getElementById("result").innerHTML=event.data;
  };
}
else
{
document.getElementById("result").innerHTML="Sorry, your browser
 does not support Web Workers...";
}
}

function stopWorker()
{
w.terminate();
}*/
