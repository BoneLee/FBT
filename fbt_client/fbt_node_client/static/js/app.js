/* vim: set sw=2 ts=2 : */
'use strict';

var app = angular.module('fbtApp', ['ui.bootstrap', 'toaster', 'emoji', 'loading', 'pagination', 'selector', 'scselector', 'chatbox', 'star','empty', 'share', 'luegg.directives', 'monospaced.qrcode']);
app.config(function ($routeProvider) {
  $routeProvider
    .when('/top', {
      controller: 'fbRankCtrl',
      templateUrl: 'partials/fb.html'
    })
    .when('/login',
    { controller: 'LoginController',
      templateUrl: 'partials/login.html'
    })
    .when('/register',
    { controller: 'RegisterController',
      templateUrl: 'partials/register.html'
    })
    .when('/home',
    { controller: 'HomeController',
      templateUrl: 'partials/home.html'
    })
    .when('/home/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/mindetails.html'
    })
    /* Resource Begin */
    .when('/resource',
    {
      controller: 'ResourceController',
      templateUrl: 'partials/resource.html'
    })
    .when('/resource-college',
    {
      controller: 'ResourceCollegeController',
      templateUrl: 'partials/resource-college.html'
    })
    .when('/resource-college/:college',
    {
      controller: 'ResourceCollegeController2',
      templateUrl: 'partials/resource-college2.html'
    })
    .when('/resource-college/:college/:course',
    {
      controller: 'ResourceCollegeController3',
      templateUrl: 'partials/resource-college3.html'
    })
    .when('/resource-recommendation',
    {
      controller: 'ResourceRecommendationController',
      templateUrl: 'partials/resource-recommendation.html'
    })
    .when('/resource-recommendation/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-study',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-study/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-movie',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-movie/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-episode',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-episode/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-music',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-music/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-cartoon',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-cartoon/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-game',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-game/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-variety',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-variety/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-sport',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-sport/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-software',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-software/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/resource-other',
    {
      controller: 'ResourceCommonController',
      templateUrl: 'partials/resource-common.html'
    })
    .when('/resource-other/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    /* Resource End */

    /* Circle  Begin */
    .when('/circle',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-study',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-study/details/:resourceId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-movie',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-movie/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-episode',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-episode/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-music',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-music/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-cartoon',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-cartoon/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-game',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-game/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-variety',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-variety/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-sport',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-sport/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-software',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-software/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    .when('/circle-other',
    {
      controller: 'CircleCommonController',
      templateUrl: 'partials/circle-common.html'
    })
    .when('/circle-other/details/:circleId',
    {
      controller: 'ResourceDetailsController',
      templateUrl: 'partials/details.html'
    })
    /* Circle End */

    /* Reward Begin */
    .when('/reward',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-study',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-movie',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-episode',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-music',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-cartoon',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-game',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-variety',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-sport',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-software',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-other',
    {
      controller: 'RewardCommonController',
      templateUrl: 'partials/reward-common.html'
    })
    .when('/reward-my',
    {
      controller: 'RewardMyController',
      templateUrl: 'partials/reward-my.html'
    })
    /* Reward End */
    .when('/search/:searchKeywords',
    {
      controller: 'SearchController',
      templateUrl: 'partials/search.html'
    })
    .when('/myspace',
    {
      controller: 'MyspaceController',
      templateUrl: 'partials/myspace.html'
    })
    .when('/friend_res',
    {
      controller: 'FriendSpaceController',
      templateUrl: 'partials/friendSpace.html'
    })
    .otherwise({ redirectTo: '/login' });
});
app.config(function ($httpProvider) {
  $httpProvider.defaults.transformRequest = function(data){
      if (data === undefined) {
          return data;
      }
      return $.param(data);
  }
  $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
});
app.constant('downloadState', {'error': -1, 'queue': 0, 'downloading': 1, 'downloaded': 2});
app.constant('resCountPerPage', 10);
app.value('uploadHint', '');

app.directive('ngBlur', ['$parse', function($parse) {
    return function(scope, element, attr) {
        var fn = $parse(attr['ngBlur']);
        element.on('blur', function(event) {
            scope.$apply(function() {
                fn(scope, {$event:event});
            });
        });
    };
}])
.directive('ngFocus', ['$parse', function($parse) {
    return function(scope, element, attr) {
        var fn = $parse(attr['ngFocus']);
        element.on('focus', function(event) {
            scope.$apply(function() {
                fn(scope, {$event:event});
            });
        });
    };
}])
.filter('range', function() {
  return function(input, total) {
    total = parseInt(total);
    for(var i = 0; i < total; i++)
      input.push(i);
    return input;
  };
})
.filter('normFileName', function() {
  return function(input) {
    return input.trim().replace(/\.\w{1,4}$/, '');
  };
})
.filter('limitFileName', function() {
  return function(input) {
    var filename = input.trim().replace(/\.\w{1,4}$/, '');
    var limit = 30;
    return filename.length > limit
      ? filename.slice(0, limit - 3) + '...'
      : filename;
  };
})
.filter('normFileSize', function() {
  return function(fileSize) {
    fileSize = window.parseInt(fileSize);
    if (fileSize<1024)
      return fileSize+'B';
    else if (fileSize<1024*1024)
      return (fileSize/1024).toFixed(0) + 'KB';
    else{
      if (fileSize<1024*1024*1024)
        return (fileSize/1024/1024).toFixed(1) + 'MB';
      else
        return (fileSize/1024/1024/1024).toFixed(2) + 'GB';
    }
  }
});
