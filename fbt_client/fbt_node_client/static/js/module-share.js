/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('share', [])
.service('share', function($rootScope, $timeout) {
  return {
    show: function(obj) {
      $timeout(function() {
        $rootScope.$broadcast('share-show', obj)
      });
    },
    hide: function() {
      $timeout(function() {
        $rootScope.$broadcast('share-hide')
      });
    }
  };
})
.directive('shareContainer', ['share', 'WinManager', function(share, WinManager) {
  return {
    restrict: 'E',
    replace: true,
    scope: {},
    template:
      '<div id="share-container" ng-show="display" ng-click="display=false">' +
        '<div>' +
          '<div>' +
            '<div class="close" ng-click="display=false;">×</div>' +
            '<div class="left">' +
              '<div class="qrcode">' +
                '<qrcode version="8" data="{{ obj.weixin }}" size="200"></qrcode>' +
              '</div>' +
              '<div class="note"><i class="icon-wechat"></i> 扫我关注FBT公众号送300F</div>' +
            '</div>' +
            '<div class="right">' +
              '<div class="qrcode">' +
                '<qrcode version="8" data="{{ obj.url }}" size="200"></qrcode>' +
              '</div>' +
              '<div class="note"><i class="icon-pengyouquan"></i> 扫我分享到朋友圈送500F</div>' +
            '</div>' +
            '<div class="channel">' +
              '<div class="note"><i class="fa fa-info-circle"></i> 分享到下方渠道也送500F哦</div>' +
              '<i ng-repeat="c in channels" ng-class="c.icon" ng-click="shareClickHandler(c)"></i>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>',
    link: function(scope, elem, attrs) {
      scope.display = false;
      scope.channels = [
        {id: 'qzone', baseurl: 'http://sns.qzone.qq.com/cgi-bin/qzshare/cgi_qzshare_onekey?url=URL&title=TITLE&desc=DESC&pics=IMAGE', icon: 'icon-qzone'},
        {id: 'weibo', baseurl: 'http://service.weibo.com/share/share.php?url=URL&title=DESC&pic=IMAGE', icon: 'icon-weibo'},
        {id: 'renren', baseurl: 'http://widget.renren.com/dialog/share?resourceUrl=URL&title=TITLE&description=DESC&pic=IMAGE', icon: 'icon-renren'},
        {id: 'douban', baseurl: 'http://www.douban.com/share/service?href=URL&name=TITLE&text=DESC&image=IMAGE', icon: 'icon-douban'},
        {id: 'qq', baseurl: 'http://connect.qq.com/widget/shareqq/index.html?url=URL&title=TITLE&desc=DESC&pics=IMAGE', icon: 'icon-qq'}
        //{id: 'wechat', url: '', icon: 'icon-wechat'},
      ];

      scope.$on('share-show', function(event, obj) {
        scope.display = true;
        scope.obj = obj;
      });
      scope.$on('share-hide', function() {
        scope.display = false;
      });
      scope.shareClickHandler = function(channel) {
        var shareUrl = channel.baseurl
          .replace('URL', encodeURIComponent(scope.obj.url))
          .replace('TITLE', encodeURIComponent(scope.obj.title))
          .replace('DESC', encodeURIComponent(scope.obj.desc))
          .replace('IMAGE', encodeURIComponent(scope.obj.image));
        WinManager.open(shareUrl);

        scope.display = false;
      };
    }
  };
}]);
