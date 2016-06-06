app.controller('experienceEditController', ['$scope', 'rte', '$http', 'toaster', 'tagSrv',

  function($scope, rte, $http, toaster, tagSrv) {

    $scope.init = function() {

      $scope.classes = {
        '留学': '留学',
        '考证': '考证',
        '就业': '就业',
        '实习': '实习',
        '校园': '校园'
      };
      $scope.formdata = {
        title: '',
        class2: '选择分类',
        tags: tagSrv.draftTags,
        content: '',
      };

    };

    $scope.selectClass = function(argClass) {
      $scope.formdata.class2 = argClass;
    };

    $scope.removeTag = function(index) {
        tagSrv.draftTags.splice(index,1);

      //var tags = $scope.formdata.tags;
      //var length = tags.length;
      //for (var i = 0; i < length; i++) {
      //  if (tags[i] === tag) {
      //    tags.splice(i, 1);
      //  }
      //}

    };

    $scope.cancel = function() {

    };

    $scope.getContent = rte.getContent;

    $scope.__deploy = function() {


      var experience = $scope.formdata;
      var req = {

        url: '/experience/post',
        method: 'POST',
        data: experience,
        headers: {
          "X-CSRFToken": getCookie("_xsrf")
        }

      };

      $http(req).success(function(data, status, headers, config) {
          var data = angular.fromJson(data);
          switch (data.err) {
            case 0:
              alert('发布成功');
              break;
            case 1:
              alert('没有登录');
              break;
            case 3:
              alert('标题太长');
              break;
            case 4:
              alert('内容太长');
              break;
            case 5:
              alert('分类错误');
              break;
            case 6:
              alert('tag错误');
              break;
          }

        })
        .error(function(data, status, headers, config) {

          if (status == 500) {
            //500服务器内部错误
            alert('服务器内部错误');

          } else if (status == 408) {
            //请求超时
            alert('请求超时');

          }
        });

    };
    $scope.deploy = function() {
      var content = $scope.getContent();
      var length = 50;
      if (length < 50) {
        alert('不能少于50字');
      } else {
        $scope.formdata.content = content;
        $scope.__deploy();
      }

      alert($scope.getContent());

    };





  }
]);
