/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceCommonController', function($scope, $location, $window, $routeParams, pagination, AllRes, Subheader, loading, $modal, downloader) {
  $scope.common = $routeParams.common;

  var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
  var page = $window.currentPageNum ? $window.currentPageNum : 1;
  $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : '最热';
  var sort_by = $scope.sort_by ? {'最新': '0', '最热': '1', '在线': '2'}[$scope.sort_by] : '0';
  var total_page = 1;

  loading.show();
  AllRes.getAllRes(res_type, page, sort_by, function(err, data) {
    loading.hide();

    if(err)
      return;

    $scope.resource_list = data && data.resource_list.sort(function(x, y) {return x.sticky && x.sticky > 0 ? -1 : 1})
      ? data.resource_list
      : [];
    total_page = data.size;

    if(!total_page) {
      pagination.hide('resource-common');
      return;
    }

    pagination.render(page, total_page, 'resource-common', function(currentPageNum, totalPageNum) {
      $window.currentPageNum = currentPageNum;
      $window.currentSortBy = $scope.sort_by;
      loading.show();
      AllRes.getAllRes(res_type, currentPageNum, sort_by, function(err, data) {
        loading.hide();
        $scope.resource_list = data && data.resource_list.sort(function(x, y) {return x.sticky && x.sticky > 0 ? -1 : 1})
          ? data.resource_list
          : [];
      });
    });
  });

  $scope.viewResourceDetailsClickHandler = function(resource) {
    $location.path('/resource-' + Subheader.getTabByIndex(res_type) + '/details/').search({'resource':resource, 'isPrivate':0});
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    delete $window.currentPageNum;
    delete $window.currentSortBy;

    var res_type = Subheader.getIndexByTab($location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
    var page = $window.currentPageNum ? $window.currentPageNum : 1;
    $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : $scope.sort_by;
    $window.currentSortBy = $scope.sort_by;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'最新': '0', '最热': '1', '在线': '2'}[$scope.sort_by] : '0';
   
    loading.show();
    AllRes.getAllRes(res_type, page, sort_by, function(err, data) {
      loading.hide();

      if(err)
        return;

      $scope.resource_list = data && data.resource_list.sort(function(x, y) {return x.sticky && x.sticky > 0 ? -1 : 1})
        ? data.resource_list
        : [];
      total_page = data.size;

      if(!total_page) {
        pagination.hide('resource-common');
        return;
      }

      pagination.render(page, total_page, 'resource-common', function(currentPageNum, totalPageNum) {
        $window.currentPageNum = currentPageNum;
        $window.currentSortBy = $scope.sort_by;
        loading.show();
        AllRes.getAllRes(res_type, currentPageNum, sort_by, function(err, data) {
          loading.hide();

          if(err)
            return;

           $scope.resource_list = data && data.resource_list.sort(function(x, y) {return x.sticky && x.sticky > 0 ? -1 : 1})
            ? data.resource_list
            : [];
        });
      });
    });
  };
  $scope.downloadResourceClickHandler = function(index) {
    $scope.isPrivate = 0;
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
