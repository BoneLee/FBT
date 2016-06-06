/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('RewardMyController', function($scope, $route, Reward, Subheader, pagination, loading, $window, $modal, downloader, ResType, toast) {
  $scope.formatDate = function(timestamp) {
    var d = new Date(timestamp);
    return sprintf('%02d/%02d %02d:%02d', d.getMonth()+1, d.getDate(), d.getHours(), d.getMinutes());
  };
  $scope.isPrivate = 1;

  var res_type = Subheader.getIndex();
  var page = 1;
  var total_page = 1;
  
  loading.show();
  Reward.my_reward(function(data) {
    loading.hide();
    $scope.rewards = data && data.result
      ? data.result.rewards
      : [];
    total_page = data.result.total_page;

    var _rewards = data.result.rewards;
    for (var i = 0; i < _rewards.length; i++) {
      if ('file_infos' in _rewards[i]) {
        preHandleRes(_rewards[i]['file_infos'], true);
      }
    }

    if(!total_page) {
      pagination.hide('reward-my');
      return;
    }

    pagination.render(1, total_page, 'reward-my', function(currentPageNum, totalPageNum) {
      loading.show();
      Reward.my_reward(function(data) {
        loading.hide();
        $scope.rewards = data && data.result && data.result.rewards
          ? data.result.rewards
          : [];

        var _rewards = data.result.rewards;
        for (var i = 0; i < _rewards.length; i++) {
          if ('file_infos' in _rewards[i]) {
            preHandleRes(_rewards[i]['file_infos'], true);
          }
        }

      }, res_type, currentPageNum);
    });
  }, res_type, page);

  $scope.viewResourceClickHandler = function(file_infos, rid) {
    $('#view-resource-modal').modal({backdrop: false, keyboard: false});
    $scope.file_infos = file_infos;
    $scope.rid = rid;
  };

  $scope.cancelReward = function(rid, res_type, idx){
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'cancelRewardModal.html',
      controller: 'cancelRewardModalCtrl',
      resolve: {
        rewardInfo: function () {
          var tmp = {
            "rid": rid,
            "res_type": res_type,
            "idx": idx,
            "rewards": $scope.rewards
          }
          return tmp;
        }
      }
    });
  };

  $scope.viewRewardClickHandler = function() {
    $('#view-reward-modal').modal({backdrop: false, keyboard: false});
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

  $scope.downloadResourceClickHandler = function(resource, rid) {
    var tmp_resource_list = [resource];
    preHandleRes(tmp_resource_list);

    if (tmp_resource_list[0].isDir) {
      $scope.curRes = tmp_resource_list;
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'folderModal.html',
        controller: 'folderModalCtrl',
        scope: $scope,
        resolve: {
          index: function () {
            return 0;
          },  
          canDownload: function(){
            return true;
          },
          rid: function(){
            return rid;
          }   
        }   
      });   
    }
    else {
      $modal.open({
        backdrop: false,
        keyboard: false,
        animation: true,
        templateUrl: 'downloadModal.html',
        controller: 'downloadModalCtrl'
      });
      downloader.download(resource, 1, rid);
    }
  };

  $scope.getResTypeByIndex = function(index) {
    return ResType.getTabByIndex(index);
  };
});
app.controller("cancelRewardModalCtrl", function($scope, $modalInstance, Reward, rewardInfo){
  $scope.reward = rewardInfo.rewards;
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.cancel = function(flag){
    $modalInstance.dismiss('cancel');
    if(flag == 1){
      Reward.cancel_reward(function(data){
        if(data["type"] == 1){
          $scope.reward.splice(rewardInfo.idx, 1);
        }
        else{
          toast.showErrorToast("删除失败，请检查网络状况");
        }
      }, rewardInfo.rid, rewardInfo.res_type);
    }
  }
});
