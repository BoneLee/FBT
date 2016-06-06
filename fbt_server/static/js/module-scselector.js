/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('selector', [])
.service('selector', function($rootScope, $timeout) {
  return {
    show: function(title, groups, groupWidth, entityWidth, entityCallback, universityEntityCallback, submitCallback) {
      $timeout(function() {
        $rootScope.$broadcast('selector-show', {
          title: title,
          groups: groups,
          groupWidth: groupWidth,
          entityWidth: entityWidth,
          entityCallback: entityCallback,
          universityEntityCallback: universityEntityCallback,
          submitCallback: submitCallback
        });
      });
    },
    hide: function() {
      $timeout(function() {
        $rootScope.$broadcast('selector-hide');
      });
    }
  };
})
.directive('selectorContainer', ['selector', function(selector) {
  var template = '<div id="selector-container" class="modal fade">\
    <div class="modal-dialog">\
      <div class="modal-content">\
        <div class="modal-header">\
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>\
          <div class="modal-title"><h2>{{ title }}</h2>&nbsp;&nbsp;<span ng-show="currentEntity">当前选择：{{ currentEntity }} {{ currentCollegeEntity }}</span></div>\
        </div>\
        <div class="modal-body">\
          <div class="groups">\
            <span ng-class="{\'choosed\': currentGroup == i}" ng-style="{\'width\': groupWidth}" ng-repeat="i in groups" ng-click="chooseGroup(i)" title="{{i}}">{{ i }}</span>\
          </div>\
        </div>\
        <div class="modal-footer" ng-show="entities">\
          <div class="form-group">\
            <input type="text" ng-model="entity" placeholder="快速名称过滤"/>\
          </div>\
          <div class="entities">\
            <span ng-class="{\'choosed\': currentEntity == i}" ng-style="{\'width\': entityWidth}" ng-repeat="i in entities | filter: entity" ng-click="chooseEntity(i)" title="{{i}}">{{ i }}</span>\
          </div>\
        </div>\
        <div class="modal-footer" ng-show="college_entities">\
          <div class="form-group">\
            <input type="text" ng-model="college_entity" placeholder="快速名称过滤"/>\
          </div>\
          <div class="entities">\
            <span ng-class="{\'choosed\': currentCollegeEntity == i}" ng-style="{\'width\': entityWidth}" ng-repeat="i in college_entities | filter: college_entity" ng-click="chooseCollegeEntity(i)" title="{{i}}">{{ i }}</span>\
          </div>\
        </div>\
        <div class="modal-footer">\
          <button class="btn default" data-dismiss="modal">取消</button>\
          <button ng-class="{disabled: !(currentGroup && currentEntity && currentCollegeEntity)}" class="btn btn-success" ng-click="submitHandler(currentEntity, currentCollegeEntity)">确定</button>\
        </div>\
      </div>\
    </div>\
  </div>';
  return {
    scope: {},
    restrict: 'E',
    replace: true,
    template: template,
    link: function(scope, elem, attrs) {
      scope.currentGroup = null;
      scope.currentEntity = null;

      scope.$on('selector-show', function(event, d) {
        scope.title = d.title;
        scope.groupWidth = d.groupWidth ? d.groupWidth : '80px';
        scope.groups = d.groups;
        scope.entityWidth = d.entityWidth ? d.entityWidth : '80px';

        scope.chooseGroup = function(group) {
          scope.currentGroup = group;
          if(d.entityCallback && typeof(d.entityCallback) == 'function') {
            d.entityCallback(group, function(entities) {
              scope.entities = entities;
              scope.college_entities = null;
            });
          }
        };

        scope.chooseEntity = function(university) {
          scope.currentEntity = university;
          if(d.universityEntityCallback && typeof(d.universityEntityCallback) == 'function') {
            d.universityEntityCallback(university, function(entities) {
              scope.college_entities = entities;
            });
          }
        };

        scope.chooseCollegeEntity = function(college_entity) {
          scope.currentCollegeEntity = college_entity;
        };
        
        scope.submitHandler = function(entity, college_entity) {
          if(d.submitCallback && typeof(d.submitCallback) == 'function') {
            d.submitCallback(entity, college_entity);
            $('#selector-container').modal('hide');
          }
        };

        $('#selector-container').modal({backdrop: false, keyboard: false});
      });
      scope.$on('selector-hide', function() {
      });
    }
  };
}]);
