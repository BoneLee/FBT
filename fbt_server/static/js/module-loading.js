/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('loading', [])
.service('loading', function($rootScope, $timeout) {
  return {
    show: function(title) {
      $timeout(function() {
        $rootScope.$broadcast('loading-show', title)
      });
    },
    hide: function() {
      $timeout(function() {
        $rootScope.$broadcast('loading-hide')
      });
    }
  };
})
.directive('loadingContainer', ['loading', function(loading) {
  return {
    restrict: 'E',
    replace: true,
    template:
      '<div id="loading-container" ng-show="loading.display">' +
        '<div>' + 
          '<div>' + 
            '<img ng-src="//test.friendsbt.com/statics/img/loading.gif">' +
            '<label>{{ loading.title }}</label>' +
          '</div>' +
        '</div>' +
      '</div>',
    controller: function($scope) {
      if(!$scope.loading) $scope.loading = {};

      $scope.loading.display = false;
      $scope.$on('loading-show', function(event, title) {
        $scope.loading.display = true;
        $scope.loading.title = title ? title : '疯狂加载中...';
      });
      $scope.$on('loading-hide', function() {
        $scope.loading.display = false;
      });
    }
  };
}]);
