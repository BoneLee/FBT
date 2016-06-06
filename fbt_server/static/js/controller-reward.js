app.service('RewardService', ['$http', 'toaster', 'User', 'uploadSrv','$location',
  function($http, toaster, User, uploadSrv,$location) {
    var self = this;
    this.rewardList = [];


    this.isRewardListEmpty = false;
    this.isPaginationVisible = false;

    this.page = {
      // max_size:,
      total_items: 0,
      max_size: 5,
      items_per_page: 15,
      current_page: 1,
      pageChanged: null,
    };

    this.setPagination = function(responseData) {

        self.page.total_items = responseData.total_page * 15;
      if(responseData.total_page >1){
        this.isPaginationVisible = true;
      }else{
          this.isPaginationVisible = false;
      }

    };



    this.fetchRewardsList = function(sortMethod, isOnlyShowMySchool, page) {
      if (page === undefined || page === null) {
        page = 1;
      }
      var kwargs = {
        page: page,
        sort_by: sortMethod,
        my_university_checked: isOnlyShowMySchool
      };
      var req = {
        url: '/reward/list',
        method: 'GET',
        params: kwargs
      };
      var promise = $http(req).success(function(data, status, headers, config) {
          var responseData = angular.fromJson(data);
          switch(responseData.err){
              case 0:

            self.rewardList = responseData.reward_list;
            if(responseData.reward_list.length ===0){
                self.isRewardListEmpty = true;
            //toaster.pop('warning','暂无悬赏','目前还没有悬赏，赶紧去悬赏一个想要的资源吧',false);
            }else{
                self.isRewardListEmpty = false;
            }
            self.page.current_page = responseData.current_page;
            self.setPagination(responseData);
            break;
              case 1:
            toaster.pop('error','参数错误！','',false);
            break;
              case 2:
            toaster.pop('error','请求分页错误','请检查page参数',false);
            break;
              case 3:
            toaster.pop('error','院系错误','您的院系出错了，请到个人中心设置正确的院系！',false);
            break;
              case 4:
            toaster.pop('error','未经授权！','请检查是否登录',false);
            break;
              default:
            toaster.pop('error','未知错误！','',false);

          }
        })
        .error(function(data, status, headers, config) {

        });
      return promise;
    };

    this.thumbDown = function(){

        toaster.pop('success','资源拍砖成功！','',true);
    };
    this.thumbUp = function(){
        toaster.pop('success','资源点赞成功！','',true);
    };
    //TODO
    this.thumbUpResource = function(resourceId) {
      var isLogin = User.logined();
      if (isLogin) {
        var kwargs = {

        };
        var req = {
          url: '/reward/resource/thumb_up',
          method: 'GET',
          resource_index: resourceId,
          reward_id: rewardId,
          headers: {
            "X-CSRFToken": getCookie("_xsrf")
          }
        };

        $http(req).success(function(data, status, headers, config) {
            var responseData = angular.fromJson(data);
            if (responseData.err === 0) {
              this.rewardList = responseData.data;
            } else if (responseData.err === 1) {

            } else if (responseData.err === 2) {

            }
          })
          .error(function(data, status, headers, config) {});
      } else {

        toaster.pop('error', '请登录后再操作', '', false);
      }

    };

    //TODO
    this.thumbDownResource = function(resourceId) {
      var isLogin = User.logined();
      if (isLogin) {
        var req = {
          method: 'GET',
          resource_index: resourceId,
          reward_id: rewardId,
          headers: {
            "X-CSRFToken": getCookie("_xsrf")
          }
        };
        $http(req).success(function(data, status, headers, config) {
            var responseData = angular.fromJson(data);
            if (responseData.err === 0) {
              this.rewardList = responseData.data;
            } else if (responseData.err === 1) {

            } else if (responseData.err === 2) {

            }
          })
          .error(function(data, status, headers, config) {});
      } else {

        toaster.pop('error', '请登录后再操作', '', false);
      }

    };

    this.appendFB = function(rewardId, addFB) {

      var isLogin = User.logined();
      if (isLogin) {
        var kwargs = {
          how_much: addFB,
          reward_id: rewardId
        };
        var req = {
          url: '/reward/append_fb',
          method: 'GET',
          params: kwargs,
          headers: {
            "X-CSRFToken": getCookie("_xsrf")
          }
        };

        $http(req).success(function(data, status, headers, config) {
            var responseData = angular.fromJson(data);
            switch (responseData.err) {
              case 0:
                toaster.pop('success', '追加成功', '', true);
                break;
              case 1:
                toaster.pop('error', '追加失败', '没有权限！', false);
                break;
              case 2:
                toaster.pop('error', '追加失败', '参数错误！', false);
                break;
              case 3:
                toaster.pop('error', '追加失败', '您的F币不足！', false);
                break;
              default:
                toaster.pop('error', '追加失败', '未知错误', false);
            }

          })
          .error(function(data, status, headers, config) {
            toaster.pop('error', '追加失败', '与服务器通信错误', false);
          });
      } else {
        toaster.pop('error', '请登录后再操作', '', false);
      }

    };



    this.uploadResource2Reward = function(reward) {

      if(User.logined()){
        uploadSrv.refreshUploader();
        uploadSrv.isRewardMode = true;
        uploadSrv.isPostRewardMode = false;
        uploadSrv.rewardId = reward.id;
        angular.element('#uploadModal').modal('show');

      }
      else{
        $location.path('home').search({
          //return_url:$location.path(),
          return_url: 'reward'
        });
      }



      //User.login(function() {
      //  uploadSrv.isRewardMode = true;
      //  uploadSrv.isPostRewardMode = false;
      //  uploadSrv.rewardId = reward.id;
      //  angular.element('#uploadModal').modal('show');
      //
      //});

    };
    this.changeCollapseIcon = function(index){
        
        var ele = angular.element('#icon' + index);
        if(ele.hasClass('glyphicon-collapse-down')){
            ele.removeClass('glyphicon-collapse-down').addClass('glyphicon-collapse-up');
        }else if(ele.hasClass('glyphicon-collapse-up')){
            ele.removeClass('glyphicon-collapse-up').addClass('glyphicon-collapse-down');

        }
    };

  }
]);



app.controller('RewardController', ['$scope', '$location', 'RewardService', 'downloadSrv', 'User', 'uploadSrv','PreviewService',
  function($scope, $location, RewardService, downloadSrv, User, uploadSrv,PreviewService) {
    $scope.isPaginationVisible = RewardService.isPaginationVisible;

    $scope.appendFBFormData = {
      addFB: ''
    };

    $scope.ch = {
      sortMethod: 0,
      isOnlyShowMySchool: 0
    };

    $scope.sortMethodEnum = {
      SORT_BY_TIME: 0,
      SORT_BY_FB: 1
    };
    $scope.page = RewardService.page;

    $scope.showRewardModal = function() {
      User.login(function() {
        uploadSrv.isPostRewardMode = true;
        uploadSrv.isRewardMode = false;
            if(uploadSrv.uploader.state == plupload.STOPPED){
                uploadSrv.refreshUploader();
            }
        angular.element('#uploadModal').modal('show');

      });
    };
    $scope.direct2MyReward = function() {


      User.login(function() {
        $location.path('reward/myreward/sponsed');

      });
    };


    $scope.init = function() {

        var is_login = User.logined();
        if(!is_login){
            $scope.canOnlyShowMySchoolBeChecked= true;
        }else{
            $scope.canOnlyShowMySchoolBeChecked= false;
        }

      $scope.isPaginationVisible = false;
      $scope.sortMethod = $scope.sortMethodEnum.SORT_BY_TIME;
      $scope.isOnlyShowMySchool = 0;
      $scope.fetchRewardsList();
      $scope.rewardList = RewardService.rewardList;
    };


    $scope.postReward = function() {
      RewardService.postReward($scope.postRewardFormData);
    };


    $scope.fetchRewardsList = function() {
      RewardService.fetchRewardsList($scope.sortMethod, $scope.isOnlyShowMySchool, $scope.page.current_page).then(function() {
        $scope.rewardList = RewardService.rewardList;
      });
    };


    $scope.changeCollapseIcon = function(index){
        RewardService.changeCollapseIcon(index);
    };

    $scope.$watch(function(){
        return RewardService.isPaginationVisible;
        },function(newValue,oldValue){
            $scope.isPaginationVisible = newValue;
        });
    $scope.$watch(function(){
        return RewardService.isRewardListEmpty;
        },function(newValue,oldValue){
            $scope.isRewardListEmpty= newValue;
        });

    $scope.$watch(function() {
      return $scope.page.current_page;
    }, function(newValue, oldValue) {
      if (newValue != oldValue) {
        $scope.fetchRewardsList();
      }

    });

    $scope.showPreviewModal = PreviewService.showPreviewModal;

    $scope.download = function(file) {
      downloadSrv.download(file.file_id, file.download_link);
    };

    $scope.showUploadModal = function(rewardId) {

      RewardService.uploadResource2Reward(rewardId);

    };

    $scope.checkSortMethod = function(value) {
      $scope.sortMethod = value;
      $scope.fetchRewardsList(value);
    };
    $scope.checkOnlyMySchool = function() {
      $scope.isOnlyShowMySchool = $scope.ch.isOnlyShowMySchool;
      $scope.fetchRewardsList($scope.ch.isOnlyShowMySchool);
    };

    $scope.showAppendFBModal = function(reward) {
      $scope.currentRewardId = reward.id;
      User.login(function() {
        angular.element('#appendFBModal').modal('show');
      });
    };
    $scope.appendFB = function() {
      RewardService.appendFB($scope.currentRewardId, $scope.appendFBFormData.addFB);
    };
    //$scope.thumbDown = function(){
    //    RewardService.thumbDown();
    //};
    //$scope.thumbUp = function(){
    //    RewardService.thumbUp();
    //};

  }
]);



app.service('MyRewardService', ['$http', 'User', 'toaster',
  function($http, User, toaster) {

    var self = this;
    this.isPaginationVisible = false;
    this.isRewardListEmpty = false;
    this.myRewardTypeEnum = {
      SPONSED: 'sponsed',
      RELATED: 'related',
    };
    this.myRewardList = [];
    this.page = {
      // max_size:,
      total_items: 0,
      max_size: 5,
      items_per_page: 15,
      current_page: 1,
      pageChanged: null,
    };

    this.setPagination = function(responseData) {

        self.page.total_items = responseData.total_page * 15;
      if(responseData.total_page >1){
        this.isPaginationVisible = true;
      }else{
          this.isPaginationVisible = false;
      }
    };
    this.fetchMyRewardList = function(myRewardType,page) {

      if (page === undefined || page === null) {
        page = 1;
      }
      var kwargs = {
        page: page,
      };

      var req = {
        method: 'GET',
        params:kwargs,
        headers: {
          "X-CSRFToken": getCookie("_xsrf")
        }
      };
      if (myRewardType === this.myRewardTypeEnum.SPONSED) {
        req.url = 'reward/user/all';
      } else if (myRewardType === this.myRewardTypeEnum.RELATED) {
        req.url = 'reward/user/related';
      }
      else {
        toaster.pop('error', '请求类型错误！', '', false);
        return;
      }
      var promise = $http(req).success(function(data, status, headers, config) {
          var responseData = angular.fromJson(data);
          if (responseData.err === 0) {
              if(responseData.reward_list.length === 0){
                  self.isRewardListEmpty = true;
              }else{
                  self.isRewardListEmpty = false;
              }
            self.myRewardList = responseData.reward_list;
            self.page.current_page = responseData.current_page;
            self.setPagination(responseData);
          } else if (responseData.err === 1) {
            toaster.pop('error', '参数错误!', '', false);
          } else if (responseData.err === 2) {
            toaster.pop('error', '采用失败！', '未经授权，请检查是否登录!', false);

          }

        })
        .error(function(data, status, headers, config) {

          toaster.pop('error', '数据加载失败', '', false);

        });
      return promise;

    };
    this.adoptResource = function(rewardId, user, ratingNum) {
      var isLogin = User.logined();
      if (isLogin) {
        var kwargs = {
          score: ratingNum,
          reward_id: rewardId,
          user: user
        };
        var req = {

          url: '/reward/resource/confirm',
          method: 'GET',
          params: kwargs,
          headers: {
            "X-CSRFToken": getCookie("_xsrf")
          }

        };
        $http(req).success(function(data, status, headers, config) {
            var responseData = angular.fromJson(data);
            if (responseData.err === 0) {
              toaster.pop('success', '采用成功！', '设置最佳答案成功，相应用户会获得F币!', true);
            } else if (responseData.err === 1) {

              toaster.pop('error', '采用失败！', '未经授权，请检查是否登录!', false);

            } else if (responseData.err === 2) {

              toaster.pop('error', '采用失败！', '参数错误！', false);
            }
          })
          .error(function(data, status, headers, config) {

            toaster.pop('error', '与服务器通信失败！', '与服务器通信失败，请稍后重试!', false);

          });
      } else {

        toaster.pop('error', '请登录后再操作', '', false);


      }

    };




  }
]);
app.controller('MyRewardController', ['$scope', '$routeParams', '$location', 'RewardService','MyRewardService', 'User', 'downloadSrv','PreviewService',
  function($scope, $routeParams, $location, RewardService,MyRewardService, User, downloadSrv,PreviewService) {
    $scope.myRewardTypeEnum = MyRewardService.myRewardTypeEnum;
    $scope.myRewardStatusEnum = {
      PENDING: 'pending',
      SOLVED: 'over',
      EXPIRED: 'expired'
    };
    $scope.confirmFormData = {
        rate:4.5
    };
      angular.element("#adopt-rating").rating({
        "stars": "5",
        "min": "0",
        "max": "5",
        "step": 0.5,
        "size": "xs",
        "showClear": false,
        "glyphicon": false,
        "starCaptions": {
          0.5: "0.5",
            1: "1",
            1.5: "1.5",
            2: "2",
            2.5: "2.5",
            3: "3",
            3.5: "3.5",
            4: "4",
            4.5: "4.5",
            5: "5"
        }
      }).rating('update', 4.5).on('rating.change', function(event, value, caption) {
        $scope.confirmFormData.rate = parseFloat(value);
      }); //暂时用jquery实现评分的初始化

    $scope.navBtnClick = function(myRewardType) {
      $location.path('/reward/myreward/' + myRewardType);
    };
    $scope.init = function() {
        $scope.isPaginationVisible = false;
        $scope.isRewardListEmpty = MyRewardService.isRewardListEmpty;
      $scope.myRewardType = $routeParams.myRewardType;
    $scope.page = MyRewardService.page;
      if ($scope.myRewardType === undefined || $scope.myRewardType.trim() === '') {
        $scope.myRewardType = MyRewardService.myRewardTypeEnum.SPONSED;
      }
      $scope.fetchMyRewardList();
    };
    $scope.fetchMyRewardList = function() {
      MyRewardService.fetchMyRewardList($scope.myRewardType,$scope.page.current_page).then(function() {
        $scope.myRewardList = MyRewardService.myRewardList;
      });

    };
    $scope.showAdoptConfirmDialog = function(reward, user) {
      $scope.currentRewardId = reward.id;
      $scope.currentRewarder = user;
      User.login(function() {
        angular.element('#adoptConfirmDialog').modal('show');
      });
    };
    $scope.adoptResource = function() {
      MyRewardService.adoptResource($scope.currentRewardId, $scope.currentRewarder,$scope.confirmFormData.rate );
    };

    $scope.$watch(function(){
        return MyRewardService.isPaginationVisible;
        },function(newValue,oldValue){
            $scope.isPaginationVisible = newValue;
        });

    $scope.$watch(function() {
      return $scope.page.current_page;
    }, function(newValue, oldValue) {
      if (newValue != oldValue) {
        $scope.fetchMyRewardList();
      }

    });

    $scope.$watch(function(){
        return MyRewardService.isRewardListEmpty;
        },function(newValue,oldValue){
            $scope.isRewardListEmpty= newValue;
        });

    $scope.showPreviewModal = PreviewService.showPreviewModal;

    $scope.download = function(file) {
      downloadSrv.download(file.file_id, file.download_link);
    };
    //$scope.thumbDown = function(){
    //    RewardService.thumbDown();
    //};
    //$scope.thumbUp = function(){
    //    RewardService.thumbUp();
    //};
    $scope.changeCollapseIcon = function(index){
        RewardService.changeCollapseIcon(index);
    };

  }
]);
