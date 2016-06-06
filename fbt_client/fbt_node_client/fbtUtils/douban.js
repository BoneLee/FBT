/*
豆瓣API接口
查询示例：
    require('douban').getInfo('南京', callback(info){
        ...
    });
回调函数参数info:
    info.id[String]: 电影的id
    info.mlink[String]: 电影的主页面链接
    info.ilink[String]: 电影海报的链接, 大小 100*147
    info.rating[Number]: 电影的平均评分
    info.title[String]: 标题
    info.year[String]: 年份
    info.countries[Array]: 国家
    info.comments[Array]: 短评
    info.summary[String]: 简介
    info=null 代表没有搜索到任何结果

e.g.
{ title: '南京！南京！',
  year: '2009',
  countries: [ '中国大陆', '香港' ],
  summary: '1937年12月13日，时为国民政府首都的南京城沦陷，部分官员弃城逃亡，但仍有许多官兵留守，誓死保卫这个大厦将倾的城池。\n宋锡濂部军官陆剑雄（刘烨 饰）协同战友与日军展开了激烈的巷战，他们微弱而顽强的抵抗最终被压制，数以万计的中国军民成为俘虏，在枪炮声中血染长江；金陵女子学院安全区，女教师姜淑云（高圆圆 饰）奔波往复，尽力帮助和拯救所有来此避难的同胞，但兽性大发的日军早已虎视眈眈盯上了藏身于此的妇女；拉贝的秘书唐先生（范伟 饰）小心应付，委曲求全，为了保护家人而做出错误的选择，他也为此付出代价；舞女小江（江一燕 饰）纵使逃亡避难也不愿抛却女性的柔媚，她在关键时刻的选择则在其女性的外壳下注入一份刚强；日本人角川（中泉英雄 饰）随部队进驻这个千疮百孔、破败不堪的城池，在这个人间炼狱，他的心灵感受到前所未有的巨大冲击。\n狼烟滚滚，血流成河，大时代的背景下，人们既要承受时代的无情给予，也要做出攸关命运的痛苦抉择……©豆瓣',
  comments:
   [ '绝对杰作！！',
     '这是一部用国难来做商业片噱头的无耻电影。陆川作为编剧和导演是失败的，对战争的反思由于其历史及价值观念的混乱而完全不可理喻。',
     '如果陆导不是汉奸 那他一定是懦夫',
     '恶心人的感人招牌，演技奇烂的高大全版人民英雄高圆圆，所有角色从头哭到尾，不为别的，就是为了让观众买账陪他们哭，日本兵凭什么要在结尾自杀满足你们一厢情愿的人本善？拍日本人马屁也不用这么明显吧，令人发指的假惺惺，呸！' ],
  rating: 7.5,
  id: '2294568',
  mlink: 'http://movie.douban.com/subject/2294568/',
  ilink: 'http://img3.douban.com/view/movie_poster_cover/spst/public/p470463541.jpg'
}
 */
var path = require("path");
var urllib =  require(path.join(global.exec_path,'urllib'));
var cheerio = require(path.join(global.exec_path,'cheerio'));
var fs = require('fs');
var EventEmitter = require('events').EventEmitter;


function retry_request(url, options, times, callback) {
  var count = 0;
  var OK = new EventEmitter();
  options.followRedirect = true;
  urllib.request(url, options, function cb(err, data, res){
    count++;
    if (err) {
      global.log.error(err);
      if (count > times) {
        callback(null);
      } else {
        options.timeout = options.timeout * 2;
        console.log("re");
        urllib.request(url, options, cb);
      }
    } else if (res.statusCode === 200) {
      OK.emit('ok', {'data': data, 'res': res});
    } else {
      global.log.warning("fetch douban status code:", res.statusCode);
      if (count > times) {
        callback(null);  // if not succeed, pass back null
      } else {
        console.log("re");
        urllib.request(url, options, cb);
      }
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
    dataType: 'json', timeout: 2000
  }, 3, function(data) {
    if (data && data.total) {
      var searchResult = {};
      searchResult.id = data.subjects[0].id;
      searchResult.mlink = data.subjects[0].alt;
      searchResult.ilink = data.subjects[0].images.medium;
      searchResult.rating = data.subjects[0].rating.average;
      cb(searchResult);  // pass back movieid
    } else {
      cb(null);   // no search result
    }
  });
};

function Fetcher(source) {
  this.source = source;
  var that = this;
  this.source_type = (function() {
    if (!isNaN(source)) {  // "123456"
      return "id";
    } else if (source.indexOf("http://img3.douban.com") === 0) {
      return "ilink";     // image link
    } else if (source.indexOf("http://movie.douban.com/subject/") === 0) {
      // last character if mlink must not be slash
      that.source = that.source.charAt(that.source.length-1) === '/' ?
        that.source.substr(0, that.source.length-1) : that.source;
      return "mlink";     // movie link
    } else {
      global.log.error("wrong type");
      return null;
    }
  })();
}

Fetcher.prototype.fetchAll = function(callback) {
  /*
   * fetch 所有信息, 包括 title, year, countries, summary, comments
   * 除了comments通过网页抓取, 其它通过movieAPI获取
   */
  if (this.source_type !== 'id' && this.source_type !== 'mlink') {
    global.log.error("source type should be id or mlink");
    callback(null);
  } else {
    var movie_api_url = "http://api.douban.com/v2/movie/subject/" +
      (this.source_type === 'mlink' ? this.source.split('/').pop() : this.source);
    var movie_url = this.source_type === 'mlink' ? this.source :
      'http://movie.douban.com/subject/' + this.source;
    retry_request(movie_api_url, {dataType: 'json'}, 3, function(info){
      if(!info) {
        return callback(null);
      }
      retry_request(movie_url, {}, 3, function(page) {
        var $ = cheerio.load(page ? page.toString() : '');
        var commentsArray = [];
        $('div.comment-item > div.comment > p').each(function(i, element){
          commentsArray[i] = element.children[0].data.trim();
        });
        callback({
          'title': info.title,
          'year': (function normalize(year) {
            var begin = year.search(/[12][0-9][0-9][0-9]/);
            if (begin >= 0) {
              return parseInt(year.substring(begin, begin+4));
            }
            return null;
          }(info.year)),
          'countries': info.countries,
          'summary': info.summary,
          'comments': commentsArray
        });
      });
    });
  }
};

var getInfo = (function(){
  var s = new Searcher();
  return function(stext, callback){
    s.query = stext;
    s.search(function(sr){
      if (sr) {
        var f = new Fetcher(sr.id);
        f.fetchAll(function (info) {
          if(info) {
            info.rating = sr.rating;
            info.id = sr.id;
            info.mlink = sr.mlink;
            info.ilink = sr.ilink;
            callback(info);
          } else {
            callback(null);
          }
        });
      } else {
        callback(null);
      }
    });
  };
}());

exports.getInfo = getInfo;
