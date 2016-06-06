/* vim: set sw=2 ts=2 : */
'use strict';

/* vim: set sw=2 ts=2 : */
'use strict';

function buildGetUri(router, kwargs) {
  var baseUri = '';
  var args = [];
  Object.keys(kwargs).forEach(function(key) {
    if(kwargs[key] || kwargs[key] == 0)
      args.push(key + '=' + kwargs[key]);
  });
  var uri = baseUri + '/' + router;
  uri += args.length!=0 ? '?' + args.join('&') : '';
  return uri;
}
app.directive('contenteditable', function() {
  return {
    restrict: 'A', // only activate on element attribute
    require: '?ngModel', // get a hold of NgModelController
    link: function(scope, element, attrs, ngModel) {
      if(!ngModel) return; // do nothing if no ng-model

      // Specify how UI should be updated
      ngModel.$render = function() {
        element.html(ngModel.$viewValue || '');
      };

      // Listen for change events to enable binding
      element.on('blur keyup change', function() {
        scope.$apply(read);
      });
      read(); // initialize

      // Write data to the model
      function read() {
        var html = element.html();
        // When we clear the content editable the browser leaves a <br> behind
        // If strip-br attribute is provided then we strip this out
        if( attrs.stripBr && html == '<br>' ) {
          html = '';
        }
        html.
          replace(/&/g, '&amp;').
          replace(/</g, '&lt;').
          replace(/>/g, '&gt;');
        ngModel.$setViewValue(html);
      }
    }
  };
});
app.directive('ngRightClick', function($parse) {
    return function(scope, element, attrs) {
        var fn = $parse(attrs.ngRightClick);
        element.bind('contextmenu', function(event) {
            scope.$apply(function() {
                event.preventDefault();
                fn(scope, {$event:event});
            });
        });
    };
});
app.filter('escapeHTML', function() {
  return function (text) {
    if (text) {
      return text.
          replace(/&/g, '&amp;').
          replace(/</g, '&lt;').
          replace(/>/g, '&gt;');
    }
    return '';
  };
});
app.factory('Reward', function($http) {
  return {
    all_reward: function(callback, res_type, page, sort_by) {
      if(!sort_by)
        sort_by = 0;
      var kwargs = {
        page: page,
        sort_by: sort_by
      };
      if(res_type !== -1)
        kwargs.res_type = res_type;

      var uri = buildGetUri('all_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    offer_reward: function(callback, uid, res_type, desc, fileName, fb, res_year, res_country) {
      var kwargs = {
        uid: uid,
        res_type: res_type,
        desc: desc,
        fileName: fileName,
        fb: fb,
        res_year: res_year,
        res_country: res_country
      };

      var uri = buildGetUri('offer_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    append_reward: function(callback, rid, appendFb) {
      var kwargs = {
        rid: rid,
        appendFb:appendFb
      };

      var uri = buildGetUri('append_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    my_reward: function(callback, res_type, page) {
      var kwargs = {
        res_type: res_type,
        page: page
      };

      var uri = buildGetUri('my_reward', kwargs);
      return $http.get(uri).success(callback);
    }
  };
});
app.factory("AllFriend", function($http){
  return {
    get: function(callback){
      var uri = buildGetUri('mySpace', {});
      //console.log(uri);
      return $http.get(uri).success(callback);
    }
  };
});
app.factory("AllMyInfo", function($http){
  return {
    get: function(callback){
      var uri = buildGetUri('myInfo', {});
      //console.log(uri);
      return $http.get(uri).success(callback);
    }
  };
});
app.factory('safeApply', function($rootScope) {
  return function(scope, fn) {
      var phase = scope.$root.$$phase;
      if (phase == '$apply' || phase == '$digest') {
          if (fn && ( typeof (fn) === 'function')) {
              fn();
          }
      } else {
          scope.$apply(fn);
      }
  }
});
app.factory('Subheader', function() {
  var index = -1;
  var tab = null;
  //{0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其他"}
  var tabMapper = {
    '全部':-1,
    '电影':0,
    '剧集':1,
    '学习':2,
    '音乐':3,
    '动漫':4,
    '游戏':5,
    '综艺':6,
    '体育':7,
    '软件':8,
    '其它':9
  };
  return {
    setIndex: function(i) {
      tab = i;
      index = tabMapper[i] ? tabMapper[i] : -1;
    },
    getIndex: function() {
      return index;
    },
    getTab: function() {
      return tab;
    }
  };
});
app.factory('ResType', function() {
  var index = 0;
  var allTabs = ["电影", "剧集", "学习", "音乐", "动漫", "游戏", "综艺", "体育", "软件", "其他"];
  var idxMapper = {0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其他"};
  /*var tabMapper = {
    '电影':0,
    '剧集':1,
    '学习':2,
    '音乐':3,
    '动漫':4,
    '游戏':5,
    '综艺':6,
    '体育':7,
    '软件':8,
    '其它':9
  };*/
  return {
    setIndex: function(idx){
      if(index != idx)
        index = idx;
    },
    getIndex: function() {
      return index;
    },
    getTab: function(){
      return idxMapper[index];
    },
    getAllTabs: function(){
      return allTabs;
    }
  };
});
app.factory('Tag', function() {
  var typeMapper = {
    '请选择类别': [],
    '剧集': ['喜剧', '古装', '伦理', '武侠', '纪录片', '玄幻', '冒险', '警匪', '军事', '神话', '科幻', '搞笑', '偶像', '悬疑', '历史', '儿童', '都市', '家庭', '言情'],
    '电影': ['喜剧', '古装', '伦理', '恐怖', '纪录片', '爱情', '动作', '科幻', '武侠', '战争', '犯罪', '惊悚', '剧情', '玄幻', '冒险', '动画'],
    '音乐': ['流行','摇滚','舞曲','电子','HIP-HOP','乡村','民族','古典','音乐剧','轻音乐'],
    '动漫': ['热血','恋爱','搞笑','LOLI','神魔','科幻','真人','美少女','运动','亲子','励志','剧情','校园','历史'],
    '游戏': ['动作','冒险','模拟','角色扮演','休闲','视频','其他'],
    '综艺': ['晚会','生活','访谈','音乐','游戏','旅游','真人秀','美食','益智','搞笑','纪实','汽车'],
    '体育': ['篮球','足球','台球','羽毛球','乒乓球','田径','水上项目','体操','其他'],
    '软件': ['系统','应用','管理','行业','安全防护','多媒体','网络软件','教学方面','即时通讯','娱乐','图形处理','编程'],
    '其他': ['其他'],
    '学习': ['课后作业和答案','课堂笔记','往届考题','电子书或视频等辅助资料','课程课件','课程资料合集','学习心得','TED','百家讲坛','软件教学','其他']
  };

  return {
    getByType: function(type) {
      var tags = typeMapper[type];
      tags.push('请选择标签');
      return tags;
    }
  };
});
app.factory('fileDialog', [function(){
  var callDialog = function(dialog, callback) {
    dialog.addEventListener('change', function() {
      var result = [dialog.files[0], dialog.value];
      callback(result);
    }, false);
    dialog.click();
  };

  var dialogs = {};

  dialogs.saveAs = function(callback, defaultFilename, acceptTypes) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    dialog.nwsaveas = defaultFilename || '';
    if (angular.isArray(acceptTypes)) {
      dialog.accept = acceptTypes.join(',');
    } else if (angular.isString(acceptTypes)) {
      dialog.accept = acceptTypes;
    }
    callDialog(dialog, callback);
  };

  dialogs.openFile = function(callback, multiple, acceptTypes) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    if (multiple === true) {
      dialog.multiple = 'multiple';
    }
    if (angular.isArray(acceptTypes)) {
      dialog.accept = acceptTypes.join(',');
    } else if (angular.isString(acceptTypes)) {
      dialog.accept = acceptTypes;
    }
    callDialog(dialog, callback);
  };

  dialogs.openDir = function(callback) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    dialog.nwdirectory = 'nwdirectory';
    callDialog(dialog, callback);
  };

  return dialogs;
}]);

/*
app.service("Askbot",  ['$rootScope', '$http',
  function ($rootScope, $http) {
  
  var askbotURL = 'http://ask.friendsbt.com/';
  var askbotCSRFToken = null;
  this.askbotCSRF = function () {
    if (askbotCSRFToken == null) {
      $http.jsonp(askbotURL + 'get_token?callback=JSON_CALLBACK')
      .success(function (data) {
        askbotCSRFToken = data;
      });
    }
    return askbotCSRFToken;
  };
  this.askbotCSRF();

  this.askbotSignup = function (postData) {
      $.ajax({
        url: askbotURL + "account/signup/",
        type: "POST",
        data: postData,
        headers: {
          "X-CSRFToken": askbotCSRFToken
        },
        xhrFields: {
          withCredentials: true
        },
        success: function(data, textStatus, xhr) {
          console.log(textStatus);
        }
      });
    };

  this.askbotLogout = function () {
    $.ajax({
      url: askbotURL + "account/signout/",
      type: "GET",
      headers: {
        "X-CSRFToken": askbotCSRFToken
      },
      xhrFields: {
        withCredentials: true
      },
      success: function(data, textStatus, xhr) {
        console.log('askbot logout success');
      }
    });
  };

  var _self = this;
  this.askbotLogin = function (username, password) {
    $.ajax({
      url: askbotURL + "account/signin/",
      type: "POST",
      data: {
        login_provider_name: "local",
        persona_assertion:'',
        openid_login_token:'',
        password_action:'login',
        login_with_password:"Sign in",
        "username": username,
        "password": password
      },
      headers: {
        "X-CSRFToken": askbotCSRFToken
      },
      xhrFields: {
        withCredentials: true
      },
      success: function(data, textStatus, xhr) {
        console.log('askbot login success');
      },
      statusCode: {
        302: function() {
          console.log('askbot login success, 302');
        },
        204: function() {
          console.log('need register');
          _self.askbotSignup( {
            'username': username.substring(0, username.indexOf('@')),
            'email': username,
            'password1': password,
            'password2': password
          });
        }
      }
    });
  };

}]);
*/
app.service("User",  ['$rootScope', '$http', '$cookies', '$interval',
  function ($rootScope, $http, $cookies, $interval) {
    
  var logincallback = null;
  var user_info = {
    is_logined: false
  };
  var item_list = ["nick_name", "icon", "allow_login", "university", 
      "college", "total_coins", "coins_by_study",
      "study_coins", "message_cnt", "username", "uid",
      "followers_num", "answers_num", "thanks_coin",
      "thumb_num", "desc", "real_name", "password"];

  this.getUserInfo = function() {
    return user_info;
  };

  this.clearUserInfo = function() {
    for (var key in user_info) {
      if (key !== "is_logined") {
        delete user_info[key];
      }
    }
    user_info.is_logined = false;
  };
  
  this.loginRequest = function(username, pwd, successCallback, errorCallback) {
    var data = {"user": username, "passwd": pwd};
    $http.post('/login', $.param(data), {
      xsrfCookieName: '_xsrf',
      xsrfHeaderName: 'X-CSRFToken',
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      }
    }).success(function (data) {
      if ('err' in data && 'nick_name' in data && 'icon' in data && data['err'] == 0) {
        var nick_name = data['nick_name'];
        var icon = data['icon'];
        var university = data['university'];
        var college = data['college'];
        var total_coins = data['total_coins'];
        var study_coins = data['study_coins'];
        var message_cnt = data['message_cnt'];
        var localUsername = data['username'];
        $rootScope.userdisplay = nick_name;
        $rootScope.is_logined = true;
        $rootScope.userIcon = icon;
        $rootScope.university = university;
        $rootScope.college = college;
        $rootScope.total_coins = total_coins;
        $rootScope.study_coins = study_coins;
        $rootScope.message_count = message_cnt;
        $rootScope.username = username;
        user_info.is_logined = true;
        for (var key in data) {
          if (key !== "err") {
            user_info[key] = localStorage[key] = data[key];
          }
        }
        //$cookies.user_token = username;
        //Askbot.askbotLogin(username, pwd);
      }
      // if (successCallback)  successCallback(data);

      if (successCallback) {
          if ('err' in data && data['err'] == 0) {
          if('allow_login' in data && data['allow_login'] == true){
            var check_cookie_setted = $interval(function() {
              var user = $cookies.user_token;
              if (user && user.length > 0)
                successCallback(data);
            }, 1);
            logincallback = (function(i) {
              return function() {
                $interval.cancel(i);
              }
            }(check_cookie_setted));
          }else{
            successCallback(data);
          }
        } else {
          successCallback(data);
        }
       }
    }).error(function() {
      if (errorCallback) errorCallback();
    });
  };

  this.logined = function() {
    var user = $cookies.user_token;
    if (user && user.length > 0) {
      angular.forEach(item_list, function(v, i) {
        user_info[v] = localStorage[v];
      });
      return true;
    } else {
      $rootScope.is_logined = false;
      $rootScope.userdisplay = "";
      $rootScope.userIcon = "";
      $rootScope.university = "";
      $rootScope.college = "";
      $rootScope.total_coins = "";
      $rootScope.study_coins = "";
      $rootScope.username = "";
      for (var key in user_info) {
        if (key !== "is_logined") {
          delete user_info[key];
          delete localStorage[key];
        }
      }
      user_info.is_logined = false;
      return false;
    }
  };

  this.login_from_fbt = function (uid, token, callback) {
    var params = {"params": {"uid": uid, "token": token}};
    $http.get('/login_from_fbt', params).success(function (data) {
      if ('err' in data && 'nick_name' in data && 'icon' in data && data['err'] == 0) {
        if(data.allow_login){
          var nick_name = data['nick_name'];
          var icon = data['icon'];
          var university = data['university'];
          var college = data['college'];
          var total_coins = data['total_coins'];
          var study_coins = data['study_coins'];
          var message_cnt = data['message_cnt'];
          var username = data['username'];
          $rootScope.userdisplay = nick_name;
          $rootScope.is_logined = true;
          $rootScope.userIcon = icon;
          $rootScope.university = university;
          $rootScope.college = college;
          $rootScope.total_coins = total_coins;
          $rootScope.study_coins = study_coins;
          $rootScope.message_count = message_cnt;
          $rootScope.username = username;
          user_info.is_logined = true;
          for (var key in data) {
            if (key !== "err") {
              user_info[key] = localStorage[key] = data[key];
            }
          }
          if (callback) callback('');
        } else {
          // return username for info complement
          if (callback) callback(data['username']);
        }
      } else {
        console.log('token login error');
      }
    });
  };

  this.login = function (callback) {
    if (this.logined()) {
      if (callback)  callback();
      return;
    }
    logincallback = callback;
    var username = localStorage.email;
    var pwd = localStorage.pwd;
    if (username && username.length > 0 && pwd && pwd.length > 0) {
      this.loginRequest(username, pwd, function(data) {
        logincallback = callback;
        if ('err' in data && data['err'] == 0) {
          if (callback)  callback();
        } else {
          console.log('user password error in local store');
          localStorage.email = '';
          localStorage.pwd = '';
          //$('#login-modal').modal({backdrop: true, keyboard: true});
          window.location.href = '/#/home';

        }
      });
    } else {
      //$('#login-modal').modal({backdrop: true, keyboard: true});
      window.location.href = '/#/home';
    }
  };

  var username = localStorage.email;
  var pwd = localStorage.pwd;

  if (this.logined()) {
    var nick_name = localStorage.nick_name;
    var icon = localStorage.icon;
    var university = localStorage.university;
    var college = localStorage.college;
    var localUsername = localStorage.username;
    $rootScope.is_logined = true;
    $rootScope.userdisplay = nick_name;
    $rootScope.userIcon = icon;
    $rootScope.university = university;
    $rootScope.college = college;
    $rootScope.username = localUsername;
  } else if (username && username.length > 0 && pwd && pwd.length > 0) {
    this.login(null);
  }

  this.loginsuccess = function () {
    if (logincallback) {
      logincallback();
    }
  };
}]);

// app.factory("MyRes", function($http){
//   return {
//     getMyRes: function(is_audit, page, callback){
//       var kwargs = {
//         is_audit: is_audit,
//         page: page
//       };

//       var req = {
//         url: '/resource/user',
//         method: 'GET',
//         params: kwargs
//       };
//       $http(req).success(callback);
//     }
//   };
// });

app.directive('fancyTree', function() {
  return {
    restrict: 'A',
    link : function(scope, element, attrs){
      $(element).fancytree({
        extensions: ["table"],
        checkbox: true,
        autoCollapse: true,
        autoScroll: true,
        selectMode: 3,
        table: {
          //indentation: 20,      // indent 20px per node level
          nodeColumnIdx: 1,     // render the node title into the 2nd column
          checkboxColumnIdx: 0  // render the checkboxes into the 1st column
        },
        source: scope.treeData,
        renderColumns: function(event, data) {
          var node = data.node,
          $tdList = $(node.tr).find(">td");
          if(typeof(scope.render) == "function")
            scope.render($tdList, node);
        },
        select: function(event, data) {
          /*var filesCount = 0;
          data.tree.visit(function(node){
            if(!node.folder) filesCount += 1;
          });*/
          scope.selectedFiles = $.map(data.tree.getSelectedNodes(), function(node){
            if(node.folder) return null;
            return node.key;
          });
          // Download callback
          //$('#btn-download-selected-files').text('下载(' + selectedFiles.length + '/' + filesCount + ')');
        }
      });
    }
  }
});
