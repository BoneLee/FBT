/*
/v2/movie/search?q={text}
Required Scope
movie_basic_rExample:
GET /v2/movie/search?q=张艺谋 GET /v2/movie/search?tag=喜剧
http://movie.douban.com/subject/7065154/
 */

var urllib = require('urllib');
var fs = require('fs');
var EventEmitter = require('events').EventEmitter;
var cheerio = require('cheerio');

function retry_request(url, options, times, callback) {
    var count = 0;
    var OK = new EventEmitter();
    urllib.request(url, options, function cb(err, data, res){
        count++;
        if (count > times) {
            callback(null);  // if not succeed, pass back null
            return;
        }
        if (err)  {
            console.log(err);
            urllib.request(url, options, cb);
        } else if (res.statusCode === 200) {
            OK.emit('ok', {'data': data, 'res': res});
        } else {
            console.log(res.statusCode);
            urllib.request(url, options, cb);
        }
    });
    OK.on('ok', function(params){
        callback(params.data, params.res);
    });
}

function Searcher(query) {
    this.query = query;    // query is an object
}

Searcher.prototype.search = function(cb) {
    retry_request("http://api.douban.com/v2/movie/search", {
        data: {'q': this.query, 'count': 1},
        dataType: 'json'
    }, 3, function(data) {
        cb(data.subjects[0].id);  // pass back movieid
    });
};

function Fetcher(movidId) {
    this.movieId = movidId;
}

Fetcher.prototype.fetch = function(callback) {
    retry_request("http://movie.douban.com/subject/"+this.movieId+'/', {}, 3, function(data){
        var $ = cheerio.load(data.toString());
        var img = $('img[src^="http://img3.douban.com/view/movie_poster_cover/spst/public/"]')[0];
        console.log(img.attribs.src);
        retry_request(img.attribs.src, {}, 3, function(data){
            callback(data);     // pass back image buffer
        });
    });
};

function fetchMoviePoster(searchText, callback) {
    /*
    目前仅针对电影, 之后可以把动漫加上
    抓取失败, callback(null)
    抓取成功, callback(image_buffer)
     */
    var s = new Searcher(searchText);
    s.search(function(movieId){
        if (!movieId) {
            callback(null);
        } else {
            var f = new Fetcher(movieId);
            f.fetch(callback);
        }
    });
}

exports.fetchMoviePoster = fetchMoviePoster;