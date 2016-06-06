'use strict';
app.filter('realName', function () {
  return function (friend) {
    if (friend.real_name) {
      return friend.nick_name+"("+friend.real_name+")";
    } else {
      return friend.nick_name;
    }
  };
});
app.controller('MyspaceController', function($scope, $window, $location, $http, toast, AllFriend, fileDialog, $rootScope) {
  $scope.isMy = true;

  var s = $location.search();
  var idx = 1;
  var html = ["inform.html", "friend.html", "resource.html", "person.html"];
  if("idx" in s){
    idx = s["idx"];
    if(idx >= html.length)
      idx = 1;
  }
  $scope.global = $window.global;
	$scope.urlBase = "partials/spacePartials/";
  $scope.sideMenus = [
  	{"title":"通知", "url":$scope.urlBase+html[0]},
  	{"title":"好友", "url":$scope.urlBase+html[1]},
  	{"title":"我的资源", "url":$scope.urlBase+html[2]},
  	{"title":"个人档", "url":$scope.urlBase+html[3]}
  ];
  $scope.idx = idx;
  $scope.spaceTemplate = $scope.urlBase+html[idx];
  //$scope.selected = $scope.sideMenus[idx];
  $scope.loadPage = function (menu, index) {
      //$scope.selected = menu;
      $(".myspace .space_sidemenu_wrap .active").removeClass('active');
      $($(".myspace .space_sidemenu_wrap li")[index]).addClass('active')
      $scope.spaceTemplate = menu.url;
  };
  /*
  $scope.isSelected = function(menu) {
    return $scope.selected === menu;
	};
  */
  $scope.editIcon = function(){
    fileDialog.openFile(function(result){
      var value = result[0];
      if(!value)
        return; 
      resizeImage(value, function(dataurl) {
        $http.get("/editIcon?path=" + encodeURIComponent(dataurl)).success(function(data){
          if("type" in data && data["type"] == 1){
            toast.showNoticeToast("修改成功");
            $scope.info.icon = dataurl;
            var scope = angular.element($("#myinfoWrap")).scope();
            if(scope){
              scope.myinfo.icon = dataurl;
            }
          }
          else{
            if("error" in data)
              toast.showErrorToast(data["error"]);
            else
              toast.showErrorToast("修改失败，请重试");
          }
        });
      });
    }, false, [".png",".jpg",".gif",".jpeg"]);
  };
  $scope.friendGroups = AllFriend.friendGroups;
  $scope.friendsUids = AllFriend.friendsUids;
  $scope.info = AllFriend.info;
  $scope.newshuo = $scope.info.shuo;
  if($scope.friendGroups.length == 0){
    AllFriend.init();
  };

  $scope.updateShuo = function() {
      if (!$scope.newshuo) {
          $scope.newshuo = $scope.info.shuo;
          return;
      }

      var content = $scope.newshuo.trim();
      if(content.length > 140){
          toast.showErrorToast("很抱歉，说说最长为140字"); 
          $scope.newshuo = $scope.info.shuo;
          return;
      }   
      if(content == $scope.info.shuo || !content) {
          $scope.newshuo = $scope.info.shuo;
          return;
      }

      content = htmlencode(content);
      var param = {}; 
      param["op"] = 0;
      param["param"] = content;
      $http.post('/myShuo', param).success(function(data) {
          if(data["type"] && data["type"] == 1){
              toast.showSuccessToast("发布成功");
              $scope.info.shuo = content;
            }
          else
              toast.showErrorToast("发布失败，请重试");
      });
  };

  $scope.goHome = function() {
    $location.path("/resource");
  };
});
app.controller('FriendController', function($scope, $modal, toaster, $window, remoteSocket, chatbox, AllFriend, toast) {
  $scope.curGroup = 1;
  $scope.friendGroup = AllFriend.friendGroups[1];
  $scope.emojis = [
    "1","-1","100","angry","beers","birthday","bowtie","cold_sweat","dizzy_face","dog","flushed","ghost","heart_eyes","joy","kissing_heart","laughing","moneybag","muscle","ok_hand","pensive","pig","pray","rage","relieved","scream","clap","shit","skull","sleeping","sleepy","smile","sob","stuck_out_tongue_winking_eye","sunglasses","tada","tired_face","triumph","unamused","v","yum",
    "hand","eyes","facepunch","see_no_evil","paw_prints","sos",
            "trollface","u7981","weary","vs","zap",
            "zzz","exclamation","feelsgood","finnadie","wink"
  ];
  $scope.groupChats = [];
  $scope.canShowEmoji = false;
  $scope.showFriendGroup = function(idx){
    $scope.curGroup = idx;
  };
  $scope.emojiClick = function(idx){
    $scope.myGroupChat += ":"+$scope.emojis[idx]+":";
  };
  $scope.showSmile = function(){
    $scope.canShowEmoji = !$scope.canShowEmoji;
  }
  $scope.chatFriend = function(id, nick_name) {
      $window.singleChats[id] = [];
      chatbox.show(id);
  }
  $scope.toggleOp = function(id){
    if($(id).is(":hidden"))
      {
        $(id).show();
        $(id).slideDown(); 
      }
      else{
        $(id).hide();
        $(id).slideUp(); 
      }
  };
  $scope.getStyleClass = function(online){
    if($window.parseInt(online) == 0)
      return 'offline';
    return '';
  };
  $scope.getChatStyleClass = function(online){
    if($window.parseInt(online) == 1)
      return 'default';
    return '';
  };
  $scope.delFriend = function(user, star, uid, groupIdx){
    $scope.delFriendInfo = {"user": user, "star": star, "uid": uid, "groupIdx": groupIdx};
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'delFriendModal.html',
      controller: 'delFriendModalCtrl',
      resolve: {
        delFriendInfo: function () {
          return $scope.delFriendInfo;
        }
      }
    });
  };
  $scope.showModal = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'searchModal.html',
      controller: 'searchFriendModalCtrl'
    });
  };
});
app.controller("MyinfoController", function($scope, $modal, AllMyInfo){
  $scope.loveStates = ["单身","暧昧","恋爱","已婚",""];
  $scope.genders = ["男","女",""];
  $scope.myinfoReady = false;
  AllMyInfo.get(function(data){
    if(data){
      $scope.myinfo = data["user"];
      $scope.preMyinfo = clone($scope.myinfo);
      /*$scope.myinfo["department"] = "111";
      $scope.myinfo["freshyear"] = "2015";
      $scope.myinfo["weibo"] = "2014";
      $scope.myinfo["qq"] = "2014";
      $scope.myinfo["phone"] = "2014";*/
      $scope.myinfoReady = true;
    }
  });
  $scope.changePwd = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'changePassword.html',
      controller: 'changePasswordModalCtrl'
    });
  };
  $scope.editInfo = function(){
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'changeInfo.html',
      controller: 'changeInfoModalCtrl',
      scope: $scope
    });
  };
});
app.controller("MyresController", function(WinManager, $scope, $window, $modal, $location, MyRes, pagination, resCountPerPage, toaster, downloader, AllFriend, localSocket){
  $scope.isMy = $scope.$parent.isMy;

  $scope.allRes = {};
  $scope.curRes = [];
  $scope.currentPage = 1;
  $scope.canDownload = $location.path().indexOf("friend_res") != -1;
  $scope.friend = $window.fbtUID;
  $scope.isPrivate = 1;
  if($scope.canDownload){
    var s = $location.search();
    $scope.friend = s["uid"];
    if (!($scope.friend in AllFriend.friendsUids))
      $scope.isPrivate = 1 - $window.parseInt(s["public"]);
  }
  $scope.shouldShowDouban = function(t){
    if(t == "电影" || t == "剧集" || t == "动漫" || t == "综艺")
      return true;
    else
      return false;
  };
  $scope.showDouban = function(dirName){
    var nameIndex=dirName.lastIndexOf('.') == -1?dirName.length:dirName.lastIndexOf('.');
    var name=dirName.substring(0,nameIndex);
    WinManager.open("http://www.douban.com/search?q="+name);
  };
  $scope.getRes = function(){
    if($scope.currentPage in $scope.allRes){
      $scope.curRes = $scope.allRes[$scope.currentPage];
    }
    else{
      MyRes.getMyRes($scope.currentPage, $scope.friend, $scope.isPrivate, function(data){
        if(data["type"] && data["type"] == 1)
        {
          if(!data["size"])
          {
            pagination.hide('my_resource');
            return;
          }
          $scope.totalItems = data["size"];
          $scope.curRes = data["resource_list"];
          preHandleRes($scope.curRes);
          $scope.allRes[$scope.currentPage] = $scope.curRes;
          if(parseInt(data["size"]) > 1)
            pagination.render($scope.currentPage, $scope.totalItems, 'my_resource',function(currentPageNum, totalPageNum) {
              $scope.currentPage = currentPageNum;
              $scope.getRes();
            });
        }
        else{
          toaster.pop('error', "错误提示", "资源请求失败，请重试", true);
        }
      });
    }
  };
  $scope.showDir = function(idx){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'folderModal.html',
      controller: 'folderModalCtrl',
      scope: $scope,
      resolve: {
        index: function () {
          return idx;
        },
        canDownload: function(){
          return $scope.canDownload;
        },
        rid: function(){
          return '';
        }
      }
    });
  };
  $scope.getRes();
  $scope.download = function(idx){
    downloader.download($scope.curRes[idx], $scope.isPrivate);
  };

  $scope.viewResourceDetailClickHandler = function(resource, isMy) {
    var returnUrl = $location.url();
    if(returnUrl.match('^/myspace') != null) {
      returnUrl = '/myspace?idx=2';
    }
    $location.path('/home/details/').search({
      'resource':resource,
      'isMy':isMy,
      'isPrivate':$scope.isPrivate,
      'returnUrl':returnUrl
    });
  };
  $scope.showMyFile = function(idx){
    var msg;
    if($scope.curRes[idx].isDir){
      var fileHash = $scope.curRes[idx].file_hashes.split(",")[0];
      msg = JSON.stringify({"file_hash": fileHash, "isDir": $scope.curRes[idx].isDir});
    }
    else
      msg = JSON.stringify({"file_hash": $scope.curRes[idx].file_hash, "isDir": $scope.curRes[idx].isDir});
    localSocket.emit('open_dir', msg);
  }
});
app.controller("InformController", function($scope, $modal, AllRes, downloader, toast, $window, $http, AllFriend){
  /*$scope.allRes = {};
  $scope.curRes = [];
  $scope.isPrivate = 0;
  $scope.totalItems = 100;
  $scope.currentPage = 1;
  $scope.maxSize = 10;
  $scope.pageChanged = function() {
    getRes();
  };
  $scope.getRes = function(){
    if($scope.currentPage in $scope.allRes){
      $scope.curRes = $scope.allRes[$scope.currentPage];
    }
    else{
      AllRes.getAllRes(1, $scope.currentPage, 1, function(data){
        if(data["type"] && data["type"] == 1)
        {
          var res = data["resource_list"];
          preHandleRes(res);
          $scope.m_uid = data["m_uid"];
          $scope.isPrivate = data["isPrivateDownload"];
          $scope.allRes[$scope.currentPage] = data["resource_list"];
          $scope.totalItems = parseInt(data["size"]);
          $scope.curRes = data["resource_list"];
        }
        else{
          toaster.pop('error', "错误提示", "资源请求失败，请重试", true);
        }
      });
    }
  };
  $scope.download = function(idx){
    downloader.download($scope.curRes[idx], $scope.isPrivate);
  };
  $scope.showDir = function(idx){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'folderModal.html',
      controller: 'folderModalCtrl',
      scope: $scope,
      resolve: {
        index: function () {
          return idx;
        },
        canDownload: function(){
          return true;
        },
          rid: function(){
            return '';
          }
      }
    });
  };
  $scope.getRes();*/
  $scope.msgCenter = $window.msgCenter;
  $scope.clearAllMsg = function () {
    if($window.global.msgCount == 0) {
      toast.showSuccessToast('烦心事已清空, 心情不好就点我吧:)');
      return;
    }
    var param = {};
    param["op"] = 7;
    $http.post('/myFriend', param).success(function(data) {
      if(data["type"] && data["type"] == 1)
      {
        toast.showSuccessToast('清理成功, 整个世界都安静了 O(∩_∩)O');
        $window.global.msgCount = 0;
        $window.msgCenter = [];
      }
      else{
        toast.showErrorToast(data["error"]);
      }
    });
  }; 
  $scope.sysShow = function(msg){
    if(!("sender" in msg) || msg["sender"] == "0")
      return true;
    return false;
  };
  $scope.handleFriend = function (msg, flag){
    var param = {};
    param["op"] = 2;
    param["user"] = msg.sender;
    param["id"] = msg.id;
    param["flag"] = flag;
    $http.post('/myFriend', param).success(function(data) {
      if(data["type"] && data["type"] == 1)
      {
        toast.showSuccessToast(data["result"]["result"]);
        var center = $window.msgCenter;
        for (var i = 0; i < center.length; i++) {
          if(center[i]["id"] == msg.id){
            center.splice(i, 1);
            break;
          }
        }
        if($window.global.msgCount != 0)
          $window.global.msgCount --;
        /*if(flag == 1)
          AllFriend.info.count ++;*/
      }
      else{
        toast.showErrorToast(data["error"]);
      }
    });
  };
  $scope.handle = function (id, idx){
    var param = {};
    param["op"] = 6;
    param["id"] = id;
    $http.post('/myFriend', param).success(function(data) {
      $window.msgCenter.splice(idx, 1);
      if($window.global.msgCount != 0)
        $window.global.msgCount --;
    });
  };
});

app.controller('delFriendModalCtrl', function($scope, $window, localSocket, $modalInstance, $http,delFriendInfo,toaster, AllFriend){
  /*toaster.pop('success', "title", "text",false/true);
  toaster.pop('error', "title", "text",false/true);
  toaster.pop('warning', "title", "text",false/true);
  toaster.pop('note', "title", "text",false/true);*/
  $scope.confirmDelFriend = function(flag){
    if(parseInt(flag) == 0)
    {
      $modalInstance.dismiss('cancel');
      return;
    }
    var param = {}
    param["op"] = 3;
    param["user"] = delFriendInfo["user"];
    param["star"] = delFriendInfo["star"];
    param["uid"] = $window.fbtUID;
    $http.post('/myFriend', param).success(
      function(data) {
        if("type" in data && data["type"] == 1)
        {
          var group = AllFriend.friendGroups[delFriendInfo["groupIdx"]];
          if(group["online"] > 0)
            group["online"] --;
          if(group["total"] > 0)
            group["total"] --;
          for (var i = 0; i < group["friends"].length; i++) {
            if(parseInt(group["friends"][i]["uid"]) == parseInt(delFriendInfo["uid"])){
              group["friends"].splice(i,1);
              break;
            }
          }
          delete AllFriend.friendsUids[""+delFriendInfo["uid"]];
          if(AllFriend.info.count > 0)
            AllFriend.info.count --;
          localSocket.emit("delFriend", delFriendInfo["uid"]);
          /*data = $.parseJSON(data["result"])*/
          toaster.pop('success', "系统提示", data["result"]["result"], true);
        }
        else{
          toaster.pop('error', "错误提示", data["error"], true);
        }
      });
    $modalInstance.dismiss('cancel');
  }
});
app.controller('searchFriendModalCtrl', function($scope, $modalInstance, $http, $filter, toaster){
  $scope.searchResults = [];
  $scope.noResult = false;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.press = function(event, searchFriend){
    if (event.keyCode == 13) {
      $scope.showSearchResult(searchFriend);
      return false;
    }
  }
  $scope.showSearchResult = function(searchFriend){
    var search = $filter('escapeHTML')(searchFriend);//$scope.searchFriend;
    if(!search){
      toaster.pop('warning', "错误提示", "搜索不能为空，请重新输入", true);
      return;
    }
    var param = {}
    param["op"] = 0;
    param["search"] = search;
    $http.post('/myFriend', param).success(function(data) {
      if(data && "type" in data && data["type"] == 1){
        data = JSON.parse(data["result"]);
        if(data.length == 0)
        {
          $scope.noResult = true;
          $scope.searchResults = [];
        }
        else{
          $scope.noResult = false;
          $scope.searchResults = data;
        }
      }
      else{
        $scope.searchResults = [];
        $scope.noResult = true;
      }
    });
  }
  $scope.addFriend = function(user,is_friend){
    if(is_friend == 1){
      toaster.pop('warning', "错误提示", "你们已经是好友，不能重复添加。", true);
      return;
    }
    var param = {}
    param["op"] = 1;
    param["user"] = user;
    $http.post('/myFriend', param).success(function(data) {
      if(data["type"] && data["type"] == 1)
      {
        toaster.pop('success', "系统提示", data["result"]["result"], true);
      }
      else{
        toaster.pop('error', "错误提示", data["error"], true);
      }
    });
  }
});
app.controller("changePasswordModalCtrl", function($scope, $modalInstance, $http, $filter, toaster){
  $scope.pwdMatch = false;
  $scope.originPwd = '';
  $scope.newPwd = '';
  $scope.confirmPwd = '';
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.savePwd = function(){
    if($scope.newPwd != $scope.confirmPwd){
      $scope.pwdMatch = true;
    }
    else{
      $scope.pwdMatch = false;
      var mod_user = {};
      console.log($scope.newPwd);
      console.log($scope.originPwd);
      mod_user["password"] = $.md5($scope.newPwd);
      mod_user["originPwd"] = $.md5($scope.originPwd);
      var str = JSON.stringify(mod_user);
      var param_user =  {"user":str}
      $http.post('/myInfo', param_user).success(function(data) {
        if(data["type"] && data["type"] == 1)
        {
          toaster.pop('success', "系统提示", "修改成功", true);
        }
        else{
          toaster.pop('error', "错误提示", "修改失败，请重试", true);
        }
      });
      $modalInstance.dismiss('cancel');
    }
  }
});
app.controller("changeInfoModalCtrl", function($scope, $modalInstance, $http, $filter, toaster, scselector){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.saveInfo = function(flag){
    if(flag == 1){
      var mod_user = {};
      Object.keys($scope.$parent.myinfo).forEach(function(key) {
        if(!(key in $scope.$parent.preMyinfo))
          mod_user[key] = $scope.$parent.myinfo[key];
        else if($scope.$parent.preMyinfo[key] != $scope.$parent.myinfo[key])
          mod_user[key] = $scope.$parent.myinfo[key];
      });
      var str = JSON.stringify(mod_user);
      var param_user =  {"user":str};
      $http.post('/myInfo', param_user).success(function(data) {
        if(data["type"] && data["type"] == 1)
        {
          toaster.pop('success', "系统提示", "修改成功", true);
          $scope.$parent.preMyinfo = clone($scope.$parent.myinfo);
        }
        else{
          $scope.$parent.myinfo = clone($scope.$parent.preMyinfo);
          toaster.pop('error', "错误提示", "修改失败，请重试", true);
        }
      });
    }
    else{
      $scope.$parent.myinfo = clone($scope.$parent.preMyinfo);
    }
    $modalInstance.dismiss('cancel');
  };
  $scope.selectCollegeClickHandler = function() {
    var title = '选择学校与学院';
    var groups = [
      '北京',
      '上海',
      '黑龙江',
      '吉林',
      '辽宁',
      '天津',
      '安徽',
      '江苏',
      '浙江',
      '陕西',
      '湖北',
      '广东',
      '湖南',
      '甘肃',
      '四川',
      '山东',
      '福建',
      '河南',
      '重庆',
      '云南',
      '河北',
      '江西',
      '山西',
      '贵州',
      '广西',
      '内蒙古',
      '宁夏',
      '青海',
      '新疆',
      '海南',
      '西藏',
      '香港',
      '澳门',
      '台湾',
    ];
    var groupWidth = '50px';
    var entityWidth = '120px';
    var entityCallback = function(group, callback) {
      // fetch from server
      $http({
        url: '/get_university',
        method: 'GET',
        params: {
          province: group
        }
      })
      .success(function(response) {
        if (0 === response.err) {
          var entities = response.list;
          callback(entities);
        }
      })
      .error(function(data,status,headers,config) {
        // 失败处理
        alert('页面加载失败，请重试！')
      });
    };

    var universityEntityCallback = function(university, callback) {
      // fetch from server
      $http({
        url: '/get_university',
        method: 'GET',
        params: {
          university: university
        }
      })
      .success(function(response) {
        if (0 === response.err) {
          var entities = response.list;
          callback(entities);
        }
      })
      .error(function(data,status,headers,config) {
        // 失败处理
        alert('页面加载失败，请重试！')
      });
    };

    var submitCallback = function(entity, college_entity) {
      $scope.$parent.myinfo.school = entity;
      $scope.$parent.myinfo.college = college_entity;
      //alert('submitting entity: ' + entity);
    };
    scselector.show(title, groups, groupWidth, entityWidth, entityCallback, universityEntityCallback, submitCallback);
  };
});
/*<body ng-app="YOUR_APP" ng-controller="MainCtrl">
  <img src="http://www.gravatar.com/avatar/{{ email | gravatar }}">
  <input type="email" ng-model="email" placeholder="Email Address">
  {{ message }}
</body>
<script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.2.10/angular.js"></script>
<script src="app/bower_components/angular-md5/angular-md5.js"></script>
<script>
  angular.module('YOUR_APP', [
    'angular-md5', // you may also use 'ngMd5' or 'gdi2290.md5'
    'controllers'
  ]);
  angular.module('controllers', [])
    .controller('MainCtrl', ['$scope', 'md5', function($scope, md5) {

      $scope.$watch('email' ,function() {
        $scope.message = 'Your email Hash is: ' + md5.createHash($scope.email || '');
      });

    }]);
</script>*/
