/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('selector', [])
.service('selector', function($rootScope, $timeout) {
  return {
    show: function(title, groups, groupWidth, entityWidth, entityCallback, submitCallback) {
      $timeout(function() {
        $rootScope.$broadcast('selector-show', {
          title: title,
          groups: groups,
          groupWidth: groupWidth,
          entityWidth: entityWidth,
          entityCallback: entityCallback,
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
          <div class="modal-title"><h2>{{ title }}</h2>&nbsp;&nbsp;<span ng-show="currentEntity">当前选择：{{ currentEntity }}</span></div>\
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
        <div class="modal-footer">\
          <button class="btn default" data-dismiss="modal">取消</button>\
          <button ng-class="{disabled: !(currentGroup && currentEntity)}" class="btn default primary" ng-click="submitHandler(currentEntity)">确定</button>\
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
            });
          }
        };

        scope.chooseEntity = function(entity) {
          scope.currentEntity = entity;
        };
        
        scope.submitHandler = function(entity) {
          if(d.submitCallback && typeof(d.submitCallback) == 'function') {
            d.submitCallback(entity);
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
