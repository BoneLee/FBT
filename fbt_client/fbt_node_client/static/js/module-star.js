/* vim: set sw=2 ts=2 expandtab : */
'use strict';

angular.module('star', [])
.service('star', function($rootScope, $timeout) {
  return {
    render: function(initScore, totalScore, group, callback) {
      group = group ? group : '';
      $timeout(function() {
        $rootScope.$broadcast('star-render', {
          initScore: initScore,
          totalScore: totalScore,
          group: group,
          callback: callback
        });
      })
    }
  };
})
.directive('starContainer', ['star', function(star) {
  return {
    restrict: 'E',
    replace: true,
    link: function(scope, elem, attrs) {
      scope.$on('star-render', function(event, d) {
        if(d.group != attrs.group) return;

        scope.display = true;
        scope.initScore = d.initScore;
        scope.totalScore = d.totalScore;
        scope.currentSelectedIndex = scope.initScore;
        scope.callback = d.callback;
      });

      scope.isSelected = function(index) {
        return scope.currentSelectedIndex >= index ? true : false;
      };

      scope.previewSelection = function(index) {
        scope.currentSelectedIndex = index;
      };

      scope.clearSelection = function() {
        scope.currentSelectedIndex = scope.initScore;
      };

      scope.updateSeletion = function(index) {
        var score = index;
        scope.initScore = score;
        scope.callback(score);
      };
    },
    scope: {},
    template:
      '<div class="star-container" ng-show="display" ng-init="display = false">' +
        '<span ng-repeat="i in [] | range: initScore track by $index">' +
          '<i ng-class="{true:\'fa fa-star\', false:\'fa fa-star-o\'}[isSelected($index+1)]" ng-mouseenter="previewSelection($index+1)" ng-mouseleave="clearSelection()" ng-click="updateSeletion($index+1)"></i>' +
        '</span>' +
        '<span ng-repeat="i in [] | range: totalScore-initScore track by $index">' +
          '<i ng-class="{true:\'fa fa-star\', false:\'fa fa-star-o\'}[isSelected($index+initScore+1)]" ng-mouseenter="previewSelection($index+initScore+1)" ng-mouseleave="clearSelection()" ng-click="updateSeletion($index+initScore+1)"></i>' +
        '</span>' +
      '</div>',
  };
}]);
