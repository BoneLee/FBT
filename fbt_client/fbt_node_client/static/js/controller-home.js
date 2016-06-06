/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('HomeController', function($scope, Feed, loading, $route, $window, $location, $timeout, OneRes, toast, downloader, $modal, $rootScope) {
  $rootScope.$broadcast('refreshSubheaderEvent', '/home');

  //page is the ctime of resource
  $window.currentTime = 1;
  $window.currentPageNum = 1;
  var time = $window.currentTime;
  var page = $window.currentPageNum;

  loading.show();
  Feed.getFeed(time, page, function(err, data) {
    loading.hide();

    if(err)
      return;

    $scope.resource_list = data;
  });

  $scope.viewMoreFeed = function() {
    $window.currentTime = $window.currentTime ? $scope.resource_list.slice(-1)[0].ctime : 1;
    $window.currentPageNum = $window.currentPageNum ? $window.currentPageNum : 1;

    var time = $window.currentTime;
    var page = $window.currentPageNum + 1;
    Feed.getFeed(time, page, function(err, data) {
      loading.hide();

      if(err)
        return;

      if(!data.length) {
        toast.showNoticeToast('没有更多动态啦');
        return;
      }

      if($scope.resource_list)
        $scope.resource_list = $scope.resource_list.concat(data);
      else
        $scope.resource_list = data;
    });
  };

  $scope.viewResourceDetailClickHandler = function(resource) {
    OneRes.getRes(resource.rid, function(err, data) {
      if(!err) {
        $location.path('/home/details/').search({'resource':data, 'isPrivate':1});
      }
    });
  };

  /*
  $scope.downloadResourceClickHandler = function(resource) {
    loading.show(); OneRes.getRes(resource.rid, function(err, data) {
      loading.hide();

      $modal.open({
        backdrop: false,
        keyboard: false,
        animation: true,
        templateUrl: 'downloadModal.html',
        controller: 'downloadModalCtrl'
      });

      if(!err) {
        downloader.download(data, 1);
      }
    });
  };
  */
});
