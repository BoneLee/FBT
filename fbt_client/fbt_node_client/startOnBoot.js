var path = require("path");
var WinReg = require(path.join(global.exec_path,'winreg'));
var startOnBoot = {
    enableAutoStart: function(name, file, callback){
        var key = getKey();
        key.set(name, WinReg.REG_SZ, file, callback || noop);
    },
    disableAutoStart: function(name, callback){
        var key = getKey();
        key.remove(name, callback || noop);
    },
    getAutoStartValue: function(name, callback){
        var key = getKey();
        key.get(name, function(error, result){
            if(result){
                callback(result.value);
            }
            else{
                callback(null, error);
            }
        });
    }
};

var RUN_LOCATION = '\\Software\\Microsoft\\Windows\\CurrentVersion\\Run';
function getKey(){
    return new WinReg({
        hive: WinReg.HKCU, //CurrentUser,
        key: RUN_LOCATION
    });
}

function noop(){}

module.exports = startOnBoot;
