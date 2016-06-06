/* vim: set sw=2 ts=2 : */
'use strict';

function _CircleController($scope, $rootScope, $location, Subheader) {
  $location.path('/circle-movie');
  $rootScope.$broadcast('refreshSubheaderEvent', '/circle');
  /*
  var currentSubheaderTab = Subheader.getTab();
  switch(currentSubheaderTab) {
    case '学校':
      $location.path('/circle-college');
      break;
  }
  */
}

function _CircleHandler($scope, $location, Subheader) {
}

app.controller('CircleController', function($scope, $rootScope, $location, Subheader) {
  _CircleController($scope, $rootScope, $location, Subheader);

  _CircleHandler($scope, $rootScope, $location, Subheader);
});
