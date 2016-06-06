/* vim: set sw=2 ts=2 : */

var app = angular.module('fbtApp', ['ngRoute', 'toaster', 'ngCookies', 'ngAnimate', 'ui.bootstrap', 'bottomLoading', 'ImageCropper', 'monospaced.qrcode', 'directives.clamp', 'share','richTextEditor']);

function GetQueryString(name) {
    var reg = new RegExp("(^|&)"+ name +"=([^&]*)(&|$)");
    var r = window.location.search.substr(1).match(reg);
    if (r!=null) 
      return unescape(r[2]);
    else
      return null;
}

app.service('userSrv', ['$http', '$q', 'toaster', function ($http, $q, toaster) {
  var self = this;
  var user_info = {
    is_me: false,
    desc_editing: false
  };

  self.setUser = function (user) {
    user_info['user'] = user;
    $http({
      url: '/user/info',
      method: 'GET',
      params: {
        user: user
      }
    })
    .success(function(response) {
      if (response.err)
        toaster.pop('error', '系统提示', response.info, true);
      else {
        var tags = response.info.tags;
        var is_me = response.info.is_me;
        if (is_me)
          user_info.who = "我";
        else {
          if (response.info.gender==='男')
            user_info.who = "他";
          else
            user_info.who = "她";
        }
        response.info.tags = [];
        for (var key in tags) {
          if (typeof(tags[key]) !== "function")
            response.info.tags.push({
              tag: key,
              num: tags[key]
            });
        }
        response.info.tags.sort(function(a, b) {
          return b.num - a.num;
        });
        response.info.tags.splice(6);
        if ('点击编辑' === response.info.desc) response.info.desc = "";
        if (!response.info.honor) response.info.honor = [];
        if (!is_me && !response.info.phone)  response.info.phone = "***";
        if (!is_me && !response.info.qq)  response.info.qq = "***";
        if (response.info.honor) {
          response.info.honor.sort(
            function (a, b) {
              return a[0] - b[0];
            }
          );
        }
        angular.extend(user_info, response.info);
      }
    })
    .error(function(data,status,headers,config) {
      toaster.pop('error', '系统提示', '请求过程错误', false);
    });
  };

  self.changeValue = function (name, old_val, new_val) {
    var deferred = $q.defer();
    data = {};
    data[name] = new_val;
    if (old_val === new_val){
      deferred.resolve();
    } else {
       var req = {
        url: '/user/info',
        method: 'POST',
        data: $.param(data),
        xsrfCookieName: '_xsrf',
        xsrfHeaderName: 'X-CSRFToken',
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
      };

      $http(req).success(function(response) {
        if (response.err) {
          toaster.pop('error', '系统提示', response.info, true);
          deferred.reject();
        }else{
          user_info[name] = new_val;
          toaster.pop('success', '系统提示', '修改成功!', true);
          deferred.resolve();
        }
      })
      .error(function(data, status, headers, config) {
        toaster.pop('error', '系统提示', '请求过程错误', true);
        deferred.reject();
      });
    }
    return deferred.promise;
  };

  self.changeMultiValues = function (values) {
    var deferred = $q.defer();
    var req = {
      url: '/user/info',
      method: 'POST',
      data: $.param(values),
      xsrfCookieName: '_xsrf',
      xsrfHeaderName: 'X-CSRFToken',
      headers: {
          "Content-Type": "application/x-www-form-urlencoded"
      }
    };

    $http(req).success(function(response) {
      if (response.err) {
        toaster.pop('error', '系统提示', response.info, true);
        deferred.reject();
      }else{
        for (var key in values) {
          if (typeof(values[key]) !== "function") user_info[key] = values[key];
        }
        toaster.pop('success', '系统提示', '修改成功!', true);
        deferred.resolve();
      }
    })
    .error(function(data, status, headers, config) {
      toaster.pop('error', '系统提示', '请求过程错误', false);
      deferred.reject();
    });
    return deferred.promise;
  };

  self.updateHonor = function () {
    var deferred = $q.defer();
    var req = {
      url: '/user/info',
      method: 'POST',
      data: $.param({"honor": JSON.stringify(user_info.honor)}),
      xsrfCookieName: '_xsrf',
      xsrfHeaderName: 'X-CSRFToken',
      headers: {
          "Content-Type": "application/x-www-form-urlencoded"
      }
    };

    $http(req).success(function(response) {
      if (response.err) {
        toaster.pop('error', '系统提示', response.info, true);
        deferred.reject();
      }else{
        toaster.pop('success', '系统提示', '修改成功!', true);
        deferred.resolve();
      }
    })
    .error(function(data, status, headers, config) {
      toaster.pop('error', '系统提示', '请求过程错误', false);
      deferred.reject();
    });
    return deferred.promise;
  };

  self.getAuth = function() {
    var req = {
        url: '/user/star/auth',
        method: 'GET'
    };
    return $http(req);
  };

  self.auth = function(university, college, entrance_year, degree, university_mail, class2) { 
    var data = {
      university: university,
      college: college,
      entrance_year: entrance_year,
      degree: degree,
      university_mail: university_mail,
      class2: class2
    };
    var req = {
      url: '/user/star/auth',
      method: 'POST',
      data: $.param(data),
      xsrfCookieName: '_xsrf',
      xsrfHeaderName: 'X-CSRFToken',
      headers: {
          "Content-Type": "application/x-www-form-urlencoded"
      }
    };

    $http(req).success(function(response) {
      if (response.err) {
        var info = "";
        switch(response.err) {
          case 4:
            info = "用户邮箱出错";
            break;
          case 5:
            info = "点赞不足66个";
            break;
          case 6:
            info = "该类帖子数不足10个";
            break;
          default:
            info = response.info;
        }
        toaster.pop('error', '系统提示', info, true);
      }else{
        toaster.pop('success', '系统提示', '恭喜您通过校园星空初步认证，请到认证邮箱激活认证链接！', true);
      }
    })
    .error(function(data, status, headers, config) {
      toaster.pop('error', '系统提示', '请求过程错误', false);
    });
  };

  self.getUserInfo = function () {
    return user_info;
  };
}]);

app.service('questionsSrv', ['$http', '$q', 'toaster', 'userSrv', 'bottomLoading', '$rootScope', 'interactiveService',
  function ($http, $q, toaster, userSrv, bottomLoading, $rootScope, interactiveService) {
  var self = this;
  var questions_info = { question_list: [],
                                       total_page: -1,
                                       current_page: 0
                                     };
  var answered_info = { question_list: [],
                                        total_page: -1,
                                        current_page: 0
                                      };
  var collected_info = { question_list: [],
                                      total_page: -1,
                                      current_page: 0
                                    };
  var my_user = localStorage.username;
  self.fetchList = function (url, info) {
    var total_page = info.total_page;
    var current_page = info.current_page;
    if (0 !== total_page && current_page === total_page) return;
    
    var user_info = userSrv.getUserInfo();
    var user = user_info.user;
    bottomLoading.show();
    $http({
      url: url,
      method: 'GET',
      params: {user: user, page: current_page + 1}
    })
    .success(function(response){
      if(response.err == 0){
        bottomLoading.hide();
        info.total_page = response.total_page;
        info.current_page += 1;
        //response.question_list = test;

        interactiveService.normalizeQuestionList(response.question_list);
        angular.forEach(response.question_list, function(v, i) {
        if (v.best_answer)
          interactiveService.normalizeAnswerList([v.best_answer]);
          var is_me = my_user == v.publisher;
          v.is_me = is_me;
          if (!is_me) {
            if (v.thumb_up_users)
              v.has_thumb_up = my_user in v.thumb_up_users;
            if (v.followers)
              v.has_collect = my_user in v.followers;
          }
          if (v.tags_with_class && v.tags_with_class.length) {
            var class2 = "";
            var tags = [];
            var _info = v.tags_with_class[0].split(':', 2);
            class2 = _info[0];
            tags.push(_info[1]);
            for (var i = 1; i != v.tags_with_class.length; i += 1)
              tags.push(v.tags_with_class[i].split(':', 2)[1]);
            v.class2 = class2;
            v.tags = tags;
          }
          if (url == '/user/question/answered') {
            var w = {
              best_answer: v,
              comment_num: v.comment_num,
              comment_list: v.comment_list,
              reply_num: 1,
              title: v.title,
              tags: v.tags,
              class2: v.class2,
              id: v.question_id
            };
            if (user_info.is_me && v.need_anonymous) {
              w.best_answer.need_anonymous = 0;
              w.best_answer.publisher_img = user_info.icon;
              w.best_answer.publisher_nick = user_info.nick_name;
            }
            info.question_list.push(w);
          } else if (url == '/user/question/posted') {
            v.reply_num = 0;
            info.question_list.push(v);
          } else {
            info.question_list.push(v);
          }
        });
      }else{
        toaster.pop('error', "系统提示", response.info, true);
      }
    }).error(function(err){
      console.log("fetchList function's err is " + err);
      bottomLoading.hide();
    })
  };

  self.fetchQuestionList = function() {
    self.fetchList('/user/question/posted', questions_info);
  };

  self.fetchAnsweredList = function() {
    self.fetchList('/user/question/answered', answered_info);
  };

  self.fetchCollectedList = function() {
    self.fetchList('/user/question/collected', collected_info);
  };

  self.thanks = function (exp_id, fb) {
      var req = {
          url: '/question/thanks',
          method: 'GET',
          params: {
              id: exp_id,
              how_much: fb ? fb : 1
          }
      };
      $http(req).success(function (data, status, headers, config) {
        if (data.err)
          toaster.pop('success', '系统提示', '奖励成功!', true);
        else
          toaster.pop('error', "系统提示", data.info, true);
      }).error(function (data, status, headers, config) {
        console.log("thanks function's err is " + err);
      });
  };

  self.thumbUp = function (exp_id) {
      var req = {
          url: '/question/thumb_up',
          method: 'GET',
          params: {
              id: exp_id
          }
      };
      $http(req).success(function (data, status, headers, config) {
        console.log(data);
         if (!data.err) {
          for (var i = 0; i != questions_info.question_list.length; i++) {
            var q = questions_info.question_list[i];
            if (q.id == exp_id) {
              q.thumb_up_users.push(my_user);
              q.has_thumb_up = true;
              q.thumb_up_num += 1;
              break;
            }
          }
          toaster.pop('success', '系统提示', '点赞成功!', true);
         } else
          toaster.pop('error', "系统提示", data.info, true);
      }).error(function (data, status, headers, config) {
        toaster.pop('error', "系统提示", "系统或网络问题，请稍后重试！", true);
      });
  };

  self.getQuestionsInfo = function () {
    return questions_info;
  };

  self.getAnsweredInfo = function () {
    return answered_info;
  };

  self.getCollectedInfo = function () {
    return collected_info;
  };
}]);

app.controller('UserPageController', ['$scope', '$http', 'userSrv', 'questionsSrv', 'ThankSrv', 'share', 'interactiveService',
    function ($scope, $http, userSrv, questionsSrv, ThankSrv, share, interactiveService) {
    init();

    function init() {
      var user = GetQueryString('user');
      user = Base64.decode(user);
      userSrv.setUser(user);
      questionsSrv.fetchQuestionList();
      $scope.isMyAnswer = false;
      $scope.isMyQuestion = true;
      $scope.panel_num = 0;
      $scope.user_info = userSrv.getUserInfo();
      $scope.questions_info = questionsSrv.getQuestionsInfo();
      $scope.answered_info = null;
      $scope.collected_info = null;
      $scope.info = $scope.questions_info;
      $scope.classes = ['留学', '考证', '就业', '实习', '校园', '考研'];
      $scope.degrees = ['本科', '硕士', '博士'];
      // TODO: add login dynamically check
      $scope.isLogined = !!localStorage.username;
      var current_year = new Date().getFullYear();
      $scope.entrance_year_list = [];
      for (var i = current_year; i >= current_year - 10; i--)
        $scope.entrance_year_list.push(i);
    };

    $scope.fetch = function() {
      switch($scope.panel_num) {
        case 0:
          $scope.fetchQuestionList();
          break;
        case 1:
          $scope.fetchAnsweredList();
          break;
        default:
          $scope.fetchCollectedList();
      }
    };

    $scope.changePanel = function(new_panel_num) {
      if (new_panel_num != $scope.panel_num) {
        $scope.panel_num = new_panel_num;
        if (new_panel_num == 1) {
          if (!$scope.answered_info) {
            $scope.answered_info = questionsSrv.getAnsweredInfo();
            questionsSrv.fetchAnsweredList();
          }
          $scope.isMyAnswer = true;
          $scope.isMyQuestion = false;
          $scope.info = $scope.answered_info;
        } else if (new_panel_num == 2) {
          if (!$scope.collected_info) {
            $scope.collected_info = questionsSrv.getCollectedInfo();
            questionsSrv.fetchCollectedList();
          }
          $scope.isMyAnswer = false;
          $scope.isMyQuestion = false;
          $scope.info = $scope.collected_info;
        } else {
          $scope.isMyAnswer = false;
          $scope.isMyQuestion = true;
          $scope.info = $scope.questions_info;
        }
      }
    };

    $scope.showCertModal = function() {
      $scope.cert_title = "如何获得校园勋章";
      userSrv.getAuth().success(function(data, status, headers, config) {
        if(!data.err) {
          $scope.university = data.university;
          $scope.college = data.college;
          $scope.degree = data.degree;
          $scope.entrance_year = data.entrance_year;
          $scope.university_mail = data.university_mail;
        }
        if (!$scope.university) $scope.university = localStorage.university;
        if (!$scope.college) $scope.college = localStorage.college;
        $('#certModal').modal('show');
      });
    };

    $scope.changeState = function() {
      if ($scope.user_info.state === $scope.new_state && $scope.user_info.state_desc === $scope.new_state_desc)
        $scope.state_editing = false;
      else {
        var promise = userSrv.changeMultiValues({'state': $scope.new_state, 'state_desc': $scope.new_state_desc});
        promise.then(function(data) {
            $scope.state_editing = false;
        }, function(data) {});
      }
    };

    $scope.followUser = interactiveService.followUser;
    $scope.unfollowUser = interactiveService.unfollowUser;
    $scope.fetchQuestionList = questionsSrv.fetchQuestionList;
    $scope.fetchAnsweredList = questionsSrv.fetchAnsweredList;
    $scope.fetchCollectedList = questionsSrv.fetchCollectedList;

    $scope.auth = function() {
      var class2 = $scope.class2.slice(0, 2);
      userSrv.auth($scope.university, $scope.college, $scope.entrance_year,
        $scope.degree, $scope.university_mail, $scope.class2);
    };

    $scope.fileChanged = function(e) {
        var files = e.target.files;
        var fileReader = new FileReader();
        fileReader.readAsDataURL(files[0]);
        fileReader.onload = function(e) {
            $scope.imgSrc = this.result;
            $scope.$apply();
        };
    };

    $scope.clear = function() {
         $scope.imageCropStep = 1;
         delete $scope.imgSrc;
         delete $scope.result;
         delete $scope.resultBlob;
    };

    $scope.showAvatarModal = function() {
      if ($scope.user_info.is_me)
        $('#uploadAvatar').modal('show');
    };

    $scope.uploadAvatar = function () {
        $http({
            url: '/fetch_token?img=1',
            method: 'GET'
          })
          .success(function(response) {
            if (response.uptoken) {
              var req = {
                method: 'POST',
                url: "http://up.qiniu.com/putb64/-1",
                timeout: 10000,
                data: $scope.result.split(',', 2)[1],
                headers: {
                    "Content-Type": "application/octet-stream",
                    "Authorization": "UpToken " + response.uptoken
                }
              };

              $http(req).success(function(data, status, headers, config) {
                //回调成功
                var new_icon = "http://7xjkhy.dl1.z0.glb.clouddn.com/" + data.hash;
                var promise = userSrv.changeValue('icon', $scope.user_info.icon, new_icon);
                promise.then(function(data) {
                  $scope.user_info.icon = new_icon;
                  $('#uploadAvatar').modal('hide');
                }, function(data) {});

              }).error(function(data, status, headers, config) {
                //回调失败
                alert('页面加载失败，请重试！');
              });
            }
          })
          .error(function(data, status, headers, config) {
            // 失败处理
            alert('页面加载失败，请重试！');
          });
    };
}]);

app.directive('editableSpan', ['userSrv', function(userSrv) {
  var template = '<div style="display:inline-block;" ng-hide="editing || !item" ng-mouseenter="edit = true" \
            ng-mouseleave="edit = false" ng-class="{editable: is_me}">{{ item }} \
            <i ng-show="is_me && edit" ng-click="editing=true; new_item=item" class="fa fa-pencil-square-o show-hide"></i> \
          </div> \
          <span class="empty" ng-click="editing=is_me?true:false;" ng-show="!editing && !item && (is_me || !is_open)">{{ emptyTitle }}</span> \
          <div ng-show="editing"> \
            <input ng-model="new_item" placeholder="{{ placeholder }}"></input><button type="button" ng-click="change()">确定</button> \
          </div>';
  return {
    scope: {
      emptyTitle: "@",
      item: "=",
      is_me: "=isMe",
      is_open: "=isOpen",
      name: "@"
    },
    restrict: 'E',
    template: template,
    link: function(scope, elem, attrs) {
      scope.placeholder = attrs['placeholder'];
      scope.change = function() {
        var promise = userSrv.changeValue(scope.name, scope.item, scope.new_item);
        promise.then(function(data) {
            scope.editing = false;
        }, function(data) {});
      };
    }
  };
}]);

app.directive('honorPane', ['userSrv', function(userSrv) {
  var template = '<span class="empty" ng-click="adding=true" ng-show="!adding && (!ngModel || 0===ngModel.length) && is_me">填写获奖经历</span> \
  <span ng-show="(!ngModel || 0===ngModel.length) && !is_me">用户未填获奖经历</span> \
  <div ng-show="adding"> \
    <div class="new-form-group row"> \
      <label class="col-md-3 control-label">年份</label> \
      <div class="col-md-9"> \
        <select ng-model="new_time" ng-options="i for i in yearList"> \
          <option value=""></option> \
        </select> \
      </div> \
    </div> \
    <div class="new-form-group row"> \
      <label class="col-md-3 control-label">级别</label> \
      <div class="col-md-9"> \
        <select ng-model="new_level" ng-options="i for i in levels"> \
          <option value=""></option> \
        </select> \
      </div> \
    </div> \
    <div class="new-form-group row"> \
      <label class="col-md-3 control-label">名称</label> \
      <div class="col-md-9"> \
      <input ng-model="new_honor"> \
      </div> \
    </div> \
    <div class="form-group row"> \
      <div class="col-md-9 col-md-offset-3"> \
      <button type="button" ng-click="ok()" class="btn btn-primary">确定</button> \
      <button type="button" ng-click="adding=false" class="btn btn-default">取消</button> \
      </div> \
    </div> \
  </div> \
  <honor-item ng-model="h" ng-repeat="h in ngModel" is-me="is_me" year-list="yearList"></honor-item>';
  return {
    scope: {
      ngModel: "=",
      is_me: "=isMe",
      yearList: "="
    },
    restrict: 'E',
    template: template,
    controller: ['$scope', function($scope) {
      this.addHonor = function() {
        $scope.adding = true;
      };
    }],
    link: function(scope, elem, attrs) {
      scope.levels = ['院级', '校级', '市级', '省级', '全国', '国际', '企业'];
      scope.ok = function() {
        if (scope.new_time && scope.new_level && scope.new_honor) {
          scope.ngModel.push([scope.new_time, scope.new_level, scope.new_honor]);
          var promise = userSrv.updateHonor();
          promise.then(function(data) {
            scope.adding = false;
          }, function(data) {});
        }
      };
    }
  };
}]);

app.directive('honorItem', ['userSrv', function(userSrv) {
  var template = '<div class="row" ng-mouseenter="edit = true" ng-mouseleave="edit = false"> \
                <div class="col-md-3" ng-hide="editing"style="padding-right: 0;"">{{ ngModel[0] }}年</div> \
                <div class="col-md-2" ng-hide="editing" style="padding-right: 0; padding-left: 0;">{{ ngModel[1] }}</div> \
                <div class="col-md-5"ng-hide="editing" style="padding-right: 0;  padding-left: 0;">{{ ngModel[2] }}</div> \
                <div class="col-md-2" ng-hide="editing" style="padding-right: 0; padding-left: 0;"> \
                  <i ng-show="is_me && edit" ng-click="editing=true; time=ngModel[0]; level=ngModel[1]; honor=ngModel[2]" class="fa fa-pencil-square-o show-hide"></i> \
                  <i ng-show="is_me && edit" ng-click="add()" class="fa fa-plus"></i> \
                </div> \
                \
                <div ng-show="editing" class="col-md-12"> \
                  <div class="new-form-group row"> \
                    <label class="col-md-3 control-label">年份</label> \
                    <div class="col-md-9"> \
                      <select ng-model="time" ng-options="i for i in yearList"> \
                        <option value=""></option> \
                      </select> \
                    </div> \
                  </div> \
                  <div class="new-form-group row"> \
                    <label class="col-md-3 control-label">级别</label> \
                    <div class="col-md-9"> \
                      <select ng-model="level" ng-options="i for i in levels"> \
                        <option value=""></option> \
                      </select> \
                    </div> \
                  </div> \
                  <div class="new-form-group row"> \
                    <label class="col-md-3 control-label">名称</label> \
                    <div class="col-md-9"> \
                    <input ng-model="honor"> \
                    </div> \
                  </div> \
                  <div class="form-group row"> \
                    <div class="col-md-9 col-md-offset-3"> \
                    <button type="button" ng-click="ok()" class="btn btn-primary">确定</button> \
                    <button type="button" ng-click="editing=false" class="btn btn-default">取消</button> \
                    </div> \
                  </div> \
                </div>';
  return {
    scope: {
      ngModel: "=",
      is_me: "=isMe",
      yearList: "="
    },
    require: '^honorPane',
    // replace: true,
    restrict: 'E',
    template: template,
    link: function(scope, elem, attrs, paneCtrl) {
      scope.levels = ['院级', '校级', '市级', '省级', '全国', '国际', '企业'];
      scope.add = function() {
        paneCtrl.addHonor();
      };
      scope.ok = function() {
        if (scope.ngModel[0] != scope.time || scope.ngModel[1] != scope.level || scope.ngModel[2] != scope.honor) {
          scope.ngModel[0] = scope.time;
          scope.ngModel[1] = scope.level;
          scope.ngModel[2] = scope.honor;
          var promise = userSrv.updateHonor();
          promise.then(function(data) {
            scope.editing = false;
          }, function(data) {});
        } else
          scope.editing = false;
      };
    }
  };
}]);

app.filter('tag_extract', function() {
  var filter = function(tag) {
    return tag.split(':', 2)[1];
  };
  return filter;
});

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

//angular 输出富文本
app.filter('trustHtml', function($sce) {
  return function(text) {
    return $sce.trustAsHtml(text);
  };
});
