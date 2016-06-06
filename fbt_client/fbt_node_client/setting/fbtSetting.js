/**
 * Created by fbt on 14-7-16.
 */

// loads module and registers app specific cleanup callback...
var cleanup = require('../fbtUtils/cleanUp');
var fs = require('fs');
var path = require('path');
var utils =require('../fbtUtils/fbtUtils');

var config={
  SETTING_FILE:path.join(global.fbt, 'setting.json'),
  HISTORY_FILE:path.join(global.fbt, 'history.json'),
  DIR_FILE:path.join(global.fbt, 'dir.json'),
  HISTORY_FILE_B:path.join(global.fbt, 'history_b.json'),
};//set to current path
if(!global.setInit){
  //var setting={};//not work
  global.setting={};//must use global variable
  global.historys = {}; //save all download history
  global.dir = {}; //all the dir download msg
  loadSetting();
  loadHistory();
  loadDir();
  global.setInit = true;
}

// defines app specific callback...
// place app specific cleanup code here
function settingCleanup() {
  //backup download state
  saveSetting();
  saveHistory();
  saveDir();
  global.log.info('My cleanup...save setting file!');
}
//cleanup.registerClean(settingCleanup);
function loadDir(){
  if (fs.existsSync(config.DIR_FILE)) {
    var data = fs.readFileSync(config.DIR_FILE);
    try{
      global.dir = JSON.parse(data);
    }
    catch(e){
      global.log.info("no dir msg");
    }
  }
}
function saveDir(){
  fs.writeFileSync(config.DIR_FILE, JSON.stringify(global.dir, null, 2));
}
function loadSetting(){
  if (fs.existsSync(config.SETTING_FILE)) {
    var data = fs.readFileSync(config.SETTING_FILE);
    try{
      global.setting = JSON.parse(data);
    }
    catch(e){
      global.log.info("loadSetting json error, recreate");
      global.setting = {};
      var defaultDownloadDir=path.join(utils.getUserHome(),"FBTDownload");
      global.setting["downloadSaveDir"]=defaultDownloadDir;
      global.setting["defaultDownloadDir"]=defaultDownloadDir;
      global.setting["tray"] = 1;
      global.setting["boot"] = 0;
      global.setting["first"] = 1;
      global.setting["s_first"] = 1;
      global.setting["auto_log"] = 0;
      global.setting["allow_bg"] = 1;
      global.setting["allow_v4_download"] = 0;
      global.setting["voice"] = 1;
      global.setting["upload_speed"] = 2097152;
      global.setting["chat_robot"] = 1;
      global.setting["friends_online_inform"] = 1;
      if(!fs.existsSync(defaultDownloadDir)){//mkdir if not exist
          try{
              fs.mkdirSync(defaultDownloadDir);
          }catch(e) {//pass error
          }
      }
      saveSetting();
    }
    if(!("downloadSaveDir" in global.setting)){
      global.setting = {};
      var defaultDownloadDir=path.join(utils.getUserHome(),"FBTDownload");
      global.setting["downloadSaveDir"]=defaultDownloadDir;
      global.setting["defaultDownloadDir"]=defaultDownloadDir;
      global.setting["tray"] = 1;
      global.setting["boot"] = 0;
      global.setting["first"] = 1;
      global.setting["s_first"] = 1;
      global.setting["auto_log"] = 0;
      global.setting["allow_v4_download"] = 0;
      global.setting["allow_bg"] = 1;
      global.setting["voice"] = 1;
      global.setting["upload_speed"] = 2097152;
      global.setting["chat_robot"] = 1;
      global.setting["friends_online_inform"] = 1;
      if(!fs.existsSync(defaultDownloadDir)){//mkdir if not exist
          try{
              fs.mkdirSync(defaultDownloadDir);
          }catch(e) {//pass error
          }
      }
      saveSetting();
    }        
    if(!("auto_log" in global.setting)){
      global.setting["auto_log"] = 0;
    }
    if(!("allow_v4_download" in global.setting)){
      global.setting["allow_v4_download"] = 0;
    }
    if(!("allow_bg" in global.setting)){
      global.setting["allow_bg"] = 1;
    }
    if(!("voice" in global.setting)){
      global.setting["voice"] = 1;
    }
    if(!("upload_speed" in global.setting)){
      global.setting["upload_speed"] = 2097152;
    }
    if(!("chat_robot" in global.setting)){
      global.setting["chat_robot"] = 1;
    }
    if(!("friends_online_inform" in global.setting)){
      global.setting["friends_online_inform"] = 1;
    }
    //global.log.info("loadSetting ok. settings: "+setting);
  }else{//default download dir
    global.log.info("loadSetting");
    var defaultDownloadDir=path.join(utils.getUserHome(),"FBTDownload");
    global.setting["downloadSaveDir"]=defaultDownloadDir;
    global.setting["defaultDownloadDir"]=defaultDownloadDir;
    global.setting["tray"] = 1;
    global.setting["boot"] = 0;
    global.setting["first"] = 1;
    global.setting["s_first"] = 1;
    global.setting["auto_log"] = 0;
    global.setting["allow_v4_download"] = 0;
    global.setting["allow_bg"] = 1;
    global.setting["voice"] = 1;
    global.setting["upload_speed"] = 2097152;
    global.setting["chat_robot"] = 1;
    global.setting["friends_online_inform"] = 1;
    if(!fs.existsSync(defaultDownloadDir)){//mkdir if not exist
        try{
            fs.mkdirSync(defaultDownloadDir);
        }catch(e) {//pass error
        }
    }
    saveSetting();
  }
}
function loadHistory(){
  if (fs.existsSync(config.HISTORY_FILE)) {
    try{
      var data = JSON.parse(fs.readFileSync(config.HISTORY_FILE));
      for(var i in data){
        var item = data[i];
        if("name" in item && "download" in item && global.setting["downloadSaveDir"]){
          var dir = "";
          if("dirName" in item){
            dir = item["dirName"];
          }
          var p1 = path.join(global.setting["downloadSaveDir"], dir, item["name"]);
          var p2 = path.join(global.setting["downloadSaveDir"], dir, item["name"])+".tmp";
          if (parseInt(item["download"]) == 1 && (!fs.existsSync(p1) && !fs.existsSync(p2))){
            continue;
          }
        }
        global.historys[item["fileHash"]] = item;
      }
    }
    catch(e){
      global.log.info("no history");
    }
  }
  //global.log.info(JSON.stringify(global.historys));
}
function saveHistory(){
  //global.log.info("global.historys length: " + Object.keys(global.historys).length);
  var data=[];
  for(var item in global.historys){
    data.push(global.historys[item]);
  }

  if(data.length == 0)
  {
    fs.createReadStream(config.HISTORY_FILE).pipe(fs.createWriteStream(config.HISTORY_FILE_B));
  }
  fs.writeFileSync(config.HISTORY_FILE, JSON.stringify(data, null, 2));
}
function saveSetting(){
  fs.writeFileSync(config.SETTING_FILE, JSON.stringify(global.setting, null, 2));
}
function startOnBoot(flag){
  if(process.platform == 'win32'){
    var startOnBoot = require('../startOnBoot.js');
    flag = parseInt(flag);
    if(flag == 1)
      startOnBoot.enableAutoStart('fbt', process.execPath);
    else
      startOnBoot.disableAutoStart('fbt');
  }
}
exports.startOnBoot=startOnBoot;
exports.saveSetting=saveSetting;
exports.saveHistory=saveHistory;
exports.saveDir=saveDir;
