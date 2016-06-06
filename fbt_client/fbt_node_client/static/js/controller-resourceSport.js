/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceSportController', function($scope, $location, $routeParams, pagination, AllRes, Subheader) {
  $scope.sport = $routeParams.sport;

  var res_type = Subheader.getIndexByTab('体育');
  var page = 1;
  var sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : '0';
  var total_page = 1;
  AllRes.getAllRes(res_type, page, sort_by, function(data) {
    $scope.resource_list = data && data.resource_list
      ? data.resource_list
      : [];
    total_page = data.size;

    pagination.render(1, total_page, 'resource-sport', function(currentPageNum, totalPageNum) {
      AllRes.getAllRes(res_type, currentPageNum, sort_by, function(data) {
        $scope.resource_list = data && data.resource_list
          ? data.resource_list
          : [];
      });
    });
  });

  $scope.viewCollegeResourceDetailsClickHandler = function(sport, course) {
    //$location.path('/resource-sport2/' + sport + '/' + course);
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    var res_type = Subheader.getIndexByTab('体育');
    var page = 1;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : '0';
    
    AllRes.getAllRes(res_type, page, sort_by, function(data) {
      $scope.resource_list = data && data.resource_list
        ? data.resource_list
        : [];
      total_page = data.size;

      pagination.render(1, total_page, 'resource-sport', function(currentPageNum, totalPageNum) {
        AllRes.getAllRes(res_type, currentPageNum, sort_by, function(data) {
          $scope.resource_list = data && data.resource_list
            ? data.resource_list
            : [];
        });
      });
    });
  };
});
