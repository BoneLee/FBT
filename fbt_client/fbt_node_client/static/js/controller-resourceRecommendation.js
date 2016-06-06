/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceRecommendationController', function($scope, selector) {
  $scope.selectCollegeClickHandler = function() {
    var title = '选择学校';
    var groups = [
      '北京北京北京北京北京北京北京',
      '上海',
      '黑龙江',
      '吉林',
      '辽宁',
      '天津',
      '安徽',
      '江苏',
      '浙江',
      '陕西',
      '湖北',
      '广东',
      '湖南',
      '甘肃',
      '四川',
      '山东',
      '福建',
      '河南',
      '重庆',
      '云南',
      '河北',
      '江西',
      '山西',
      '贵州',
      '广西',
      '内蒙古',
      '宁夏',
      '青海',
      '新疆',
      '海南',
      '西藏',
      '香港',
      '澳门',
      '台湾',
    ];
    var groupWidth = '72px';
    var entityWidth = '120px';
    var entityCallback = function(group, callback) {
      // fetch from server
      var entities = [
            '哈尔滨工业大学',
            '哈工程东北林大',
            '东北农业大学',
            '哈尔滨医科大学',
            '黑龙江中医药',
            '黑工程',
            '黑龙江科技大学',
            '哈尔滨学院',
            '哈尔滨体院',
            '东方学院',
            '黑龙江大学',
            '哈尔滨商业大学',
      '北京北京北京北京北京北京北京',
      '上海',
      '黑龙江',
      '吉林',
      '辽宁',
      '天津',
      '安徽',
      '江苏',
      '浙江',
      '陕西',
      '湖北',
      '广东',
      '湖南',
      '甘肃',
      '四川',
      '山东',
      '福建',
      '河南',
      '重庆',
      '云南',
      '河北',
      '江西',
      '山西',
      '贵州',
      '广西',
      '内蒙古',
      '宁夏',
      '青海',
      '新疆',
      '海南',
      '西藏',
      '香港',
      '澳门',
      '台湾',
          ];
      callback(entities);
    };
    var submitCallback = function(entity) {
      console.log('submitting entity: ' + entity);
      $scope.$parent.selectedCollege = entity;
    };
    selector.show(title, groups, groupWidth, entityWidth, entityCallback, submitCallback);
  };
});
