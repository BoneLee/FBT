/* vim: set sw=2 ts=2 : */
'use strict';

function _ResourceController($scope, $rootScope, $location, Subheader) {
  $location.path('/resource-movie');
  $rootScope.$broadcast('refreshSubheaderEvent', '/resource');
  /*
  var currentSubheaderTab = Subheader.getTab();
  switch(currentSubheaderTab) {
    case '学校':
      $location.path('/resource-college');
      break;
  }
  */
}

function _ResourceHandler($scope, $location, Subheader) {
}

app.controller('ResourceController', function($scope, $rootScope, $location, Subheader) {
  _ResourceController($scope, $rootScope, $location, Subheader);

  _ResourceHandler($scope, $rootScope, $location, Subheader);
});
