/* vim: set sw=2 ts=2 : */

var app = angular.module('fbtApp', ['ngRoute', 'ngCookies', 'ui.bootstrap', 'toaster', 'loading', 'pagination', 'tableSort', 'snapscroll', 'swipe', 'richTextEditor','share','bottomLoading', 'ngSanitize','monospaced.qrcode','directives.clamp','pdf']);

app.config(function($routeProvider) {

  $routeProvider
    .when('/rank', {
      controller: 'rankController',
      templateUrl: '/statics/partials/creditsrank.html'
    })
    .when('/home', {
      controller: 'homeController',
      templateUrl: '/statics/partials/home.html'
    })
    .when('/fmall', {
      controller: 'NestedSnapscrollController',
      templateUrl: '/statics/partials/fmall.html'
    })
    .when('/schools', {
      controller: 'schoolsController',
      templateUrl: '/statics/partials/schools.html'
    })
    .when('/studysearch_resource', {
      controller: 'searchController',
      //templateUrl: '/statics/partials/resource-more.html',
      templateUrl: '/statics/partials/course-resource.html',
      url: '/resource/search',
      currentType: 0
    })
    .when('/studysearch_course', {
      controller: 'searchController',
      templateUrl: '/statics/partials/course-more.html',
      url: '/course/search',
      currentType: 1
        //templateUrl: '/statics/partials/search.html'
    })
    .when('/course_resource', {
      controller: 'courseResourceController',
      templateUrl: '/statics/partials/course-resource.html'
    })
    .when('/studysearch', {
      controller: 'studySearchController',
      templateUrl: '/statics/partials/study-search.html'
    })
    .when('/schools/:university', {
      controller: 'collegesController',
      templateUrl: '/statics/partials/colleges.html'
    })
    .when('/schools/:university/:college/:course_name/details', {
      controller: 'courseDetailsController',
      templateUrl: '/statics/partials/course-details.html'
    })
    .when('/schools/:university/:college', {
      controller: 'collegesController',
      templateUrl: '/statics/partials/colleges.html'
    })
    .when('/schools/:university/:college/:course', {
      controller: 'coursesController',
      templateUrl: '/statics/partials/courses.html'
    })
    .when('/recommendation', {
      controller: 'recommendController',
      templateUrl: '/statics/partials/resource-recommendation.html'
    })
    .when('/details', {
      controller: 'detailsController',
      templateUrl: '/statics/partials/details.html'
    })
    .when('/recommendation/:tag', {
      controller: 'resourceMoreCtrl',
      templateUrl: '/statics/partials/resource-more.html'
    })
    .when('/myresource', {
      controller: 'MyResController',
      templateUrl: '/statics/partials/myresource.html'
    })
    .when('/myresource/downloaded', {
      controller: 'MyResController',
      templateUrl: '/statics/partials/myresource.html'
    })
    .when('/myresource/audited', {
      controller: 'MyResController',
      templateUrl: '/statics/partials/myresource.html'
    })
    .when('/myresource/auditing', {
      controller: 'MyResController',
      templateUrl: '/statics/partials/myresource.html'
    })
    .when('/myresource/unaudited', {
      controller: 'MyResController',
      templateUrl: '/statics/partials/myresource.html'
    })
    .when('/myresource/details', {
      controller: 'detailsController',
      templateUrl: '/statics/partials/details.html'
    })
    .when('/myresource/unaudited/unpassdetail', {
      controller: 'unpassDetailController',
      templateUrl: '/statics/partials/unpassdetail.html'
    })
    .when('/reward/myreward/:myRewardType', {
      controller: 'MyRewardController',
      templateUrl: '/statics/partials/myreward.html'
    })
    .when('/reward', {
      controller: 'RewardController',
      templateUrl: '/statics/partials/reward.html'
    })
    .when('/message', {
      controller: 'messageCenterController',
      templateUrl: '/statics/partials/message-center.html'
    //}).when('/schools/:university/:college/:course_name/question_detail', {
    //  controller: 'QuestionDetailController',
    //  templateUrl: '/statics/partials/question-detail.html'
    //}).when('/question', {
    //  controller: 'QuestionClassController',
    //  templateUrl: '/statics/partials/question_class.html'
    //}).when('/myquestion', {
    //  controller: 'MyQuestionController',
    //  templateUrl: '/statics/partials/myquestion.html'
    }).when('/star', {
      controller: 'StarController',
      templateUrl: '/statics/partials/star.html'
    }).when('/starsearch', {
      //controller: 'StarSearchController',
      templateUrl: '/statics/partials/star-search.html'
    }).when('/find/experience', {
      controller: 'FindDetailsController',
      templateUrl: '/statics/partials/find-details.html'
    })
    //问答主页
    .when('/qahome/:questionClass/:questionScope', {
      controller: 'QuestionController',
      templateUrl: '/statics/partials/qa-home.html'
    })
    .when('/askquestion', {
      controller: 'AskQuestionController',
      templateUrl: '/statics/partials/ask-question.html'
    })
    .when('/replyquestion/:questionId/:questionClass/:questionTitle', {
      controller: 'ReplyQuestionController',
      templateUrl: '/statics/partials/reply-question.html'
    })
    .when('/qadetail/:questionId', {
      controller: 'QuestionAnswerDetailController',
      templateUrl: 'statics/partials/qa-detail.html',
        reloadOnSearch:false
    })
  .when('/explore', {
    controller: 'experienceEditController',
    templateUrl: '/statics/partials/experience-edit.html'
  }).when('/info',{
        templateUrl: '/statics/partials/show-information.html',
        controller: 'ShowInfoController'
      }).when('/usersearch', {
        controller: 'searchController',
        templateUrl: '/statics/partials/user-more.html',
        url:'/user/search',
        currentType: 2
        //templateUrl: '/statics/partials/search.html'
      }).when('/qsearch', {
        controller: 'searchController',
        templateUrl: '/statics/partials/question-more.html',
        url: '/question/search',
        currentType: 3
        //templateUrl: '/statics/partials/search.html'
      }).when('/rule', {
        templateUrl: '/statics/partials/rule.html',
      })
      //.when('/preview/:fileId/:fileName',{
      //  templateUrl: '/statics/preview/preview.html',
      //})
  .otherwise({
    template: '',
    controller: function($location) {
      var redirectURL = '/qahome/校园/1';
      $location.path(redirectURL);
    }
  });

});

app.filter('type_icon', function() {
  var filter = function(resource_name) {
    var type = resource_name.split('.').splice(-1)[0];
    var icon = '';
    switch (type) {
      case 'rar':
      case 'zip':
      case 'tar':
        icon = 'rar.png';
        break;
      case 'ppt':
      case 'pptx':
        icon = 'ppt.png';
        break;
      case 'pdf':
        icon = 'pdf.png';
        break;
      case 'doc':
      case 'docx':
        icon = 'word.png';
        break;
      case 'xls':
      case 'xlsx':
      case 'csv':
        icon = "excel.png";
        break;
      case 'txt':
        icon = 'txt.png';
        break;
      case 'exe':
        icon = 'software.png';
        break;
      case 'mp3':
        icon = 'audio.png';
        break;
      case 'rmb':
      case 'mp4':
      case 'avi':
        icon = 'mv.png';
        break;
      case 'gif':
      case 'jpg':
      case 'png':
        icon = 'img.png';
        break;
      default:
        icon = 'unknown.png';
    }
    return icon;
  };
  return filter;
});

// TO BE DEPRECATED!
app.filter('local_date', function() {
  var filter = function(input) {
    return ctime2LocaleDateString(input);
  };
  return filter;
});

app.filter('showList', function() {
  var filter = function(input, char_limit) {
    var res = ""
    if (input) {
      res = input[0];
      for (var i = 1; i < input.length; i++) {
        if (res.length + input[i].length + 2 > char_limit) {
          res += "等";
          break;
        } else
          res += ', ' + input[i];
      }
    }
    return res;
  };
  return filter;
});

app.filter('twoLinePoint', function() {
  var filter = function(text) {
    text = text || '';
    var len = 0;
    var i = 0;
    for (; i < text.length; i++) {
      if (text[i].match(/[\ |\~|\`|\!|\@|\#|\$|\%|\^|\&|\*|\(|\)|\-|\_|\+|\=|\||\\|\[|\]|\{|\}|\;|\:|\"|\'|\,|\<|\.|\>|\/|\?|？|，|。|；|——|+|－]/g) != null) {
        len += 0.5; //标点符号占半个
      } else if (text[i].match(/[^\x00-\xff]/ig) != null) { //全角
        len += 2;
      } else {
        len += 1;
      }
      if (len >= 30 || i >= 30) { //这里的10是指能有多少个英文字符的个数
        break;
      }
    }
    // var showText = text;
    // if(text.length >= 20){
    //   showText = text.substring(0,18) + '...';
    // }
    if (i == text.length) {
      return text;
    } else {
      return text.substring(0, i) + '...';
    }
  }
  return filter;
});


app.filter('isPreviewAble', function() {
  var filter = function(input) {
    if (input == undefined) {
      return false;
    }
    var file_name = input.filename;
    var file_size = input.file_size;
    var extentName = getFileExtension(file_name).toLocaleLowerCase();
    var array1 = ['.docx', '.doc','.odt','.rtf','.wps', '.pptx','.ppt','.odp','.dps','.pdf', '.jpg', '.gif'];
    var array2 = ['.xlsx', '.ods', '.xls', '.csv','.et'];
    if (array1.indexOf(extentName) >= 0 && file_size <= 10485760) { //小于10M
      return true;
    } else if (array2.indexOf(extentName) >= 0 && file_size <= 5242880) { //小于5M
      return true;
    } else {
      return false;
    }
  }
  return filter;
});


app.filter('isImg', function() {
  var filter = function(input) {
    if (input == undefined) {
      return false;
    }
    var file_name = input.filename;
    var extentName = getFileExtension(file_name).toLocaleLowerCase();
    var array1 = ['.jpg', '.gif'];
    if (array1.indexOf(extentName) >= 0 ) {
      return true;
    }
      return false;
  }
  return filter;
});



app.controller('RootController', function($scope, $window) {
  $scope.$on('$routeChangeSuccess', function() {
    $scope.workspaceHeight = $window.innerHeight - 60 + 'px';
    //$scope.workspaceLeftHeight = $window.innerHeight - 80 + 'px';
    //$scope.workspaceWithoutPagiHeight = $window.innerHeight - 130 + 'px';
  });
  angular.element($window).on('resize', function() {
    $scope.$apply(function() {
      $scope.workspaceHeight = $window.innerHeight - 60 + 'px';
      //$scope.workspaceLeftHeight = $window.innerHeight - 80 + 'px';
      //$scope.workspaceWithoutPagiHeight = $window.innerHeight - 130 + 'px';
    });
  });
});

app.controller('QuickNavController', ['$scope', '$sce', '$location',
  function($scope, $sce, $location) {
    var navs = decodeURI($location.url()).split('?')[0].replace('/', '').split(/[\-\/]/);
    var tmp = [];
    var tmp2 = [];
    var mapper = {
      'schools': ['学校', 'schools'],
      'recommendation': ['推荐', 'recommendation'],
      'resmore': ['更多', 'resmore'],
      'details': ['详情', 'details'],
      'search': ['资源搜索', 'search'],
      'search_course': ['课程搜索', 'search_course'],
      'course_resource': ['课程资源', 'course_resource'],
      'my': ['我的悬赏', 'my'],
      'resource': ['资源库', 'resource'],
      'circle': ['朋友圈', 'circle'],
      'reward': ['悬赏', 'reward'],
      'myresource': ['我的资源', 'myresource'],
      'message': ['消息中心', 'message'],
      // 'unpassdetail': ['资源详情', 'unpassdetail'],
      'audited': ['成功上传', 'audited'],
      'auditing': ['待审资源', 'auditing'],
      'unaudited': ['被拒资源', 'myresource/unaudited?page_num=' + $location.search().page_num + '&r_type=' + $location.search().r_type],
      'downloaded': ['我的下载', 'downloaded'],
      'unpassdetail': ['被拒详情', 'unpassdetail'],
      'course': ['课程', 'schools/?university=' + $location.search().university + '&college=' + $location.search().college],
      'myreward': ['我的悬赏', 'myreward'],
      'sponsed': ['我发起的'],
      'related': ['我参与的'],
      'question_detail': ['课程讨论', 'question_detail'],
    };
    if (navs.length === 4 && navs[0] === 'schools') {
      var c = navs[navs.length - 1];
      if (c[0] === '1')
        c = Base64.decode(c.slice(1));
      else
        c = c.slice(1);
      navs[navs.length - 1] = c;
    }
    for (var i = 0; i < navs.length; i++) {
      /*
       if(navs[i] == 'details') {
       tmp.push('<a>' + mapper[navs[i]][0] + '</a>');
       break;
       }*/
      if (i != navs.length - 1) {
        if (navs[i] in mapper) {
          tmp.push('<a href="#/' + mapper[navs[i]][1] + '">' + mapper[navs[i]][0] + '</a>');
          tmp2.push(mapper[navs[i]][1]);
        } else {
          tmp2.push(navs[i]);
          tmp.push('<a href="#/' + tmp2.join('/') + '">' + navs[i] + '</a>');
        }
      } else {
        if (navs[i] in mapper) {
          tmp.push('<a>' + mapper[navs[i]][0] + '</a>');
        } else {
          tmp.push('<a>' + navs[i] + '</a>');
        }
      }
    }
    $scope.navs = $sce.trustAsHtml('当前位置：' + tmp.join(' > '));
  }
]);
//app.config(function ($httpProvider) {
//  $httpProvider.defaults.transformRequest = function(data){
//      if (data === undefined) {
//          return data;
//      }
//      return $.param(data);
//  };
//  $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8';
//});

app.constant('resCountPerPage', 10);
app.filter('static_path', function() {
  var filter = function(path) {
    return '//test.friendsbt.com/' + path;
  };
  return filter;
});

app.directive('keyboardKeys', ['$document',
  function($document) {
    return {
      restrict: 'A',
      link: function(scope) {
        var keydown = function(e) {
          if (e.keyCode === 38) {
            e.preventDefault();
            scope.$emit('arrow-up');
          }
          if (e.keyCode === 40) {
            e.preventDefault();
            scope.$emit('arrow-down');
          }
        };
        $document.on('keydown', keydown);
        scope.$on('$destroy', function() {
          $document.off('keydown', keydown);
        });
      }
    }
  }
]);

app.controller('NestedSnapscrollController', ['$scope', '$window',
  function($scope, $window) {
    // these min and max values are only hardcoded for demonstration
    var minNestedSnapIndex = 0,
      maxNestedSnapIndex = 4;
    $scope.nestedSnapIndex = 0;

    $scope.$on('arrow-up', function() {
      //$scope.$apply(function () {
      $scope.nestedSnapIndex--;
      //});
    });
    $scope.$on('arrow-down', function() {
      //$scope.$apply(function () {
      $scope.nestedSnapIndex++;
      //});
    });

    $scope.swipeUp = function($event) {
      if ($scope.nestedSnapIndex + 1 <= maxNestedSnapIndex) {
        $scope.nestedSnapIndex++;
        $event.stopPropagation();
      }
      // else, allow bubbling up since this instance is already scrolled to the end
    };
    $scope.swipeDown = function($event) {
      if ($scope.nestedSnapIndex - 1 >= minNestedSnapIndex) {
        $scope.nestedSnapIndex--;
        $event.stopPropagation();
      }
      // else, allow bubbling up since this instance is already scrolled to the end
    };

    $scope.$on('$routeChangeSuccess', function() {
      //$scope.$apply(function () {
      $scope.workspaceHeight = $window.innerHeight - 60 + 'px';
      //});
      //$scope.workspaceLeftHeight = $window.innerHeight - 80 + 'px';
      //$scope.workspaceWithoutPagiHeight = $window.innerHeight - 130 + 'px';
    });
    angular.element($window).on('resize', function() {
      //$scope.$apply(function () {
      $scope.workspaceHeight = $window.innerHeight - 60 + 'px';
      //$scope.workspaceLeftHeight = $window.innerHeight - 80 + 'px';
      //$scope.workspaceWithoutPagiHeight = $window.innerHeight - 130 + 'px';
      //});
    });
  }
]);

app.directive('coinFormat', function() {
  return {
    restrict: 'A',
    scope: {
      coin: '@',
      suffix: '@',
      coinFormat: '='
    },
    link: function(scope, element, attrs) {
      var check_coin = function(coin) {
        coin = coin || 0;
        if (coin >= 10000) {
           $(element).attr('title', coin);
           coin = (coin / 10000).toFixed(1) + 'W';
        } else {
          $(element).removeAttr('title');
        }
        if (scope.suffix)
          coin += scope.suffix;
        $(element).text(coin);
      };
      //check_coin(coin);
      scope.$watch('coinFormat', function(value) {
        check_coin(value);
      });
    }
  };
});

app.directive('scrollTo', function($timeout) {
  return {
    restrict: 'A',
    scope: {
      scrollTo: '='
    },
    link: function(scope, element, attrs) {
      $timeout(function() {
        $(element).scrollTop(scope.scrollTo || 0);
      }, 1);
    }
  };
});
