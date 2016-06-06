/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('pagination', [])
.service('pagination', function($rootScope, $timeout) {
  return {
    render: function(currentPageNum, totalPageNum, group, callback) {
      group = group ? group : '';
      $timeout(function() {
        $rootScope.$broadcast('pagination-render', {
          currentPageNum: currentPageNum,
          totalPageNum: totalPageNum,
          group: group,
          callback: callback
        });
      })
    },
    hide: function(group) {
      $timeout(function() {
        $rootScope.$broadcast('pagination-hide', {
          group: group,
        });
      });
    }
  };
})
.directive('paginationContainer', ['pagination', function(pagination) {
  return {
    restrict: 'E',
    replace: true,
    link: function(scope, elem, attrs) {
      var callback = function(currentPageNum, totalPageNum) {
        console.log('You clicked ' + currentPageNum + '/' + totalPageNum);
      };

      scope.goPage = function(pageNum, totalPageNum) {
        scope.$parent.$broadcast('pagination-render', {
          currentPageNum: pageNum,
          totalPageNum: totalPageNum,
          group: attrs.group,
          callback: callback
        });

        callback(pageNum, totalPageNum);
      };

      scope.$on('pagination-hide', function(event, d) {
        if(d.group != attrs.group) return;

        scope.display = false;
      });

      scope.$on('pagination-render', function(event, d) {
        if(d.group != attrs.group) return;

        scope.display = true;

        var begin = 1;
        var end = d.totalPageNum;
        if(d.callback && typeof(d.callback) == 'function') callback = d.callback;

        scope.pageNums1 = [];
        for(var i = 0; i < 3; i++) {
          var pageNum = d.currentPageNum - 3 + i;
          if(pageNum > 0 && pageNum <= end) scope.pageNums1.push(pageNum);
        }
        scope.pageNums2 = [];
        for(var i = 0; i < 3; i++) {
          var pageNum = d.currentPageNum + 1 + i;
          if(pageNum > 0 && pageNum <= end) scope.pageNums2.push(pageNum);
        }

        if(scope.pageNums1 && scope.pageNums1[0] > begin) {
          scope.prevDots = true;
          scope.beginButton = true;
        }
        else {
          scope.prevDots = false;
          scope.beginButton = false;
        }

        if(scope.pageNums2 && scope.pageNums2[scope.pageNums2.length-1] < end) {
          scope.nextDots = true;
          scope.endButton = true;
        }
        else {
          scope.nextDots = false;
          scope.endButton = false;
        }

        scope.currentPageNum = d.currentPageNum;
        scope.totalPageNum = d.totalPageNum;

        scope.prevButton = d.currentPageNum <= begin ? false : true;
        scope.nextButton = d.currentPageNum >= end ? false : true;
      });
    },
    scope: {},
    template:
      '<div class="pagination-container" ng-show="display" ng-init="display = false">' +
        '<span class="prev-button" ng-click="goPage(currentPageNum-1, totalPageNum)" ng-class="{true: \'\', false: \'disabled\'}[prevButton]">&lt</span>' +
        '<span class="begin-button" ng-click="goPage(1, totalPageNum)" ng-show="beginButton">1</span>' +

        '<span class="prev-dots disabled" ng-show="prevDots">...</span>' +

        '<span class="page-button1" ng-click="goPage(pageNum, totalPageNum)" ng-repeat="pageNum in pageNums1">{{ pageNum }}</span>' +
        '<span class="current-button" ng-show="currentPageNum">{{ currentPageNum }}</span>' +
        '<span class="page-button2" ng-click="goPage(pageNum, totalPageNum)" ng-repeat="pageNum in pageNums2">{{ pageNum }}</span>' +

        '<span class="next-dots disabled" ng-show="nextDots">...</span>' +

        //'<span class="end-button" ng-click="goPage(totalPageNum, totalPageNum)" ng-show="endButton">{{ totalPageNum }}</span>' +
        '<span class="next-button" ng-click="goPage(currentPageNum+1, totalPageNum)" ng-class="{true: \'\', false: \'disabled\'}[nextButton]">&gt</span>' +
      '</div>',
  };
}]);
