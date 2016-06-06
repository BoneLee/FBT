var main = require("./main");
var path = require('path');
var gui;

exports.tray = function(){
  main.check(window,redirect);
  setTimeout(function () {
    main.setWindow(window);
  }, 2000);
};

function getUserHome() {
  return process.env[(process.platform == 'win32') ? 'USERPROFILE' : 'HOME'];
}

function redirect(){
  window.location.href = "http://127.0.0.1:12345/index";
  //setTimeout(run, 1000);
  run();
}

exports.open_dir = function(filepath) {
  if (!gui) {
    gui = window.require('nw.gui');
  }
  gui.Shell.showItemInFolder(filepath);
};
exports.winMin = function(){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  var win = gui.Window.get(window);
  win.minimize();
};
exports.winMax = function(){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  var win = gui.Window.get(window);
  win.maximize();
};
exports.winUnMax = function(){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  var win = gui.Window.get(window);
  win.unmaximize();
};
exports.winClose = function(){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  var win = gui.Window.get(window);
  win.close();
};
exports.winResize = function(w, h){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  try{
    var win = gui.Window.get(window);
    win.resizeTo(w, h);
  }catch(e){
    //pass
  }
}
exports.winMoveTo = function(w, h){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  var win = gui.Window.get(window);
  win.moveTo(w, h);
}
exports.winOpen = function(url){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  gui.Window.open(url, {
    "position": 'center',
    "width": 1140,
    "height": 720,
    "icon": "fbtLogo2.png",
    "title": "FBT",
    "toolbar": false,
    "frame": true
  });
}
exports.winOpenEx = function(url){
  if (!gui) {
    gui = window.require('nw.gui');
  }
  gui.Shell.openExternal(url);
}

function run(){
  gui = window.require('nw.gui');
  /*
  if (parseInt(process.versions['node-webkit'].split('.')[1]) >= 8) {
    // this works for nw >= 0.8.x
    gui.App.setCrashDumpDir(path.join(getUserHome(), ".fbt"));
  }
  */
  var win = gui.Window.get(window);
  //win.maximize();
  if(process.platform == 'win32'){
    var tray;
    var trayMenu = new gui.Menu();
    trayMenu.append(new gui.MenuItem({label:"exit"}));
    trayMenu.items[0].click = function() {
      gui.App.quit();
    };
    win.on('close', function(){
      //win.console.log(loadSet());
      if(loadSet()){
        this.hide();
        tray = new gui.Tray({title:'fbt',icon:"fbtLogo2.png"});
        tray.menu = trayMenu;
        tray.on("click", function(){
          this.remove();
          tray = null;
          win.show();
        });
      }
      else{
        this.close(true);
      }
    });
  }
  process.on('uncaughtException', function(err) {
    var fs = require('fs');
    var data = err.stack+"\n";
    var fbt = path.join(getUserHome(),".fbt");
    if(!fs.existsSync(fbt)){
      fs.mkdirSync(fbt);
    }
    fs.appendFileSync(path.join(getUserHome(),".fbt", 'error.txt'),data);
    window.location.href = "http://127.0.0.1:12345/error";
    /*window.alert("很抱歉，由于网络异常，软件出现了未知错误，请重启");
     var win = gui.Window.get(window);
     win.close();*/
  });
}

function loadSet(){
  //history {"fileHash":,"progress":}
  var fs = require('fs');
  if (fs.existsSync(path.join(getUserHome(),".fbt", 'setting.json'))) {
    var data;
    try{
      data = JSON.parse(fs.readFileSync(path.join(getUserHome(),".fbt", 'setting.json')));
    }
    catch(e){
      return true;
    }
    return !(data && "tray" in data && data["tray"] == 0);
  }
  else
    return true;
}
