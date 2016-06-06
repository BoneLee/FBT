/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceCollegeController', function($scope, $location) {
  $scope.groups = [];
  for(var i = 0; i < 55; i++) {
    $scope.groups.push({'title':Math.floor(Math.random(i)*10000)});
  }

  $scope.viewCollegeResourceClickHandler = function(college) {
    $location.path('/resource-college/' + college);
  };
});

app.controller('ResourceCollegeController2', function($scope, $location, $routeParams) {
  $scope.college = $routeParams.college;
  $scope.courses = [];
  for(var i = 0; i < 55; i++) {
    $scope.courses.push({'title':Math.floor(Math.random(i)*10000)});
  }

  $scope.viewCollegeResourceDetailsClickHandler = function(college, course) {
    $location.path('/resource-college/' + college + '/' + course);
  };
});
