/* vim: set sw=2 ts=2 : */
'use strict';

function _ResourceController($scope, $location, Subheader) {
  var currentSubheaderTab = Subheader.getTab();
  switch(currentSubheaderTab) {
    case '学校':$location.path('/resource-college');
      
      break;
    case '推荐':
      $location.path('/resource-recommendation');
      break;
  }
}

function _ResourceHandler($scope, $location, Subheader) {
}

app.controller('ResourceController', function($scope, $location, Subheader) {
  _ResourceController($scope, $location, Subheader);

  _ResourceHandler($scope, $location, Subheader);
});
