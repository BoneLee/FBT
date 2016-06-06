/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceVarietyController', function($scope, $location, $routeParams, pagination, AllRes, Subheader) {
  $scope.variety = $routeParams.variety;

  var res_type = Subheader.getIndexByTab('综艺');
  var page = 1;
  var sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : '0';
  var total_page = 1;
  AllRes.getAllRes(res_type, page, sort_by, function(data) {
    $scope.resource_list = data && data.resource_list
      ? data.resource_list
      : [];
    total_page = data.size;

    pagination.render(1, total_page, 'resource-variety', function(currentPageNum, totalPageNum) {
      AllRes.getAllRes(res_type, currentPageNum, sort_by, function(data) {
        $scope.resource_list = data && data.resource_list
          ? data.resource_list
          : [];
      });
    });
  });

  $scope.viewCollegeResourceDetailsClickHandler = function(variety, course) {
    //$location.path('/resource-variety2/' + variety + '/' + course);
  };

  $scope.changeSortbyClickHandler = function(sort_by) {
    var res_type = Subheader.getIndexByTab('综艺');
    var page = 1;
    var total_page = 1;
    sort_by = $scope.sort_by ? {'最新': '0', '最热': '1'}[$scope.sort_by] : '0';
    
    AllRes.getAllRes(res_type, page, sort_by, function(data) {
      $scope.resource_list = data && data.resource_list
        ? data.resource_list
        : [];
      total_page = data.size;

      pagination.render(1, total_page, 'resource-variety', function(currentPageNum, totalPageNum) {
        AllRes.getAllRes(res_type, currentPageNum, sort_by, function(data) {
          $scope.resource_list = data && data.resource_list
            ? data.resource_list
            : [];
        });
      });
    });
  };
});
