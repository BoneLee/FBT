/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('RootController', function($scope, $window, $location, localSocket, WinManager, $http, $modal, share, toast, Adv) {
  $scope.global = $window.global;
  $window.setting = {};
  $http.get("/setting/init").success(function(data){
    $window.setting = data;
    if(("first" in $window.setting) && $window.setting["first"] != 0){
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'fbRuleModal.html',
        controller: 'fbRuleCtrl',
      });
      $window.setting["first"] = 0;
      localSocket.emit("first", "1"); }
    if($window.setting.version > 8)
      $scope.shouldShowFrame = true;
    else
      $scope.shouldShowFrame = false;
  });
  $scope.$on('$routeChangeSuccess', function() {
    //console.log($location.url());
    var workspaceHeight = ['home', 'search', 'top'].indexOf($location.url().split('/', 2)[1]) > -1 ? 60 + 30: 60 + 30 + 30;
    $scope.workspaceHeight = $window.innerHeight - workspaceHeight;
  });
  angular.element($window).on('resize', function() {
    $scope.$apply(function() {
      var workspaceHeight = ['home', 'search', 'top'].indexOf($location.url().split('/', 2)[1]) > -1 ? 60 + 30: 60 + 30 + 30;
      $scope.workspaceHeight = $window.innerHeight - workspaceHeight;
    });
  });

  $scope.resetPageNum = function() {
    delete $window.currentPageNum;
    delete $window.currentSortBy;
  };

  $scope.isMac = ($window.setting.platform + '').toLowerCase() == 'darwin';
  $scope.minApp = function() {
    WinManager.min();
  };
  $scope.maxApp = function() {
    WinManager.max();
  };
  $scope.closeApp = function() {
    WinManager.close();
  };
  $scope.shareClickHandler = function() {
    share.show({
      title: '后六维时代,资源下载哪家强？',
      desc: 'FBT，是北大清华中科院小伙伴联合开发的校内影视、学习资源分享平台，免流量神速下载，最高可到20M/s，百度一下FBT。',
      url: 'http://www.friendsbt.com/?uid=' + $window.fbtUID,
      weixin: 'http://weixin.qq.com/r/MXULEy7E-XOCrWpw9yAj',
      image: 'http://friendsbt.com/static/img/share.jpg'
    });
  };
  // Adv
  $scope.$on('update-adv', function(event, adv) {
    $scope.adv = adv;
  });
  $scope.openAdvLink = function(url) {
    WinManager.openExternal(url);
    toast.showStickyNoticeToast('已使用浏览器打开');
  };
});

app.controller('RegisterController', function($scope, $window, $location, $http, scselector, WinManager){
  $scope.alertMsg = '';
  $scope.gender = "女";
  $scope.schools = schools;

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
      $scope.school = entity;
      $scope.college = college_entity;
      //alert('submitting entity: ' + entity);
    };
    scselector.show(title, groups, groupWidth, entityWidth, entityCallback, universityEntityCallback, submitCallback);
  };

  function validate(){
    if (!$scope.readAgreement){
      $scope.alertMsg = "请先勾选接受注册协议";
      return false; 
    }
    if ($scope.school.length > 20){
      $scope.alertMsg = "学校名称最多为20个字";
      return false;
    }
    if($scope.school.length == 0){
      $scope.alertMsg = "请选择学校";
      return false;
    }
    if($scope.college.length == 0){
      $scope.alertMsg = "请选择学院";
      return false;
    }
    if($scope.nickName.length > 10){
      $scope.alertMsg = "昵称最多为10个字";
      return false;
    }
    else if($scope.email == "" || $scope.password == "" || $scope.confirmPassword == "")
    {
      $scope.alertMsg = "用户名或者密码未填写.";
      return false;
    }
    else if($scope.password.length < 6){
      $scope.alertMsg = "密码小于6位，为了您的账户安全，请重设";
      return false;
    }
    else if($scope.password != $scope.confirmPassword){
      $scope.alertMsg = "两次密码输入不一致，请检查";
      return false;
    }
    else if ((null == $scope.email.match(/^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$/))) {
      $scope.alertMsg = "非法的邮箱格式.";
      return false;
    }
    else if($scope.referName != "" && ($scope.referName == $scope.nickName || $scope.referName == $scope.realName)){
      $scope.alertMsg = "推荐人请不要与所填昵称或者真名相同";
      return false;
    }
    return true;
  }
  function registration() {
    var message = {};
    message["college"] = $scope.college;
    message["school"] = $scope.school;
    message["gender"] = $scope.gender;
    message["user"] = $scope.email;
    message["pwd"] = $.md5($scope.password);
    message["nick"] = $scope.nickName;
    message["name"] = $scope.realName;
    message["refer"] = $scope.referName;
    message["next"] = "/login";
    $scope.clicked = true;
    $http.post("/registration", message).success(function(response) {
      $scope.clicked = false;
      if(response["type"] == 1)
      {
        //need email verify ?
        $scope.alertMsg = response["result"]["result"];
      }
      else{
        if(response["error"])
          $scope.alertMsg = response["error"];
        else
          $scope.alertMsg = "注册出现了一点小故障，您可以去试试是否可以登录。";
      }
    }).error(function(){
      $scope.clicked = false;
    });
  }
  $scope.confirm = function(){
    if ($scope.password != $scope.confirmPassword) {
      $scope.alertMsg = "两次密码输入不一致，请检查";
    }
    else
    {
      $scope.alertMsg = '';
    }
  }

  $scope.closeAlert = function(){
    $scope.alertMsg = '';
  };
  $scope.toLogin = function (){
    $location.path("/login");
  };
  $scope.agreement = function(){
    WinManager.open("http://www.friendsbt.com/agreement.htm");
  };
  $scope.submit = function(){
    if (validate()) {
      registration();
    }
  };
});

app.controller('LoginController', function($scope, $window, $http, $location, $modal, toast, localSocket, AllFriend, WinManager, HisRes, Adv){
  var hints = ["注意：如果分享的文件位于移动存储设备中，打开软件前请确保移动设备接入电脑。",
                    "点小人图标，进入个人中心，查看积分和添加好友；点好友昵称，可以查看其资源主页。",
                    "点右上角积分榜旁边的分享图标，可以查看自己的资源，在个人档里完善信息和头像。",
                    "私有圈是你所有好友的资源的集合，下载永久免积分。好友越多，免积分资源越多！",
                    "点击FBT，可以返回主页或打开官网。官网可以了解积分规则：www.friendsbt.com。"];
  $scope.global = $window.global;
  var auto = 1;
  if($window.global.shouldDisconnect){
    auto = 0;
    $scope.global.isLogin = false;
  }
  $scope.hint = hints[Math.floor(Math.random()*hints.length)];
  $scope.alertMsg = '';
  $scope.remenber = false;
  $scope.logined = false;
  $scope.closeAlert = function(){
    $scope.alertMsg = '';
  };
  $scope.toCoin = function (){
    WinManager.open("http://www.friendsbt.com/fmall.html", "_blank");
  };
  $scope.toRegister = function (){
    $location.path("/register");
  };
  function validate(){
    if($scope.user == "" || $scope.pwd == "")
    {
      $scope.alertMsg = "用户名或者密码未填写.";
      return false;
    }
    return true;
  }
  function getToken(callback){
    $http.get('/token').success(
        function(data){
          $window.token = data["result"];
          $window.platform = data["platform"];
          if(callback)
            callback();
        }
    ).error(function(){
      toast.showErrorToast("您的网络可能出了点问题");
    });
  }
  function beforeLogin(){
    //$document.body.style.cursor='wait';
    if($window.token){
      login();
    }
    else{
      getToken(login);
    }
  }
  function login() {
    var message = {}
    message["user"] = $scope.user;
    message["pwd"] = $.md5($scope.pwd);
    message["next"] = "/";
    if($scope.remenber)
        message["password"] = $scope.pwd;
    $scope.logined = true;
    $http.post("/login", message).success(function(response) {
      //console.log(response);
      //$document.body.style.cursor='default';
      $scope.logined = false;
      if(response["type"] == 1)
      {
        //console.log("login");
        AllFriend.init();
        Adv.init();
        HisRes.getHis();
        $scope.global.isLogin = true;
        // var url = 'http://xinghuan.com/#/?uid=' + $window.fbtUID + '&token=' + $window.token;
        // WinManager.openExternal(url);
        $location.path("/resource");
      }
      else{
        //console.log(response);
        if("error" in response)
          $scope.alertMsg = response["error"];
        else
          $scope.alertMsg = "用户名或者密码错误";
        $scope.pwd = '';
      }
    }).error(function(){
      $scope.logined = false;
      toast.showErrorToast("您的网络可能出了点问题");
    });
  }
  localSocket.emit("init");
  if($window.setting["user"]){
    $scope.user = $window.setting["user"];
    $scope.pwd = $window.setting["pwd"];
    $scope.remenber = true;
    if($window.setting["auto_log"] == 1 && auto == 1){
      if (validate()) {
        beforeLogin();
      }
    }
  }

  $scope.reset = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'resetModal.html',
      controller: 'resetController',
    });
  };  
  $scope.login_click = function (){
    if (validate()) {
      beforeLogin();
    }
    return false;
  }
  $scope.loginPress = function(event) {
    /* Act on the event */
    var keynum = event.keyCode;
    if (keynum == 13) {
      if (validate()) {
        beforeLogin();
      }
      return false;
    }
  }
  getToken();
});

app.controller('fbRuleCtrl', function($scope, $window, $modalInstance, WinManager){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.toWeb = function(){
    $modalInstance.dismiss('cancel');
    WinManager.open("http://www.friendsbt.com/fmall.html");
  }
});

app.controller('resetController', function($scope, $http, toast, $modalInstance){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.resetPwd = function(flag){
    if(flag == 1 || flag == "1"){
        var user = $scope.resetEmail;
        if(user){
            $http.get("/reset?user="+user).success(function(data){
              if(data["type"] == 0)
                toast.showErrorToast("请求失败，请重试");
              else
                toast.showSuccessToast("重置密码的链接已经发到您的邮箱，请稍后查收");
            });
        }
    }
    $modalInstance.dismiss('cancel');
  }
});

app.controller('fbRankCtrl', function($scope, $http, toast, loading, $window, $rootScope, $location, safeApply){
  $rootScope.$broadcast('refreshSubheaderEvent', $location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);

  $scope.allRanks = [];
  $scope.allRanks[0] = [];
  $scope.allRanks[1] = [];
  $scope.allRanks[2] = [];
  $scope.winW = $window.innerWidth;
  $scope.winH = $window.innerHeight;
  $scope.tabs = ["积分商城", "周排行", "月排行", "F币富豪榜"];
  $scope.curIdx = 0;
  $scope.showFbRank = function(idx){
    $scope.curIdx = idx;
    if($scope.allRanks[idx-1] && $scope.allRanks[idx-1].length != 0)
      return;
    loading.show();
    var gIdx = idx;
    $http.get("/fbrank?type="+gIdx).success(function(data){
      loading.hide();
      if(data["type"] == 0)
      {
        toast.showErrorToast("网络出现了故障，请重试");
        return;
      }
      safeApply($rootScope, function() {
        $scope.allRanks[idx-1] = data["data"];
      });
    }).error(function(){
      loading.hide();
      toast.showErrorToast("网络出现了故障，请重试");
    });
  };
});

app.controller('HeaderController', function(WinManager, $scope, $rootScope, $window, $location, $modal, Subheader, selector, AllFriend, toast) {
  $scope.info = AllFriend.info;
  $scope.global = $window.global;

  $rootScope.$headerScope = $scope;

  $scope.alertRule = function(){
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'fbRuleModal.html',
        controller: 'fbRuleCtrl',
      });
  };
  $scope.alertSetting = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'settingModal.html',
      controller: 'settingCtrl',
    });
  };

  /*$scope.alertSetting = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'settingModal.html',
      controller: 'settingCtrl',
    });
  };*/

  $scope.alertHelp = function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'helpModal.html',
      controller: 'helpCtrl',
    });
  };

  $scope.min = function(){
    WinManager.min();
  };
  $scope.max = function(){
    WinManager.max();
  };
  $scope.close = function(){
    WinManager.close();
  };

  $scope.uploadFile = function(){
    //判断积分是否大于3000
    if($window.global.fbCoin >= 3000){
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'uploadContentModal.html',
        controller: 'uploadContentCtrl',
        resolve: {
          extInfo: function () {
            return null;
          }
        }
      });
    }
    else{
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'noCoinModal.html',
        controller: 'noCoinCtrl'
      });
    }
  };

  $scope.isCurrentTab = function(tab) {
    //var currentTab = $location.url().split('?')[0].replace('/', '').replace(/-.+/, '');
    var currentTab = $location.url().split('?')[0].replace('/', '').replace(/-.+/, '').split('/')[0];
    return currentTab == tab;
  };

  $scope.isNoHover = function(tab) {
    return ['学习社区', '影音娱乐', '实用工具'].indexOf(tab) != -1;
  };

  $scope.isCompact = function(tab) {
    return $scope.subheaderTabs.length > 13;
  };

  $scope.selectHeaderTab = function(tab) {
    if(tab === 'resource') {
      //$scope.subheaderTabs = ['学习社区', '学校', '推荐', '影音娱乐', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '实用工具', '软件', '其它', '电视'];
      $scope.subheaderTabs = ['校园星空', '学习', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '软件', '其它', '电视'];
      $scope.selectedSubheaderTab = '电影';

      //Set searchKeywords input
      $scope.selectedResourceType = '电影';
    }
    else if(tab === 'circle') {
      //$scope.subheaderTabs = ['全部', '学习', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '软件', '其它'];
      $scope.subheaderTabs = ['学习', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '软件', '其它'];
      $scope.selectedSubheaderTab = '电影';
      toast.showNoticeToast('朋友圈改版啦，仅显示在线资源哦！');
    }
    else if(tab === 'reward') {
      $scope.subheaderTabs = ['全部', '学习', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '软件', '其它'];
      $scope.selectedSubheaderTab = '全部';
    }
    else {
      $scope.subheaderTabs = null;
      $scope.selectedSubheaderTab = null;
    }
    Subheader.setIndex($scope.selectedSubheaderTab);
  };

  $rootScope.$on('refreshSubheaderEvent', function(event, tab) {
    //console.log('refreshSubheader current tab: ' + tab)
    if (tab.search(/\//) >= 0)
      $scope.selectHeaderTab(tab.replace(/\//, ''));
  });

  $scope.subheaderTabClickHandler = function(tab) {
    if(tab == '学校' || tab == '推荐' || tab == '校园星空') {
      //临时使用网页学习版
      var isMac = ($window.setting.platform + '').toLowerCase() == 'darwin';
      var url = 'http://xinghuan.com/#/?uid=' + $window.fbtUID + '&token=' + $window.token;
      if(isMac) {
        WinManager.open(url);
      }
      else {
        WinManager.openExternal(url);
        toast.showStickyNoticeToast('已使用浏览器打开校园星空网页，请注意查看。校园星空的大学课程资源由FBT用户共同参与建设。欢迎您多多上传自己的大学往届考题、课程作业、学习心得、笔记、课件、电子书等有益大家高效学习的课程资源，FBT将给您大额积分奖励～每门课程奖励2000F币，优质学习资源奖励更多～分享高贵，造福学弟学妹～');
      }
      return;
    }
    if(tab == '电视') {
      WinManager.open('http://www.friendsbt.com/tv');
      return;
    }

    $scope.selectedSubheaderTab = tab;
    Subheader.setIndex($scope.selectedSubheaderTab);

    var header = $location.url().split('?')[0].replace('/', '').replace(/-.+/, '').split('/')[0];
    var pathMapper = {
      '学校': 'college', 
      '推荐': 'recommendation',
      '电影': 'movie',
      '剧集': 'episode',
      '音乐': 'music',
      '动漫': 'cartoon',
      '游戏': 'game',
      '综艺': 'variety',
      '体育': 'sport',
      '软件': 'software',
      '其它': 'other',
      '学习': 'study',
      '全部': ''
    };
    if(tab in pathMapper) {
      var path;
      if(pathMapper[tab]) {
        path = '/' + header + '-' + pathMapper[tab];
        $location.path(path);
      }
      else {
        path = '/' + header;
        $location.path(path);
      }
      delete $window.currentPageNum;
      delete $window.currentSortBy;
      console.log('Going to ' + path);
    }
    else {
      console.log('Cannot handle ' + tab);
    }

    //Set searchKeywords input
    if(['全部', '学习', '电影', '剧集', '音乐', '动漫', '游戏', '综艺', '体育', '软件', '其它'].indexOf(tab) != -1)
      $scope.selectedResourceType = tab;
    else if(tab == '学校' || tab == '推荐')
      $scope.selectedResourceType = '学习';
    else
      $scope.selectedResourceType = '全部';
  };

  $scope.searchKeywordsClickHandler = function(searchKeywords) {
    delete $window.currentPageNum;
    delete $window.currentSortBy;
    searchKeywords && $location.path('/search/' + searchKeywords);
    //$scope.searchKeywords = '';

    //Set subheaders
    $scope.subheaderTabs = null;
    $scope.selectedSubheaderTab = null;
    Subheader.setIndex($scope.selectedSubheaderTab);
  };


  $scope.selectCollegeClickHandler = function() {
    var title = '选择学校';
    var groups = [
      '北京北京北京北京北京北京北京',
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
    var groupWidth = '72px';
    var entityWidth = '120px';
    var entityCallback = function(group, callback) {
      // fetch from server
      var entities = [
            '哈尔滨工业大学',
            '哈工程东北林大',
            '东北农业大学',
            '哈尔滨医科大学',
            '黑龙江中医药',
            '黑工程',
            '黑龙江科技大学',
            '哈尔滨学院',
            '哈尔滨体院',
            '东方学院',
            '黑龙江大学',
            '哈尔滨商业大学',
      '北京北京北京北京北京北京北京',
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
      callback(entities);
    };
    var submitCallback = function(entity) {
      console.log('submitting entity: ' + entity);
      $scope.$parent.selectedCollege = entity;
    };
    selector.show(title, groups, groupWidth, entityWidth, entityCallback, submitCallback);
  };
});

app.controller("settingCtrl", function($scope, $modalInstance, $window, $http, fileDialog, toast){
  $scope.setting = {};
  if($window.setting["upload_speed"]){
    var delta = 1024*1024*1.0;
    var speed = ($window.parseInt($window.setting["upload_speed"])/delta).toFixed(2);
    $scope.setting.set_upload_speed = speed;
  }
  else
    $scope.setting.set_upload_speed = "2.00";
  if ($window.setting["downloadSaveDir"]) {
    $scope.setting.text_download_path = $window.setting["downloadSaveDir"];
  } else {
    $scope.setting.text_download_path = "尚未设置下载目录";
  }
  if($window.setting["tray"] == 0)
    $scope.setting.exit_tray = false;
  else
    $scope.setting.exit_tray = true;
  if($window.setting["boot"] == 0)
    $scope.setting.auto_login = false;
  else
    $scope.setting.auto_login = true;
  if($window.setting["auto_log"] == 0)
    $scope.setting.auto_log = false;
  else
    $scope.setting.auto_log = true;
  if($window.setting["voice"] == 0)
    $scope.setting.voice = false;
  else
    $scope.setting.voice = true;
  if($window.setting["chat_robot"] == 0)
    $scope.setting.chat_robot = false;
  else
    $scope.setting.chat_robot = true;
  if($window.setting["allow_bg"] == 0)
    $scope.setting.allow_bg = false;
  else
    $scope.setting.allow_bg = true;
  if($window.setting["friends_online_inform"] == 0)
    $scope.setting.friends_online_inform = false;
  else
    $scope.setting.friends_online_inform = true;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.selectDir = function(){
    fileDialog.openDir(function(result){
      var value = result[1];
      if(!value)
        return;
      $scope.setting.text_download_path = value;
      $("#settingPath").text($scope.setting.text_download_path);
    });
  }
  $scope.saveSettings = function (){
    var speed = $scope.setting.set_upload_speed;
    speed = $window.parseInt(speed);
    if(!speed || speed < 0){
      toast.showErrorToast("资源索引生成速度设置不合法");
      return;
    }
    if(speed > 20){
      toast.showWarningToast("资源索引生成速度最大为20哦");
      speed = 20;
    }
    var path = $scope.setting.text_download_path;
    var tray;
    var boot;
    var auto;
    var v4 = 1;
    var voice;
    var chat_robot;
    var bg;
    var friends_online_inform;
    if($scope.setting.voice)
      voice = 1;
    else
      voice = 0;
    if($scope.setting.auto_log)
      auto = 1;
    else
      auto = 0;
    if($scope.setting.auto_login)
      boot = 1;
    else
      boot = 0;
    if($scope.setting.exit_tray)
      tray = 1;
    else
      tray = 0;
    if($scope.setting.chat_robot)
      chat_robot = 1;
    else
      chat_robot = 0;
    /*if($("#allow_v4_download").hasClass('checked'))
      v4 = 1;
    else
      v4 = 0;*/
    if($scope.setting.allow_bg)
      bg = 1;
    else
      bg = 0;
    if($scope.setting.friends_online_inform)
      friends_online_inform = 1;
    else
      friends_online_inform = 0;
    $http.get("/setting/save?path="+path+"&tray="+tray+"&boot="+boot+"&auto_log="+auto+"&allow_v4_download="+v4+"&voice="+voice+"&upload_speed="+speed+"&chat_robot="+chat_robot+"&allow_bg="+bg+"&friends_online_inform="+friends_online_inform).success(function(data){
      if (data["type"] == 1) {
        //点击保存设置后 隐藏对话框
        $modalInstance.dismiss('cancel');
        if($window.setting["allow_bg"] != bg){
          //set bg
        }
        $window.setting["downloadSaveDir"] = path;
        $window.setting["auto_log"] = auto;
        $window.setting["allow_v4_download"] = v4;
        $window.setting["allow_bg"] = bg;
        $window.setting["voice"] = voice;
        $window.setting["tray"] = tray;
        $window.setting["boot"] = boot;
        $window.setting["chat_robot"] = chat_robot;
        $window.setting["upload_speed"] = speed*1024*1024;
        $window.setting["friends_online_inform"] = friends_online_inform;
        toast.showSuccessToast("保存成功");
      } else {
        $scope.setting.text_download_path = '无效下载路径';
        $("#settingPath").text($scope.setting.text_download_path);
        toast.showErrorToast("保存失败");
      }
    }); 
  };
  $scope.resetSettings = function (){
    $window.setting["downloadSaveDir"] = $window.setting["defaultDownloadDir"];
    $scope.setting.text_download_path = $window.setting["downloadSaveDir"];
    $("#settingPath").text($scope.setting.text_download_path);
    var path = $window.setting["downloadSaveDir"];
    var tray = 1;
    $window.setting["tray"] = 1;
    var boot = 0;
    $window.setting["boot"] = 0;
    var auto = 0;
    $window.setting["auto_log"] = 0;
    var v4 = 0;
    var bg = 1;
    $window.setting["allow_v4_download"] = v4;
    $window.setting["allow_bg"] = bg;
    var voice = 1;
    $window.setting["voice"] = 1;
    var speed = 2;
    var chat_robot = 1;
    $window.setting["upload_speed"] = 2;
    $window.setting["friends_online_inform"] = 1;
    $http.get("/setting/save?path="+path+"&tray="+tray+"&boot="+boot+"&auto_log="+auto+"&allow_v4_download="+v4+"&voice="+voice+"&upload_speed="+speed+"&chat_robot="+chat_robot+"&allow_bg="+bg+"&friends_online_inform="+friends_online_inform).success(function(data){
      if (data["type"] == 1) {
        toast.showSuccessToast("恢复默认成功");
        $scope.setting.set_upload_speed = "2.00";
        //set bg
      } else {
        $scope.setting.text_download_path = '无效下载路径';
        $("#settingPath").text($scope.setting.text_download_path);
        toast.showErrorToast("重置失败");
      }
    }); 
  }
});

app.controller('QuickNavController', function($scope, Subheader, $location) {
  var navs = $location.url().split('?')[0].replace('/', '').split(/[\-\/]/);
  var tmp = [];
  var mapper = {
    'resource': ['资源库', 'resource'],
    'circle': ['朋友圈', 'circle'],
    'reward': ['悬赏', 'reward'],
    'college': ['学校', 'college'],
    'recommendation': ['推荐', 'recommendation'],
    'details': ['详情', 'recommendation'],
    'my': ['我的悬赏', 'my'],
    'study': ['学习', 'study'],
    'movie': ['电影', 'movie'],
    'episode': ['剧集', 'episode'],
    'music': ['音乐', 'music'],
    'cartoon': ['动漫', 'cartoon'],
    'game': ['游戏', 'game'],
    'variety': ['综艺', 'variety'],
    'sport': ['体育', 'sport'],
    'software': ['软件', 'software'],
    'other': ['其它', 'other'],
    'search': ['搜索结果', 'search'],
    'home': ['动态', 'home'],
  };
  for(var i = 0; i < navs.length; i++) {
    if(navs[i] == 'details') {
      tmp.push('<a>' + mapper[navs[i]][0] + '</a>');
      break;
    }
    if(navs[i] == 'search') {
      $scope.navs = '搜索“' + decodeURIComponent(navs[i+1]) + '”';
      return;
    }

    if(navs[i] in mapper) {
      if(i == 1)
        tmp.push('<a href="#/' + mapper[navs[i-1]][1] + '-' + mapper[navs[i]][1] + '">' + mapper[navs[i]][0] + '</a>');
      else
        tmp.push('<a href="#/' + mapper[navs[i]][1] + '">' + mapper[navs[i]][0] + '</a>');
    }
    else
      tmp.push('<a>' + navs[i]+ '</a>');
  }
  $scope.navs = '当前位置：' + tmp.join(' > ');
});

app.controller('downloadCtrl' , function($scope, $modal){
  $scope.showDownload = function(){
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'downloadModal.html',
      controller: 'downloadModalCtrl'
    });
  }
});
app.controller('uploadCtrl' , function($scope, $modal){
  $scope.showUpload = function(){
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'uploadModal.html',
      controller: 'uploadModalCtrl'
    });
  }
});
app.controller('trueUploadCtrl' , function($scope, $modal){
  $scope.showUpload = function(){
    $modal.open({
      animation: true,
      templateUrl: 'trueUploadModal.html',
      controller: 'trueUploadModalCtrl'
    });
  }
});
app.controller("trueUploadModalCtrl", function($scope, $modalInstance, BeDownloading){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.trueUpload = [];
  BeDownloading.getFiles(function(data){
    $scope.trueUpload = data;
  });
});

app.controller('shortcutBoxController', function($scope, chatbox, $window, $location, remoteSocket, AllFriend, toast, safeApply) {
  $scope.openChatbox = function() {
    //Need jQuery-Easydrag
    //https://github.com/zhangxiaoyang/jQuery-Easydrag
    clearInterval($window.chatAnimationInterval);
    chatbox.show(null);
  };

  $scope.goTopClickHandler = function() {
    var path = $location.path().split('/',2)[1];
    if (path == 'friend_res' || path == 'myspace') {
      ['space_content', 'friend_right', 'my_resource'].forEach(function(itemClass) {
        if ($('.' + itemClass).length)
          $('.' + itemClass).animate({ scrollTop: 0 }, 'fast');
      });
    }
    else
      $('.workspace').animate({ scrollTop: 0 }, 'fast');
  };

  $scope.goBottomClickHandler = function() {
    var path = $location.path().split('/',2)[1];
    if (path == 'friend_res' || path == 'myspace') {
      ['space_content', 'friend_right', 'my_resource'].forEach(function(itemClass) {
        if ($('.' + itemClass).length)
          $('.' + itemClass).animate({ scrollTop: $('.' + itemClass)[0].scrollHeight }, 'fast');
      });
    }
    else
      $('.workspace').animate({ scrollTop: $('.workspace')[0].scrollHeight }, 'fast');
  };

  $scope.$watch(function(){return $window.global.hasNewSingleChat;}, function(oldValue, newValue) {
    var hidden = $('#chatbox-container').is(':hidden');
    if(hidden && $window.global.hasNewSingleChat) {
      $window.chatAnimationInterval = setInterval(function() {
        $(".chat .fa-comment").fadeOut(500).fadeIn(500);
      }, 1500);

    }
    safeApply($scope, function() {
      $window.global.hasNewSingleChat = false;
    });
  });
});

app.controller('downloadModalCtrl', function($scope, $modalInstance, downloader, localSocket, $modal){
  $scope.allDownloads = downloader.allDownloads;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.downloadCtrls = function(idx, flag){
    if(flag == 1){
      $scope.allDownloads[idx].isPause = false;
      var tmp = $scope.allDownloads[idx];
      tmp["value"] = "正在重新启动下载";
      localSocket.emit('resumeFileDownload', JSON.stringify({"size":tmp["fileSize"],"type":4, "hash":tmp["fileHash"],"isDir":tmp["isDir"]}));
    }
    else{
      $scope.allDownloads[idx].isPause = true;
      var tmp = $scope.allDownloads[idx];
      tmp["value"] = "已暂停";
      localSocket.emit('pauseFileDownload', JSON.stringify({"size":tmp["fileSize"],"type":3, "hash":tmp["fileHash"],"isDir":tmp["isDir"]}));
    }
  };
  $scope.reDownload = function(idx){
    downloader.reDownload(idx);
  };
  $scope.continueDownload = function(idx){
    downloader.continueDownload(idx);
  };
  $scope.cancelDownload = function(idx){
    downloader.cancelDownload(idx);
  };
  $scope.openDir = function(idx){
    downloader.openDir(idx);
  };
  $scope.viewDownload = function(idx){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'folderDownloadModal.html',
      controller: 'showDirDownload',
      scope: $scope,
      resolve: {
        index: function () {
          return idx;
        }
      }
    });
  };
});

app.controller('folderModalCtrl', function($scope, $modalInstance, toast, downloader, index, canDownload, rid){
  $scope.canDownload = canDownload;
  $scope.treeData = [];
  $scope.shouldHide = false;
  $scope.error = "";
  $scope.selectedFiles = [];
  $scope.totalFiles = 0;
  $scope.tmp = $scope.$parent.curRes[index];
  downloader.viewFolderInfo($scope.tmp["file_name"], $scope.tmp["file_hash"], $scope.tmp["file_size"], $scope.$parent.m_uid, function(err, data, len){
    $scope.shouldHide = true;
    if(err){
      $scope.error = data;
    }
    else{
      $scope.totalFiles = len;
      $scope.treeData = data;
    }
  });
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.render = function(tdList, node){
    tdList.eq(2).text(node.data['file_size']).css("text-align", "center");
    tdList.eq(3).text(node.data['download_num']).css("text-align", "center");
    var online_owners_num =  node.data['online_owners_num'];
    var all_owner_num =  node.data['all_owner_num'];
    if (all_owner_num || online_owners_num)
      tdList.eq(4).text([online_owners_num, all_owner_num].join('/')).css("text-align", "center");
  };
  $scope.select = function(files){
    $scope.selectedFiles = files;
  };
  $scope.download = function(flag){
    $modalInstance.dismiss('cancel');
    if(flag != 0){
      var fileHashs = [], fileSizes=[];
      var len = $scope.selectedFiles.length;
      for(var i = 0; i < len; i++){
        var item = $scope.selectedFiles[i];
        item = item.split("_");
        fileHashs.push(item[0]);
        fileSizes.push(item[1]);
      }
      if(fileHashs.length == 0){

        toast.showWarningToast("oops~请选择至少一个文件");
        return;
      }
      fileHashs = fileHashs.join(",");
      fileSizes = fileSizes.join(",");
      downloader.download($scope.tmp, $scope.$parent.isPrivate, fileHashs, fileSizes, rid);
    }
  };
});

app.controller('showDirDownload', function($scope, $window, $modalInstance, index){
  $scope.shouldHide = false;
  var tmp = $scope.$parent.allDownloads[index];
  var fileInfo = tmp["folderInfo"];
  var children = [];
  for(var i in fileInfo){
    var item = fileInfo[i];
    var one_file = {};
    one_file["key"] = i;
    one_file["title"] = item["fileName"];
    one_file["size"] = item["fileSize"];
    if($window.parseInt(item["complete"]) === 0){
      if("progress" in item)
        one_file["progress"] = item["progress"] +"%";
      else{
        one_file["progress"] = "排队中";
      }
    }
    else
      one_file["progress"] = "已下完";
    children.push(one_file);
  }
  var folder = {
    title: tmp["fileName"],
    folder: true,
    "file_size": children.length,
    expanded: true,
    children: children
  }
  $scope.treeData = [folder];
  $scope.shouldHide = true;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.render = function(tdList, node){
    tdList.eq(2).text(node.data['size']).css("text-align", "center");
    tdList.eq(3).text(node.data['progress']).css("text-align", "center");
  };
});

app.controller('uploadModalCtrl', function($scope, $modalInstance, $modal, $window){
  $scope.uploadProgress = $window.uploadProgress;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.showCancelUpload = function(id){
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'uploadCancelModal.html',
      controller: 'uploadCancelModalCtrl',
      resolve: {
        mid: function(){
          return id;
        }
      }
    });
  }
  $scope.hasUpload = function() {
    return Object.keys($scope.uploadProgress).length;
  };
});

app.controller('uploadCancelModalCtrl', function($scope, $modalInstance, localSocket, $window, mid){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.cancelUpload = function(flag){
    if($window.parseInt(flag) == 1){
        localSocket.emit("cancel-upload"+mid, mid);
        delete $window.uploadProgress[mid];
        if($window.upload_count > 0)
          $window.upload_count--;
        if($window.upload_count == 0)
          $window.showUploadingHint = false;
    }
    $modalInstance.dismiss('cancel');
  }
});

app.controller('noCoinCtrl', function($scope, $modalInstance){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  }
});

app.controller('uploadContentCtrl', function($scope, $modalInstance, $http, $window, star, fileDialog, localSocket, toast, Tag, ResType, extInfo, WinManager, safeApply, $rootScope){
  $scope.guifan = '';
  $scope.guifanIdx = 0;
  $scope.tagList = [];
  $scope.labelTags = [];
  $scope.tagNumMax = 5;
  $scope.shouldShowSub = false;
  $scope.showUploadHint = false;
  $scope.fileSel = '';
  $scope.isDir = false;
  $scope.uploadFileType = '上传文件';
  $scope.showUploadFileType = false;
  $scope.rate = 4.5;
  $scope.upload_html = {
    "请选择类别": "",
    "剧集": '<div><input style="margin-left:15px;margin-right: 18px;" class="col-xs-9" id="resourceName" type="text" value="" placeholder="请填写剧集资源名称，如“吸血鬼日记”"/>'+
            '<input class="col-xs-2" id="resourceNum" type="text" value="" placeholder="集数"/></div>' +
            '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
            '<i class="fa fa-pencil-square-o textMain" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></i></div>',
    "电影": '<div><input style="margin-left: 15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写电影资源名称，如“星际穿越”" /></div>' +
            '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
            '<i class="fa fa-pencil-square-o textMain" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></i></div>',
    "音乐": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写音乐资源名称，如“青花瓷”"/>'+
            '<input class="col-xs-3" style="margin-right: 5px;" id="resourceArt" type="text" value="" placeholder="音乐家"/>'+
            '<input class="col-xs-2" id="resourceAlbum" type="text" value="" placeholder="专辑名"/></div>',
    "动漫": '<div><input style="margin-left:15px;margin-right: 18px;" class="col-xs-9" id="resourceName" type="text" value="" placeholder="请填写动漫资源名称，如“海贼王”"/>'+
            '<input class="col-xs-2" id="resourceNum" type="text" value="" placeholder="集数"/></div>' +
            '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
            '<i class="fa fa-pencil-square-o textMain" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></i></div>',
    "游戏": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写游戏资源名称，如“实况足球”"/>'+
            '<input class="col-xs-3" style="margin-right: 5px;" id="resourceEnName" type="text" value="" placeholder="英文名"/>'+
            '<input class="col-xs-2" id="resourceVersion" type="text" value="" placeholder="版本号"/></div>',
    "综艺": '<div><input style="margin-left:15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写综艺资源名称，如“爸爸去哪儿”"/></div>' +
            '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
            '<i class="fa fa-pencil-square-o textMain" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></i></div>',
    "体育": '<div><input style="margin-left:15px;margin-right: 15px;" class="col-xs-8" id="resourceName" type="text" value="" placeholder="请填写体育资源名称"/>'+
            '<input class="col-xs-3" id="resourceDay" type="text" value="" placeholder="日期"/></div>' +
            '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
            '<i class="fa fa-pencil-square-o textMain" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></i></div>',
    "软件": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写软件资源名称，如“会声会影”"/>'+
            '<input class="col-xs-3" style="margin-right: 5px;" id="resourcePlantform" type="text" value="" placeholder="平台"/>'+
            '<input class="col-xs-2" id="resourceVersion" type="text" value="" placeholder="版本号"/></div>',
    "其它": '<div><input style="margin-left:15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写一个中文名或者纯英文名" /></div>',
    "学习": '<div><input data="0" style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写一个中文名称"/>'+
            '<input data="1" class="col-xs-3" style="margin-right: 5px;" id="resourceCourse" type="text" value="" placeholder="课程名"/>'+
            '<input data="1" class="col-xs-2" id="resourceTeacher" type="text" value="" placeholder="授课老师"/></div>'+
            '<div><input data="1" style="margin-left:15px;margin-right: 18px;" class="col-xs-8" id="resourceSchool" type="text" value="" placeholder="资源所属学校名"/>'+
            '<input data="1" class="col-xs-3" id="resourceAcademy" type="text" value="" placeholder="资源所属院系名"/></div>'
  };
  $scope.init = function(){
    var initScore = 1;
    var totalScore = 5;
    var group = 'uploadStar';
    star.render(initScore, totalScore, group, function(score) {
      $scope.rate = score;
    });
  };
  $scope.init();
  $scope.isUploading = function(){
    return $window.showUploadingHint;
  }
  $scope.toggleFileType = function(){
    $scope.showUploadFileType = !$scope.showUploadFileType;
  }
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  }
  $scope.readGf = function(){
    var url = "http://www.friendsbt.com/guifan.html#guifan-"+$scope.guifanIdx;
    WinManager.open(url);
  }
  $scope.typeChange = function(){
    //var t = $scope.selectedResourceType;
    //显示上传规范
    if($scope.selectedResourceType == '请选择类别') 
      $scope.guifan = '';
    else 
      $scope.guifan = '【' + $scope.selectedResourceType + '】';
    $scope.guifanIdx = Tag.getIdx($scope.selectedResourceType);
    $scope.tagList = Tag.getByType($scope.selectedResourceType);
    $scope.selectedTag = '请选择标签';
    $("#upload_panel").html($scope.upload_html[$scope.selectedResourceType]);
    if($scope.selectedResourceType == "电影" || $scope.selectedResourceType=="剧集" || $scope.selectedResourceType=="综艺" || $scope.selectedResourceType=="动漫")
    {
      $window.shouldUpload = false;
      $("#resourceName").blur(function(event) {
        /* Act on the event */
        var val = $("#resourceName").val();
        if(val.length > 0)
        {
          $http.get("/getdouban?douban="+val);
          $("#err_tips").html("正在为您获取资源详情，请耐心等候...");
        }
        //if(!val || !isChinese(val)){
        //  toast.showNoticeToast("请填写一个中文名称<br/>可以帮助找到漂亮配图哟~");
        //}        
      }).focus(function(event) {
        /* Act on the event */
        $("#err_tips").html("");
        $("#upload_exp_info").remove();
        delete $window.uploadDoubanData;
      });
      $scope.shouldShowSub = true;
    }
    else{
      $scope.shouldShowSub = false;
    }
  };
  $scope.delTag = function(idx){
    $scope.labelTags.splice(idx, 1);
  };
  $scope.tagChange = function(){
    var idx = $scope.labelTags.indexOf($scope.selectedTag);
    if (idx == -1) {
        if ($scope.labelTags.length < $scope.tagNumMax) {
          $scope.labelTags.push($scope.selectedTag);
        } else {
          toast.showNoticeToast("最多可以添加" + $scope.tagNumMax + "个标签");
        }
    } else {
      $scope.labelTags.splice(idx, 1);
    }
    $scope.selectedTag = "请选择标签";
    if($scope.selectedResourceType === "学习"){
      var d = $scope.labelTags.length;
      var exclusiveInStudy = ["TED","百家讲坛","软件教学","其它"];
      for (var i = 0; i < $scope.labelTags.length; i++) {
          d = 1;
          if (exclusiveInStudy.indexOf($scope.labelTags[i]) == -1) {
            d = 0;
            break;
          }
      }
      if(d > 0){
        $("#upload_panel").find("input[data='1']").attr("disabled","disabled");
      }
      else
        $("#upload_panel").find("input[data='1']").removeAttr('disabled'); 
    }
  };
  $scope.fileSelChange = function(fileType){
    $scope.uploadFileType = fileType;
    var sel = 1;
    if(fileType == '上传文件')
      sel = 1;
    else if(fileType == '上传文件夹')
      sel = 3;
    if(sel == 1){
      fileDialog.openFile(function(result){
        var value = result[1];
        if(!value)
          return;
        $("#upload_panel").attr('data', value);
        $scope.isDir = false;
        $scope.fileSel = value;
        safeApply($rootScope, function() {
          $scope.showUploadHint = true;
        });
      }, false);
    }
    else if(sel == 3){
      fileDialog.openDir(function(result){
        var value = result[1];
        if(!value)
          return;
        $("#upload_panel").attr('data', value);
        $scope.isDir = true;
        $scope.fileSel = value;
        safeApply($rootScope, function() {
          $scope.showUploadHint = true;
        });
      });
    }
    $scope.toggleFileType();
  };
  $scope.validateUpload = function(upload_type){
    var exp_info = {};
    var ret = [];
    switch(upload_type) {
      case 0:case 6:
        var enName = $("#resourceEnName").val();
        if (enName && enName.length > 0) {
          ret.push(true);
          exp_info["resource_en_name"] = enName;
          ret.push(exp_info);
        }
        else{
          $('#err_tips').html("请填写0day英文名，点击右侧按钮可自动提取");
        }
        break;
      case 1:case 4:
        var num = $("#resourceNum").val();
        var reg = new RegExp("^[0-9]+$");
        if(!reg.test(num)){
          $('#err_tips').html("集数只能为纯数字");
          ret.push(false);
          return ret;
        }
        ret.push(true);
        exp_info["resource_num"] = num;
        var enName = $("#resourceEnName").val();
        if (enName && enName.length > 0) {
          exp_info["resource_en_name"] = enName;
        }
        ret.push(exp_info);
        break;
      case 3:
        var art = $("#resourceArt").val();
        var album = $("#resourceAlbum").val();
        if(!art || !album){
          $('#err_tips').html("音乐家或专辑名未填");
          ret.push(false);
          return ret;
        }
        ret.push(true);
        exp_info["resource_art"] = art;
        exp_info["resource_album"] = album;
        ret.push(exp_info);
        break;
      case 2:
        //var d = window.parseInt($("#resourceLabel option:selected").attr("data"));
          var d = $scope.labelTags.length;
          var exclusiveInStudy = ["TED","百家讲坛","软件教学","其它"];
          for (var i = 0; i < $scope.labelTags.length; i++) {
              d = 1;
              if (exclusiveInStudy.indexOf($scope.labelTags[i]) == -1) {
                  d = 0;
                  break;
              }
          }
          if(d == 0){
          var course = $("#resourceCourse").val();
          var teacher = $("#resourceTeacher").val();
          var school = $("#resourceSchool").val();
          var academy = $("#resourceAcademy").val();
          if(!course || !teacher || !school || !academy){
            $('#err_tips').html("课程名或任课老师或所属学校学院未填");
            ret.push(false);
            return ret;
          }
          exp_info["resource_course"] = course;
          exp_info["resource_teacher"] = teacher;
          exp_info["resource_school"] = school;
          exp_info["resource_academy"] = academy;
        }
        ret.push(true);
        ret.push(exp_info);
        break;
      case 5:
        var enName = $("#resourceEnName").val();
        var version = $("#resourceVersion").val();
        if(!version){
          $('#err_tips').html("请填写版本号");
          ret.push(false);
          return ret;
        }
        ret.push(true);
        exp_info["resource_en_name"] = enName;
        exp_info["resource_version"] = version;
        ret.push(exp_info);
        break;
      case 7:
        var date = $("#resourceDay").val();
        if(!date){
          $('#err_tips').html("请填写资源日期");
          ret.push(false);
          return ret;
        }
        ret.push(true);
        exp_info["resource_date"] = date;
        var enName = $("#resourceEnName").val();
        if (enName && enName.length > 0) {
          exp_info["resource_en_name"] = enName;
        }
        ret.push(exp_info);
        break;
      case 8:
        var platform = $("#resourcePlantform").val();
        var version = $("#resourceVersion").val();
        if(!version || !platform){
          $('#err_tips').html("版本号或平台未填");
          ret.push(false);
          return ret;
        }
        ret.push(true);
        exp_info["resource_platform"] = platform;
        exp_info["resource_version"] = version;
        ret.push(exp_info);
        break;
      default:
        ret.push(true);
        ret.push(exp_info);
        break;    
    }
    return ret;
  };
  $scope.fileUpload = function(){
    var t = $scope.selectedResourceType;
    if(!$window.shouldUpload && (t == "电影" || t=="剧集" || t=="综艺" || t=="动漫"))
    {
      toast.showNoticeToast("正在为您获取资源信息，请耐心等候");
      return;
    }
    $('#err_tips').html("");
    var filePath = $scope.fileSel;
    //console.log($('#resourceFile').val());
    //console.log($('#resourceDir').val());
    if (!filePath) {
      $('#err_tips').html("请选择分享的文件");
      return;
    }
    var mainType = ResType.getTabIdx($scope.selectedResourceType);
    if(mainType == -1)
    {
      $('#err_tips').html("请选择类别");
      return;
    }
    var subType = ResType.getSubIdx($scope.selectedSubType);
    if(!subType)
    {
      $('#err_tips').html("请选择类型");
      return;
    }
    var fileName = $('#resourceName').val();
    if (extInfo)
      fileName = extInfo.resName;
    if (!fileName) { 
      $('#err_tips').html("请填写资源名");
      return;
    }
    //var label = $('#resourceLabel').val();
    if ($scope.labelTags.length == 0) {
        $('#err_tips').html("请至少选择一个标签");
        return;
    }
    var label = $scope.labelTags.join(',');
    var isPublic = 1;
    if ($scope.onlyFriendSee) {
      isPublic = 0;
    }
    var comment = $scope.resourceComment;
    if (!comment) {
      comment = "珍藏的好资源分享给大家，希望大家喜欢。";
    }
    if(comment.length > 200){
      toast.showNoticeToast("评论过长，请保持在200以内");
      return;
    }
    comment = htmlencode(comment);
    //var grade = $("input:radio[name ='radio_grade']:checked").val();
    var ret = $scope.validateUpload(mainType);
    if(!ret[0]){
      return;
    }
    $('#err_tips').html("");
    if(!$scope.isDir && (t=="剧集" || t=="动漫"))
      fileName = fileName+"_"+$("#resourceNum").val();
    fileName = htmlencode(fileName);
    var param = {};
    param["op"] = 0;
    param["path"] = filePath;
    param["name"] = fileName;
    param["mainType"] = mainType;
    param["subType"] = subType;
    param["label"] = label;
    param["desc"] = comment;
    param["grade"] = $scope.rate;
    param["isPublic"] = isPublic;
    param["nick_name"] = $window.nick_name;
    param["rid"] = $scope.rid;
    param["ext_info"] = {};
    if($window.uploadDoubanData){
      param["ext_info"] = $window.uploadDoubanData;
    }
    for(var key in ret[1]){
      param["ext_info"][key] = ret[1][key];
    } 
    param["ext_info"] = JSON.stringify(param["ext_info"]);
    if($scope.isDir){
      param["isDir"] = 1;
    }
    else{
      param["isDir"] = 0;
    }
    $scope.fileSel = '';
    $http.post("/res", param).success(function(){
      delete $window.uploadDoubanData;
    }).error(function(){
      delete $window.uploadDoubanData;
      console.log("upload error");
      toast.showErrorToast("上传失败，请检查文件是否存在或者重试");
      $window.upload_count--;
      if($window.upload_count == 0)
        $window.showUploadingHint = false;
    });
    //hide the file upload dialog
    $window.upload_count++;
    $window.showUploadingHint = true;
    toast.showNoticeToast("正在上传，请稍后");
    $modalInstance.dismiss('cancel'); 
  };
  $scope.fillData = function(){
    if(extInfo){
      $scope.shouldShowPublic = false;
      $scope.onlyFriendSee = false;
      $scope.selectedResourceType = ResType.getTabByIndex(extInfo.resType);
      $scope.rid = extInfo.rid;
      $scope.typeChange();
      $("#resourceName").val(extInfo.resName);
      if($scope.selectedResourceType == "电影" || $scope.selectedResourceType=="剧集" || $scope.selectedResourceType=="综艺" || $scope.selectedResourceType=="动漫")
      {
        $window.shouldUpload = false;
        $http.get("/getdouban?douban="+extInfo.resName);
        $("#err_tips").html("正在为您获取资源详情，请耐心等候...");
      }
      $("#upload_res_type").attr("disabled","disabled");
      $("#resourceName").attr("disabled","disabled");
    }
    else{
      $scope.shouldShowPublic = true;
      $("#upload_res_type").removeAttr("disabled");
      $("#resourceName").removeAttr("disabled");
      $scope.selectedResourceType = '请选择类别';
      $scope.rid = '';
    }
  }
});

app.controller('updateCtrl', function($scope, $modalInstance, localSocket){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.update = function(flag){
    $modalInstance.dismiss('cancel');
    if(flag == 1)
      localSocket.emit('update');
  }
});

app.controller('helpCtrl', function($scope, $modalInstance, WinManager){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.toWeb = function(){
    $modalInstance.dismiss('cancel');
    WinManager.open("http://www.friendsbt.com/");
  }
});

app.controller('closeController', function($scope, $modalInstance, localSocket){
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.closeSoftware = function(flag){
    $modalInstance.dismiss('cancel');
    if(flag == 1)
      localSocket.emit('winclose');
  };
});
