/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('CircleCommonController', function($rootScope, $scope, $location, $window, $routeParams, pagination, AllFriendRes, Subheader, loading, $modal, downloader) {
  $rootScope.$broadcast('refreshSubheaderEvent', $location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);

  var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
  res_type = res_type === undefined ? -1 : res_type;
  var page = $window.currentPageNum ? $window.currentPageNum : 1;
  $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : '最热';
  var sort_by = $scope.sort_by ? {'最新': '0', '最热': '1', '在线': '2'}[$scope.sort_by] : '0';
  var total_page = 1;

  loading.show();
  AllFriendRes.getRes(res_type, sort_by, page, function(err, data) {
    loading.hide();

    if(err)
      return;

    $scope.resource_list = data && data.resource_list
      ? data.resource_list
      : [];
    total_page = data.size;

    if(!total_page) {
      pagination.hide('circle-common');
      return;
    }

    pagination.render(page, total_page, 'circle-common', function(currentPageNum, totalPageNum) {
      $window.currentPageNum = currentPageNum;
      $window.currentSortBy = $scope.sort_by;
      loading.show();
      AllFriendRes.getRes(res_type, sort_by, currentPageNum, function(err, data) {
        loading.hide();

        if(err)
          return;

        $scope.resource_list = data && data.resource_list
          ? data.resource_list
          : [];
      });
    });
  });

  $scope.viewResourceDetailsClickHandler = function(circle) {
    if (res_type == -1)
      $location.path('/circle/details/').search({'resource':circle, 'isPrivate':1});
    else
      $location.path('/circle-' + Subheader.getTabByIndex(res_type) + '/details/').search({'resource':circle, 'isPrivate':1});
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    delete $window.currentPageNum;
    delete $window.currentSortBy;

    var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
    res_type = res_type === undefined ? -1 : res_type;
    var page = $window.currentPageNum ? $window.currentPageNum : 1;
    $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : $scope.sort_by;
    $window.currentSortBy = $scope.sort_by;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'最新': '0', '最热': '1', '在线': '2'}[$scope.sort_by] : '0';
   
    loading.show();
    AllFriendRes.getRes(res_type, sort_by, page, function(err, data) {
      loading.hide();

      if(err)
        return;

      $scope.resource_list = data && data.resource_list
        ? data.resource_list
        : [];
      total_page = data.size;

      if(!total_page) {
        pagination.hide('circle-common');
        return;
      }

      pagination.render(page, total_page, 'circle-common', function(currentPageNum, totalPageNum) {
        $window.currentPageNum = currentPageNum;
        $window.currentSortBy = $scope.sort_by;
        loading.show();
        AllFriendRes.getRes(res_type, sort_by, currentPageNum, function(err, data) {
          loading.hide();

          if(err)
            return;

          $scope.resource_list = data && data.resource_list
            ? data.resource_list
            : [];
        });
      });
    });
  };
  $scope.downloadResourceClickHandler = function(index) {
    $scope.isPrivate = 1;
    if ($scope.resource_list[index].isDir) {
      $scope.curRes = $scope.resource_list;
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'folderModal.html',
        controller: 'folderModalCtrl',
        scope: $scope,
        resolve: {
          index: function () {
            return index;
          },  
          canDownload: function(){
            return true;
          },
          rid: function(){
            return '';
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
      downloader.download($scope.resource_list[index], $scope.isPrivate);
    }
  };
});
