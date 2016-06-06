/**
 * Created by fbt on 14-7-16.
 */

require("./fbtSetting.js");
var setting=global.setting;

if(setting["downloadSaveDir"]){
    console.log("downloadSaveDir:"+setting["downloadSaveDir"])
}else{
    console.log("downloadSaveDir not set yet.")
}
setting["downloadSaveDir"]="D:\\";
