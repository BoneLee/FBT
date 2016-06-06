/**
 *
 * Created by bone-lee on 15-3-22.
 */


var downloadingFileIDs={};

var MAX_DOWNLOAD_IN_UPDATE_TIME=5;
var UPDATE_TIME=1*1000;//60*1000;//60 seconds
var THREE_MINUTES=3;//3*60;

function now(){
    return parseInt(new Date().getTime()/1000);
}

setInterval(function updateProgress() {
    for(var fileID in downloadingFileIDs){
        var expireTime=downloadingFileIDs[fileID];
        var nowTime=now();
        if(nowTime > expireTime){
            delete downloadingFileIDs[fileID];
        }
    }
    console.log("time up");
    console.log("expireTimeOfFileHashes:"+JSON.stringify(downloadingFileIDs));
}, UPDATE_TIME);

function downloadFileMock(requestedFileHash) {
//    var requestedFileHash = query["hash"];
    console.log("requestedFileHash:"+requestedFileHash+" length of expireTimeOfFileHashes:"+Object.keys(downloadingFileIDs).length);
    if(Object.keys(downloadingFileIDs).length >= MAX_DOWNLOAD_IN_UPDATE_TIME){
        console.log("error");
        return;
        //return page404(response, "hash argument not found");
    }
    downloadingFileIDs[requestedFileHash]=now()+THREE_MINUTES;
}



function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

for(var i=0; i < 15; ++i){
    var mockHash=Math.floor(Math.random()*100);
//    sleep(Math.floor(Math.random()*5)*1000);
    downloadFileMock(mockHash);
}
