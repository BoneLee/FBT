/*var ejs = require("C:\\Users\\dengbo\\.fbt\\node_modules\\ejs");
var path = __dirname+"/views/friendItem.ejs"
    ,str = require("fs").readFileSync(path, "utf-8");
var ret = ejs.render(str, {"count":1,"nick_name": "ok", "online": 1, "type": 0, "user": "ok@11.com", "uid": 14095495822832});
console.log(ret);*/
//var main = require("./main");
//main.check(Object,function(){});
//var http = require('http');http.createServer(function (request, response) {  response.writeHead(200, {'Content-Type': 'text/plain'});  response.end('Hello World\n');}).listen(8886,"2001:cc0:2026:e00:75c4:cba0:993c:48f2");console.log('Server running...maybe...');
/*var fs = require("fs");
var path = require("path");
var compressor = require('yuicompressor');
function getAllFiles(root){
	var files = fs.readdirSync(root);
	files.forEach(function(file){
		var pathname = path.join(root,file);
		var stat = fs.lstatSync(pathname);

		if (!stat.isDirectory() && path.extname(pathname) == ".js"){
		    compressor.compress(pathname, {
			    //Compressor Options:
			    charset: 'utf8',
			    type: 'js',
			    nomunge: true,
			    'line-break': 80
			}, function(err, data, extra) {
			    //err   If compressor encounters an error, it's stderr will be here
			    //data  The compressed string, you write it out where you want it
			    //extra The stderr (warnings are printed here in case you want to echo them
			    outpath = path.join(process.argv[3],pathname);
			    fs.writeFileSync(outpath, data, 'utf-8');
			});
		} else {
		   getAllFiles(pathname);
		}
	});
}
getAllFiles(process.argv[2]);*/
/*var s = [];
s[0] = "test";
s[1] = "hehe";
console.log(s.shift());*/
function removeArrayItem(arr, item) {
    if(!arr)
        return;
    var removeCounter = 0;

    for (var index = 0; index < arr.length; index++) {    	 
        if ( arr[index] === item ) {
            arr.splice(index, 1);
            removeCounter++;
            index--;
        }
    }

    return removeCounter;
}
function randomChoose(items){
	return items[Math.floor(Math.random()*items.length)];
}
var a=[{"12":"test","ho":"12"},{"123":"test","ho":"12"}];
var i = randomChoose(a);
console.log(JSON.stringify(a));
removeArrayItem(a,i);
console.log(JSON.stringify(a));
