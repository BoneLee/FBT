function getCookie(name) {
  var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
  return c ? c[1] : undefined;
}

function normalizeFileSize(fileSize){
    fileSize = parseInt(fileSize);
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

function removeHtmlTag(html){
    if(html === undefined || html === '')
        return '';
    var s = html;
    s =  s.replace(/(\n)/g,'');
    s =  s.replace(/(\t)/g,'');
    s =  s.replace(/(\r)/g,'');
    s =  s.replace(/<\/?[^>]*>/g,'');
    s =  s.replace(/\s*/g,'');
    s =  s.replace(/&nbsp;|&#160;/gi, '');
    //s = '<html>' + s + '</html>';
    return s;

}

function ctime2LocaleDateString (ctime) {
    return new Date(ctime * 1000).toLocaleDateString();
}

function user_icon_not_find(){
    var img=event.srcElement;
    img.src="//test.friendsbt.com/statics/images/user_icon/34.jpg";
    img.onerror=null;
}

function encode_username(username) {
    username = username || "";
    return Base64.encode(username);
}
