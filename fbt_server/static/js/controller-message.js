/**
 * Created by SG on 2015/7/16.
 */
app.controller('MessageController', ['$http', '$scope', 'toaster', '$rootScope', function($http, $scope, toaster, $rootScope) {
  $scope.messages = [];

  $scope.max_size = 5;
  $scope.items_per_page = 8;
  $scope.current_page = 1;

  $http.get('/user/message/list')
    .success(function (data) {
      if ('err' in data && data['err'] == 0) {
        $scope.message_list = data['message_list'];
        $scope.changePage();
      }
    });

  $scope.delete = function(msg) {
    $http.get('/user/message/delete?msg_id=' + msg.id)
    .success(function (data) {
      if ('err' in data && data['err'] == 0) {
        var idx = $scope.message_list.indexOf(msg);
        $scope.message_list.splice(idx, 1);
        $rootScope.message_count = $scope.message_list.length;
        $scope.changePage();
        console.log('delete message success');
      } else {
        toaster.pop('warning', "系统提示", "消息删除错误，请稍后重试", true);
      }
    }).error(function() {
        toaster.pop('warning', "系统提示", "消息删除错误，请稍后重试", true);
      });
  };

  $scope.changePage = function() {
    var start = $scope.items_per_page * ($scope.current_page - 1);
    var end = start + $scope.items_per_page;
    $scope.messages = $scope.message_list.slice(start, end);
  };
}]);
