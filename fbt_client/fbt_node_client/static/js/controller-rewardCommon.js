/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('RewardCommonController', function($modal, $rootScope, $scope, $route, $location, Reward, Subheader, Tag, pagination, loading, $window, toast, ResType) {
  $rootScope.$broadcast('refreshSubheaderEvent', $location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
  $scope.fbCoin = $window.global.fbCoin;
  $scope.fbtUID = $window.fbtUID;

  var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
  var page = $scope.currentPage ? $scope.currentPage : 1;
  var sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : null;
  var total_page = 1;
 
  loading.show();
  Reward.all_reward(function(data) {
    loading.hide();
    $scope.rewards = data && data.result && data.result.rewards
      ? data.result.rewards
      : [];
    total_page = data.result.total_page;

    if(!total_page) {
      pagination.hide('reward');
      return;
    }

    pagination.render(1, total_page, 'reward', function(currentPageNum, totalPageNum) {
      loading.show();
      Reward.all_reward(function(data) {
        loading.hide();
        $scope.rewards = data && data.result && data.result.rewards
          ? data.result.rewards
          : [];
      },
      res_type,
      $scope.rewards ? $scope.rewards.slice(-1)[0].ctime : 1,
      currentPageNum,
      sort_by);
    });
  },
  res_type, 
  $scope.rewards ? $scope.rewards.slice(-1)[0].ctime : 1,
  page, 
  sort_by);


  //Publish Reward
  $scope.publishRewardClickHandler = function() {
    $('#publish-reward-modal').modal({backdrop: false, keyboard: false});
  };

  $scope.publishRewardSubmitHandler = function() {
    var uid = $scope.fbtUID;
    var res_type = ResType.getTabIdx($scope.res_type);
    var desc = $scope.desc.trim();
    var fileName = $scope.fileName.trim();
    var fb = $scope.fb.trim();
    var res_year = $scope.res_year.trim();
    var res_country = $scope.res_country.trim();

    if (desc == '')
      desc = '你懂得';
    if (!(fileName && fb && res_year && res_country)) {
      toast.showErrorToast('填写内容不全哦, 发布悬赏失败');
      return;
    }
    if (!parseInt(fb) || parseInt(fb) > $scope.fbCoin || parseInt(fb) <= 0) {
      toast.showErrorToast('F币填写错误, 发布悬赏失败');
      return;
    }
    if (!parseInt(res_year) || res_year.length != 4) {
      toast.showErrorToast('年份填写错误, 发布悬赏失败');
      return;
    }

    Reward.offer_reward(function(data) {
      if (data.type == 0)
        toast.showErrorToast('填写内容不合法哦, 发布悬赏失败');
      else
        $route.reload();
    }, uid, res_type, desc, fileName, fb, res_year, res_country);

    $scope.resetPublish();
  };

  //Append Reward
  $scope.appendRewardClickHandler = function(rid) {
      $scope.rid = rid;
      $('#append-reward-modal').modal({backdrop: false, keyboard: false});
  };

  $scope.appendRewardSubmitHandler = function() {
    var rid = $scope.rid;
    var appendFb = $scope.appendFb.trim();

    if (!parseInt(appendFb) || parseInt(appendFb) > $scope.fbCoin || parseInt(appendFb) <= 0) {
      toast.showErrorToast('F币填写错误, 追加悬赏失败');
      return;
    }

    Reward.append_reward(function(data) {
      $route.reload();
    }, rid, appendFb);

    $scope.resetAppend();
  };

  $scope.uploadResourceClickHandler = function(fileName, resType, rid) {
    var info = {"resType": resType, "resName": fileName, "rid": rid};
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'uploadContentModal.html',
      controller: 'uploadContentCtrl',
      resolve: {
        extInfo: function () {
          return info;
        }
      }
    });
  };

  $scope.viewAppendRewardClickHandler = function(append_uid, append_user, append_fb) {
      var append_list = [];
      var row_list = [];
      for(var i = 0; i < append_uid.length; i++) {
        if(row_list.length >= 4) {
          append_list.push(row_list);
          row_list = [];
        }
        row_list.push({
          append_uid: append_uid[i],
          append_user: append_user[i],
          append_fb: append_fb[i]
        });
      }
      if(row_list.length)
          append_list.push(row_list);

      $scope.append_list = append_list;
      $('#view-append-reward-modal').modal({backdrop: false, keyboard: false});
  };

  $scope.selectUploadTypeChangeHandler = function(type) {
    $scope.typeTags = Tag.getByType(type);
    $scope.selectedUploadTags = [];
    $scope.selectedUploadTag = '请选择标签';
  };

  $scope.selectUploadTagChangeHandler = function(tag) {
    if(!$scope.selectedUploadTags) {
      $scope.selectedUploadTags = [tag];
    }
    else if(tag != '请选择标签' && $scope.selectedUploadTags.indexOf(tag) == -1) {
      if($scope.selectedUploadTags.length < 5)
        $scope.selectedUploadTags.push(tag);
      else
        console.log("selectedUploadTags.length should not be larger than 5")
    }
  };

  $scope.removeUploadTagClickHandler = function(tag) {
    $scope.selectedUploadTags.splice($scope.selectedUploadTags.indexOf(tag), 1);
    console.log($scope.selectedUploadTags);
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
    var page = 1;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : null;
    
    loading.show();
    Reward.all_reward(function(data) {
      loading.hide();
      $scope.rewards = data && data.result && data.result.rewards
        ? data.result.rewards
        : [];
      total_page = data.result.total_page;

      if(!total_page) {
        pagination.hide('reward');
        return;
      }

      pagination.render(1, total_page, 'reward', function(currentPageNum, totalPageNum) {
        loading.show();
        Reward.all_reward(function(data) {
          loading.hide();
          $scope.rewards = data && data.result && data.result.rewards
            ? data.result.rewards
            : [];
        },
        res_type,
        $scope.rewards ? $scope.rewards.slice(-1)[0].ctime : 1,
        currentPageNum,
        sort_by);
      });
    },
    res_type, 
    $scope.rewards ? $scope.rewards.slice(-1)[0].ctime : 1,
    page,
    sort_by);
  };

  $scope.getResTypeByIndex = function(index) {
    return ResType.getTabByIndex(index);
  };

  $scope.resetPublish = function() {
    $scope.res_type = '';
    $scope.desc = '';
    $scope.fileName = '';
    $scope.fb = '';
    $scope.res_year = '';
    $scope.res_country = '';
  };

  $scope.resetAppend = function() {
    $scope.appendFb = '';
  };
});
