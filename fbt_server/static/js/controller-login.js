/**
 * Created by SG on 2015/5/18.
 */

app.controller('LoginController', ['$rootScope', '$scope', '$http', '$window', 'User', '$route', '$interval', 'toaster', 'universityCollegeSrv',
    function ($rootScope, $scope, $http, $window, User, $route, $interval, toaster, universityCollegeSrv) {
        //跳转到主页注册页面
        $scope.goToHome = function(){
            $window.location.href = '#/home';
            $('#login-modal').modal('hide');
        }
        //显示邀请奖励
        $scope.showMessage = false;
        $scope.rewardMessage = function () {
            $scope.showMessage = !$scope.showMessage;
            return $scope.showMessage;
        };
        // 邀请奖励--end

        $scope.keyupHandler = function (event) {
            if (event.keyCode == 13) {
                $scope.loginHandler();
            }
        };

        $scope.switch2View = function (viewId) {
            $scope.switchView = viewId;
            $scope.errtip = "";
        };

        $scope.loginHandler = function () {
            $scope.errtip = "";
            if ($scope.savepwd) {
                localStorage.email = $scope.username;
                localStorage.pwd = $.md5($scope.password);
            } else {
                localStorage.email = "";
                localStorage.pwd = "";
            }

            User.loginRequest($scope.username, $.md5($scope.password), function (data) {
                if ('err' in data && data['err'] == 0) {
                    $('#login-modal').modal('hide');
                    User.loginsuccess();
                } else {
                    if ('info' in data) {
                        $scope.errtip = '*' + data['info'];
                    } else {
                        $scope.errtip = '登录出现错误，请稍后重试';
                    }
                }
            }, function () {
                $scope.errtip = '服务器抛锚了，请稍后重试';
            });
        };

        $scope.logoutHandler = function () {
            $scope.logouterr = "";
            var logoutReq = {
                url: '/logout',
                method: 'GET',
                xsrfCookieName: '_xsrf',
                xsrfHeaderName: 'X-CSRFToken'
            };
            $http(logoutReq).success(function (data) {
                $scope.logouterr = '';
                if ('OK' in data && data['OK'] == 0) {
                    $rootScope.is_logined = false;
                    $rootScope.userdisplay = "";
                    $rootScope.userIcon = "";
                    $rootScope.college = "";
                    $rootScope.university = "";
                    $rootScope.total_coins = "";
                    $rootScope.study_coins = "";
                    $rootScope.username = "";

                    //TODO 以后封装在一个字段里边吧，这样太不方便
                    localStorage.removeItem('allow_login');//清理这一个应该就够了吧，其他登录后再重新赋值
                    localStorage.removeItem('username');
                    localStorage.removeItem('uid');
                    //localStorage.clear();
                    






                    User.clearUserInfo();
                    $('#logout-modal').modal('hide');
                    //Askbot.askbotLogout();
                    $window.location.href = "/";
                } else {
                    $scope.logouterr = '注销出现错误，请稍后重试';
                }
            }).error(function () {
                $scope.logouterr = '服务器抛锚了，请稍后重试';
            });
        };

        $scope.resetPwdHandler = function () {
            $scope.errtip = "";
            var data = {"user": $scope.username};
            var req = {
                url: '/reset_password',
                method: 'GET',
                params: data
            };

            $http(req).success(function (data) {
                if ('type' in data && data['type'] == 0) {
                    //$scope.errtip = '重置密码错误，请稍后重试';
                    toaster.pop('warning', "系统提示", "重置密码错误，请稍后重试", true);
                } else {
                    toaster.pop('success', "系统提示", "重置密码的链接已经发到您的邮箱。", false);
                    //$scope.errtip = '重置密码的链接已经发到您的邮箱。';
                    //$('#login-modal').modal('hide');
                }
            }).error(function () {
                //$scope.errtip = '*服务器抛锚了，请稍后重试';
                toaster.pop('warning', "系统提示", "服务器抛锚了，请稍后重试", true);
            });
        };

        $scope.register_info = "";

        $scope.registerSubmit = function (argument) {
            $scope.register_info = "";
            function htmlencode(s) {
                var div = document.createElement('div');
                div.appendChild(document.createTextNode(s));
                return div.innerHTML;
            }

           // var school = $scope.university;
           // var college = $scope.college;
            /*
            var askbotSignupData = {
                username: htmlencode($scope.nick),
                email: $scope.username,
                password1: $.md5($scope.passwd),
                password2: $.md5($scope.passwd)
            };
            */

            var data = {
                user: $scope.username,
                nick: htmlencode($scope.nick),
               // gender: $scope.gender,
                passwd: $.md5($scope.passwd),
              //  school: htmlencode(school),
              //  college: htmlencode(college),
              // name: htmlencode($scope.real_name),
                captcha: $scope.captcha,
                referee: htmlencode($scope.referee)
            };

            $http({
                url: '/register',
                method: 'POST',
                xsrfCookieName: '_xsrf',
                xsrfHeaderName: 'X-CSRFToken',
                data: $.param(data),
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            })
                .success(function (response) {
                    if (0 == response.err) {
                        //Askbot.askbotSignup(askbotSignupData);
                        //$scope.register_info = "注册成功，请登录！资源下载时某些浏览器可能会阻止下载弹窗，请在地址栏右侧进行设置。";
                        toaster.pop('success', "系统提示", "注册成功，请登录！资源下载时某些浏览器可能会阻止下载弹窗，请在地址栏右侧进行设置。", true);
                        $scope.switchView = 1;
                    } else {
                        $scope.register_info = response.info;
                    }
                });
        };

        $scope.isCurrentOrder = function (order) {
            return order == $scope.show_order;
        };

        $scope.universityClickHandler = function () {
            $scope.show_order = 1;
        };

        $scope.chooseProvince = function (province) {
            universityCollegeSrv.fetchUniversities(province);
            $scope.show_order = 2;
        };

        $scope.chooseUniversity = function (university) {
            $scope.university = university;
            $scope.college = "";
            universityCollegeSrv.fetchColleges(university);
            $scope.show_order = 3;
        };

        $scope.chooseCollege = function (college) {
            $scope.college = college;
            $scope.show_order = 0;
        };

        $scope.collegeClickHandler = function () {
            var currentUniversity = $scope.university;
            if (currentUniversity) {
                universityCollegeSrv.fetchColleges(currentUniversity);
                $scope.show_order = 3;
            }
        };

        $scope.captchaChange = function () {
            $scope.captchaSrc = '/captcha?a=' + Math.random();
        };

        function init(argument) {
            $scope.show_order = 0; // 0 for no selector, 1 for province, 2 for university, 3 for college
            $scope.prov_list = universityCollegeSrv.getProvList();
            $scope.universities = universityCollegeSrv.getUniversities();
            $scope.colleges = universityCollegeSrv.getColleges();
            $scope.captchaSrc = '/captcha';
            $scope.btnText = '获取';
            // $scope.btnDisabled = myForm.captcha.$invalid;
        };

        init();
    }]);

app.controller('changePasswordModalCtrl', ['$scope', '$modalInstance', '$http', '$filter', 'toaster', function ($scope, $modalInstance, $http, $filter, toaster) {
    $scope.errtip = "";
    $scope.captchaSrc = '/captcha';

  $scope.captchaChange = function () {
      $scope.captchaSrc = '/captcha?a=' + Math.random();
  };

    $scope.close = function () {
        $modalInstance.dismiss('cancel');
    };
    $scope.savePwd = function (originPwd, newPwd, confirmPwd) {
        if (newPwd != confirmPwd) {
            $scope.errtip = '*两次密码不相同';
        }
        else {
            $scope.errtip = "";
            var mod_user = {};
            mod_user["passwd"] = $.md5(originPwd);
            mod_user["new_passwd"] = $.md5(newPwd);
            mod_user["captcha"] = $scope.captcha;

            var req = {
                url: '/change_password',
                method: 'GET',
                params: mod_user
            };
            $http(req).success(function (data) {
                if ('err' in data && data['err'] == 0) {
                    localStorage.pwd = mod_user["new_passwd"];
                    $modalInstance.close();
                    toaster.pop('success', "系统提示", "密码修改成功！", false);
                } else {
                    if ('info' in data) {
                        $scope.errtip = '*' + data['info'];
                    } else {
                        $scope.errtip = '*登录出现错误，请稍后重试';
                    }
                }
            }).error(function () {
                $scope.errtip = '*服务器抛锚了，请稍后重试';
            });
        }
    };
}]);

app.controller('changeUniversityCollegeModalCtrl', ['$rootScope', '$scope', '$modalInstance', '$http', 'universityCollegeSrv',
    'toaster', function ($rootScope, $scope, $modalInstance, $http, universityCollegeSrv, toaster) {
        $scope.formdata = {  'university': "",
            'college': "",
            'gender':  "",
            'name': ""};
        $scope.close = function () {
            $modalInstance.dismiss('cancel');
        };

        $scope.isCurrentOrder = function (order) {
            return order == $scope.show_order;
        };

        $scope.universityClickHandler = function () {
            $scope.show_order = 1;
        };

        $scope.chooseProvince = function (province) {
            universityCollegeSrv.fetchUniversities(province);
            $scope.show_order = 2;
        };

        $scope.chooseUniversity = function (university) {
            $scope.formdata.university = university;
            $scope.formdata.college = "";
            universityCollegeSrv.fetchColleges(university);
            $scope.show_order = 3;
        };

        $scope.chooseCollege = function (college) {
            $scope.formdata.college = college;
            $scope.show_order = 0;
        };

        $scope.collegeClickHandler = function () {
            var currentUniversity = $scope.formdata.university;
            if (currentUniversity) {
                universityCollegeSrv.fetchColleges(currentUniversity);
                $scope.show_order = 3;
            }
        };

        $scope.unmodified = function() {
            return $scope.formdata.university === $scope.user_info.university && $scope.formdata.college === $scope.user_info.college &&
                $scope.formdata.gender == $scope.user_info.gender && $scope.formdata.name == $scope.user_info.real_name;
        };

        $scope.saveChange = function () {
            $scope.errtip = "";
            var req = {
                url: '/user/info/change',
                method: 'POST',
                xsrfCookieName: '_xsrf',
                xsrfHeaderName: 'X-CSRFToken',
                data: $.param($scope.formdata),
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            };
            $http(req).success(function (data) {
                if ('err' in data && data['err'] === 0) {
                    $modalInstance.close();
                    toaster.pop('success', "系统提示", "个人信息修改成功！", false);
                } else {
                    if ('info' in data) {
                        $scope.errtip = '*' + data['info'];
                    } else {
                        $scope.errtip = '*登录出现错误，请稍后重试';
                    }
                }
            }).error(function () {
                $scope.errtip = '*服务器抛锚了，请稍后重试';
            });
        };
        //从服务器获取用户信息
        $scope.user_info = {};
        var req = {
            url: '/user/info/change',
            method: 'GET',
            params: $scope.formdata
        };
        $http(req).success(function (data) {
            if ('err' in data && data['err'] === 0) {
                $scope.user_info = data.user_info;
                init();
            } else {
                if ('info' in data) {
                    $scope.errtip = '*' + data['info'];
                } else {
                    $scope.errtip = '*登录出现错误，请稍后重试';
                }
            }
        }).error(function (err) {
            $scope.errtip = '*服务器抛锚了，请稍后重试';
        });
        function init() {
            $scope.errtip = "";
            $scope.show_order = 0; // 0 for no selector, 1 for province, 2 for university, 3 for college
            $scope.prov_list = universityCollegeSrv.getProvList();
            $scope.universities = universityCollegeSrv.getUniversities();
            $scope.colleges = universityCollegeSrv.getColleges();
            //判断返回值是否是“undefined”，如果是则定义变量为空
            if($scope.user_info.university == "undefined" || $scope.user_info.university == "null"){
                $scope.formdata.university = "";
            }else {
                $scope.formdata.university = $scope.user_info.university;
            }
            if($scope.user_info.college == "undefined" || $scope.user_info.college == "null")
            {
                $scope.formdata.college = "";
            }else {
                $scope.formdata.college = $scope.user_info.college;
            }
            if($scope.user_info.gender == "undefined" || $scope.user_info.gender == "null")
            {
                $scope.formdata.gender = "";
            }else {
                $scope.formdata.gender = $scope.user_info.gender;
            }
            if($scope.user_info.real_name == "undefined" || $scope.user_info.real_name == "null")
            {
                $scope.formdata.name = "";
            }else{
                $scope.formdata.name =  $scope.user_info.real_name
            }
        };
    }]);
