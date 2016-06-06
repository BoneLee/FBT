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
app.controller('MyspaceController', function($scope, $location, $http, toaster, AllFriend, fileDialog) {
  $scope.editIconPath = "";
	$scope.urlBase = "/statics/partials/spacePartials/";
  $scope.sideMenus = [
  	{"title":"通知", "url":$scope.urlBase+"inform.html"},
  	{"title":"好友", "url":$scope.urlBase+"friend.html"},
  	{"title":"我的资源", "url":$scope.urlBase+"resource.html"},
  	{"title":"个人档", "url":$scope.urlBase+"person.html"}
  ];
  $scope.spaceTemplate = $scope.urlBase+"friend.html";
  $scope.selected = $scope.sideMenus[1];
  $scope.loadPage = function (menu) {
  	$scope.selected = menu;
  	$scope.spaceTemplate = menu.url;
  };
  $scope.isSelected = function(menu) {
    return $scope.selected === menu;
	};
  $scope.editIcon = function(){
    fileDialog.openFile(function(result){
      var value = result[0];
      if(!value)
        return; 
      resizeImage(value, function(dataurl) {
        $http.get("/editIcon?path=" + encodeURIComponent(dataurl)).success(function(data){
          if("type" in data && data["type"] == 1){
            toaster.pop("note", "系统提示", "修改成功", true);
            $scope.icon = dataurl;
            var scope = angular.element($("#myinfoWrap")).scope();
            if(scope){
              scope.myinfo.icon = dataurl;
            }
          }
          else{
            if("error" in data)
              toaster.pop("error", "系统提示", data["error"], true);
            else
              toaster.pop("error", "系统提示", "修改失败，请重试", true);
          }
        });
      });
    }, false, [".png",".jpg",".gif",".jpeg"]);
  };
  AllFriend.get(function(data){
      $scope.friendGroups = [];
      $scope.friendsUids = {};
      $scope.friendsUids[window.fbtUID+''] = 0;
      $scope.friendsUids['null'] = 0;
      if(data){          
        $scope.icon = data["icon"];
        $scope.nick_name = data["nick_name"];
        $scope.fb_coin = data["fb_coin"];
        $scope.shuo = data["shuo"];
        $scope.count = data["count"];
        var starFriendGroup = {"index":0,"title":"我粉的","id":"friendstar","online":0,"total":0,"friends":[]};
        $scope.friendGroups.push(starFriendGroup);
        var friendGroup = {"index":1,"title":"好友","id":"myfriend","online":data["count_online"],"total":data["count"],"friends":data["friends"]};
        $scope.friendGroups.push(friendGroup);
        for (var i = 0; i < data["friends"].length; i++) {
          $scope.friendsUids[data["friends"][i]["uid"]+''] = 0;
        }
      }        
  });
});
app.controller('FriendController', function($scope, $modal, toaster) {
  $scope.curGroup = 1;
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
  $scope.groupChatPress = function(event, myGroupChat){
    var keynum = event.keyCode || event.which;
    if(event.ctrlKey && keynum == 13 || keynum == 10){
      $scope.publish(myGroupChat);
    }
  };
  $scope.publish = function(myGroupChat){
    //{"type":3,"recv":"","sender":who,"msg":content,"time":time}
    var content = myGroupChat.trim();//$('#myGroupChat').val().trim();
    if(!content)
    {
      toaster.pop('warning', "系统提示", "内容为空不能发送，请重新输入");
      return;
    }
    if(content.length > 200)
    {
      toaster.pop('warning', "系统提示", "内容过长，应少于200字");
      return;
    }

    var time = (new Date()).Format("hh:mm MM-dd-yyyy");
    var data = {"uid":window.fbtUID,"token":window.token,"type": 3, "recv":"", "sender":getCookie("fbt_user"),"msg":content,"time":time,"name":window.nick_name};
    if(!window.ws){
      setTimeout("window.ws.send(JSON.stringify(data));",2000);
    }
    else
      window.ws.send(JSON.stringify(data));
    //console.log(content);
    data["name"] = "我";
    appendGroupChatToView(data);
    //$('#myGroupChat').val("");
    $scope.myGroupChat = "";

    //根据用户发送内容，自动回复
    if(window.setting["chat_robot"] == 1) {
      (function autoReply(content) {
        var rules = {
          "F币规则": "点击【排行榜】（资源库右上角），可进入查看【F币规则】。因细小变动，具体请以官网为准",
          "赚F币": "多多上传【优质资源、首发资源】、ps：学习资源F币更多哟；多多在线，做种【供水】；多去【朋友圈】或者好友个人中心下载资源(免费)；多多【分享】",
          "赚F币": "多多上传【优质资源、首发资源】、ps：学习资源F币更多哟；多多在线，做种【供水】；多去【朋友圈】或者好友个人中心下载资源(免费)；多多【分享】",
          "网络不佳": "对方突然下线或者不在线，或者您已掉线，请等待…或者重启软件，还是不行的话请联系管理员: 1026250255",
          "稍后重试": "对方突然下线或者不在线，或者您已掉线，请等待…或者重启软件，还是不行的话请联系管理员: 1026250255",
          "排队中": "最多同时下载两个，剩余任务显示排队中，请稍后",
          "加群": "新用户欢迎加入【校园星空官方群】6群339674514，或7群194239857，或8群389730107。加群后请先看群公告，谢谢您的支持！ 另，欢迎关注【fbt百度贴吧】，发帖留言你的疑问和建议，我们会不断改进 ~！O(∩_∩)O~",
          "批量": "暂时只能上传单个资源，或者压缩包。【文件夹上传、显示、下载】功能正在完善中。。。敬请期待。。O(∩_∩)O~~",
          "文件夹": "暂时只能上传单个资源，或者压缩包。【文件夹上传、显示、下载】功能正在完善中。。。敬请期待。。O(∩_∩)O~~",
          "怎么加好友": "好友列表右下角【+添加校园星空好友】",
          "查看我的": "点击资源库主页【我的分享图标】，或者点击聊天室【个人头像】",
          "查看上传": "点击资源库右下角【N个资源正在上传】，可查看正在上传的资源和上传进度，以及取消上传",
          "下载不了": "检查自己是否有连接【ipv6】校园网，软件暂不支持ipv4下载；查看资源是否有人【在线】即 [在线数/总数]；检查自己是否【掉线】；实在米办法就【重启软件】试试……",
          "卡": "O.O不可能吧，程序猿已经优化了。。。O(∩_∩)O~~",
          "上传的搜不到": "资源上传后，请【等待审核】…审核菌也是蛮拼的，最迟第二天即可显示； fbt已有一样的资源，你的资源信息被合并在首发者名下，可在评论里看到",
          "怎么删除": "【上传途中的资源】可点X取消上传；【上传完成的资源】可选择:移动电脑原文件、更改资源名、删除文件等方式删除",
          "电视看不了": "重装一下Windows Media Player，在CMD里输入regsvr32 wmnetmgr.dll，regsvr32 wmstream.dll"
        }
        for(var ruleKey in rules) {
          if(content.indexOf(ruleKey) > -1) {
            var time = (new Date()).Format("hh:mm MM-dd-yyyy");
            var data = {"uid":null,"token":window.token,"type": 3, "recv":"", "sender":getCookie("fbt_user"),"msg":"关于【"+htmlencode(ruleKey)+"】："+rules[ruleKey],"time":time,"name":"x校园星空小兔"};
            appendGroupChatToView(data);
          }
        }
      }(content));
    }
  };
  $scope.addFriendByNickname = function(nickname){
    var param = {}
    param["op"] = 8;
    param["nick_name"] = nickname;
    $http.post('/myFriend', param).success(function(data) {
      if(data["type"] && data["type"] == 1)
      {
        toaster.pop('success', "系统提示", data["result"]["result"], true);
      }
      else{
        toaster.pop('error', "错误提示", data["error"], true);
      }
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
      $scope.myinfo["department"] = "111";
      $scope.myinfo["freshyear"] = "2015";
      $scope.myinfo["weibo"] = "2014";
      $scope.myinfo["qq"] = "2014";
      $scope.myinfo["phone"] = "2014";
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
// app.service("MyResStateService", function() {
//   this.current_page = {0: 1, 1: 1};
//   this.is_audit = 0;
// });
// app.controller("MyresController", function($scope, $routeParams, $modal, MyRes, pagination, toaster, MyResStateService){
//   $scope.allRes = {};
//   $scope.curRes = [];
//   $scope.is_audit = MyResStateService.is_audit;
//   $scope.page = {
//     'page0': {
//       'current_page': MyResStateService.current_page[0],
//       'max_size': 3
//     },
//     'page1': {
//       'current_page': MyResStateService.current_page[1],
//       'max_size': 3
//     }
//   };

//   $scope.getRes = function(){
//     var page_key = 'page' + $scope.is_audit;
//     var current_page = $scope.page[page_key].current_page;
//     if($scope.is_audit in $scope.allRes && current_page in $scope.allRes[$scope.is_audit]){
//       $scope.curRes = $scope.allRes[$scope.is_audit][current_page];
//     }
//     else{
//       MyRes.getMyRes($scope.is_audit, current_page, function(data){
//         if('err' in data && data["err"] == 0)
//         {
//           var res = data["resource_list"];
//           angular.forEach(res, function(v) {
//             if ('unpass_reason' in v) {
//               v['unpass'] = true;
//             } else {
//               v['unpass'] = false;
//               v['unpass_reason'] = '';
//             }
//             v['str'] = angular.toJson(v);
//           });

//           $scope.page[page_key].total_page = parseInt(data["total_page"]);
//           // 潜在bug：如果此页res列表不满整页，那items_per_page值有误
//           $scope.page[page_key].items_per_page = res.length;
//           $scope.page[page_key].total_items = $scope.page[page_key].total_page * $scope.page[page_key].items_per_page;
//           if($scope.page[page_key].total_page > 1){
//             $scope.page[page_key].noPagination = true;
//           } else {
//             $scope.page[page_key].noPagination = false;
//           }

//           if (res.length > 0) {
//             $scope.page[page_key].noResult = false;
//           } else {
//             $scope.page[page_key].noResult = true;
//           }

//           $scope.curRes = res;

//           if (!($scope.is_audit in $scope.allRes)) {
//             $scope.allRes[$scope.is_audit] = {};
//           }
//           $scope.allRes[$scope.is_audit][$scope.page[page_key].current_page] = res;
//         }
//         else{
//           toaster.pop('error', "错误提示", "资源请求失败，请重试", true);
//         }
//       });
//     }
//   };

//   $scope.btnClick = function(is_audit) {
//     $scope.is_audit = is_audit;
//     MyResStateService.is_audit = is_audit;
//     $scope.getRes();
//   };

//   $scope.pageChange = function() {
//     MyResStateService.current_page[$scope.is_audit] = $scope.page['page'+$scope.is_audit].current_page;
//     $scope.getRes();
//   };

//   // 首次加载资源
//   $scope.getRes();
// });

app.controller("InformController", function($scope, $modal, AllRes, downloader, toaster, $window){

  
});

app.controller('delFriendModalCtrl', function($scope, $modalInstance, $http,delFriendInfo,toaster){
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
    param["uid"] = window.fbtUID;
    $http.post('/myFriend', param).success(
      function(responseData) {
        if("type" in data && data["type"] == 1)
        {
          var group = $scope.$parent.$parent.friendGroups[groupIdx];
          group["online"] --;
          group["total"] --;
          for (var i = 0; i < group["friends"].length; i++) {
            if(parseInt(group["friends"]["uid"]) === parseInt(delFriendInfo["uid"])){
              group["friends"].splice(i,1);
              break;
            }
          }
          delete $scope.$parent.$parent.friendsUids[""+delFriendInfo["uid"]];
          window.socket.emit("delFriend", confirm.attr("index"));
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
  $scope.noResult = true;
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
        }
        else{
          $scope.noResult = false;
          $scope.searchResults = data;
        }
      }
      else{
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

  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.savePwd = function(originPwd, newPwd, confirmPwd){
    if(newPwd != confirmPwd){
      $scope.pwdMatch = true;
    }
    else{
      $scope.pwdMatch = false;
      var mod_user = {};
      mod_user["password"] = $.md5(password);
      mod_user["originPwd"] = $.md5(originPwd);
      var str = JSON.stringify(mod_user);
      var param_user =  {"user":str}
      $http.post('/myInfo', param_user).success(function(data) {
        if(data["type"] && data["type"] == 1)
        {
          toaster.pop('success', "系统提示", data["result"]["result"], true);
        }
        else{
          toaster.pop('error', "错误提示", data["error"], true);
        }
      });
      $modalInstance.dismiss('cancel');
    }
  }
});

app.controller("changeInfoModalCtrl", function($scope, $modalInstance, $http, $filter, toaster){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.saveInfo = function(flag){
    if(flag == 1){
      var mod_user = {};
      Object.keys($scope.$parent.preMyinfo).forEach(function(key) {
        if($scope.$parent.preMyinfo[key] != $scope.$parent.myinfo[key])
          mod_user[key] = $scope.$parent.myinfo[key];
      });
      var str = JSON.stringify(mod_user);
      var param_user =  {"user":str};
      $http.post('/myInfo', param_user).success(function(data) {
        if(data["type"] && data["type"] == 1)
        {
          toaster.pop('success', "系统提示", data["result"]["result"], true);
          $scope.$parent.preMyinfo = clone($scope.$parent.myinfo);
        }
        else{
          $scope.$parent.myinfo = clone($scope.$parent.preMyinfo);
          toaster.pop('error', "错误提示", data["error"], true);
        }
      });
    }
    else{
      $scope.$parent.myinfo = clone($scope.$parent.preMyinfo);
    }
    $modalInstance.dismiss('cancel');
  };
});
