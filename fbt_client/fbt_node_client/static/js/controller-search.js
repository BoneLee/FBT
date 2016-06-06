/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('SearchController', function($scope, $location, $window, $routeParams, pagination, SearchRes, Subheader, loading, $modal) {
  var searchKeywords = $routeParams.searchKeywords;

  var page = $window.currentPageNum ? $window.currentPageNum : 1;
  $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : '资源库';
  var total_page = 1;

  loading.show();
  SearchRes.getResByKey(searchKeywords, page, 0, function(err, data) {
    loading.hide();

    if(err)
      return;

    $scope.resource_list = data && data.resource_list
      ? data.resource_list
      : [];
    total_page = data.size;

    if(!total_page) {
      pagination.hide('search');
      return;
    }

    pagination.render(page, total_page, 'search', function(currentPageNum, totalPageNum) {
      $window.currentPageNum = currentPageNum;
      $window.currentSortBy = $scope.sort_by;
      loading.show();
      SearchRes.getResByKey(searchKeywords, currentPageNum, 0, function(err, data) {
        loading.hide();

        if(err)
          return;

        $scope.resource_list = data && data.resource_list
          ? data.resource_list
          : [];
      });
    });
  });

  $scope.viewResourceDetailsClickHandler = function(resource) {
    var searchUrl = $location.url();
    if ($scope.sort_by == '资源库')
      $location.path('/home/details/').search({'resource':resource, 'isPrivate':0, 'searchUrl':searchUrl});
    else if ($scope.sort_by == '朋友圈')
      $location.path('/home/details/').search({'resource':resource, 'isPrivate':1, 'searchUrl':searchUrl});
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    delete $window.currentPageNum;
    delete $window.currentSortBy;

    var page = $window.currentPageNum ? $window.currentPageNum : 1;
    $scope.sort_by = $window.currentSortBy ? $window.currentSortBy : $scope.sort_by;
    $window.currentSortBy = $scope.sort_by;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'资源库': '0', '朋友圈': '1'}[$scope.sort_by] : '0';
   
    loading.show();
    SearchRes.getResByKey(searchKeywords, page, sort_by, function(err, data) {
      loading.hide();

      if(err)
        return;

      $scope.resource_list = data && data.resource_list
        ? data.resource_list
        : [];
      total_page = data.size;

      if(!total_page) {
        pagination.hide('search');
        return;
      }

      pagination.render(page, total_page, 'search', function(currentPageNum, totalPageNum) {
        $window.currentPageNum = currentPageNum;
        $window.currentSortBy = $scope.sort_by;
        loading.show();
        SearchRes.getResByKey(searchKeywords, currentPageNum, sort_by, function(err, data) {
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
    $scope.isPrivate = $scope.sort_by == '资源库' ? 0 : 1;
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
