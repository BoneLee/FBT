/*********************************************************************************
 *     File Name           :     baidu-share.js
 *     Created By          :     DQ - D.Q.Zhang.chn@gmail.com
 *     Creation Date       :     [2015-11-07 14:36]
 *     Last Modified       :     [2015-11-07 20:52]
 *     Description         :     百度分享的directive，封装之后更好用，有木有！！！
 **********************************************************************************/
angular.module('BaiDuShare', [])
  .service('BaiDuShare', function($rootScope) {
    this.shareInfo = {};
    this.changeShareInfo = function(_bdText, _bdDesc, _bdUrl, _bdPic) {
      this.shareInfo = {
        bdText: _bdText,
        bdDesc: _bdDesc,
        bdUrl: _bdUrl,
        bdPic: _bdPic,
      };
    };

  })
  .constant('baiduConfig', {


  })
  .directive('baidushare', ['BaiDuShare',

    function(BaiDuShare) {

      return {

        replace: true,
        restrict: 'E',
        link: function(scope, elm, attrs) {


        },
        controller: function($scope, $element, $attrs) {
          var mode = $attrs.mode;

          $scope.setShareInfo = function(cmd, config) {
            $scope.shareInfo = BaiDuShare.shareInfo;
            config.bdText = $scope.shareInfo.bdText;
            config.bdDesc = $scope.shareInfo.bdDesc;
            config.bdUrl = $scope.shareInfo.bdUrl;
            config.bdPic = $scope.shareInfo.bdPic;
            return config;
          };


          $scope.init = function() {

            window._bd_share_main = null;
            window._bd_share_config = {
              common: {
                onBeforeClick: $scope.setShareInfo,
              },
              share: [{
                "bdSize": 16,
                "bdMini": 2,
                "bdMiniList": ['tsina', "weixin", 'qzone', "renren", "baidu", "tqq", "sqq", "mshare", "tieba", "douban", "hi", "kaixin001", "t163", "tsohu", "fbook", "twi", "linkedin", "ibaidu", "bdhome", "xg", "ty", "meilishuo", "mogujie", "huaban", "duitang", "mail", "isohu", "bdxc", "thx"],
                "bdPopupOffsetLeft": -138
              }]
            };
            with(document) 0[(getElementsByTagName('head')[0] || body).appendChild(createElement('script')).src = 'http://bdimg.share.baidu.com/static/api/js/share.js?cdnversion=' + ~(-new Date() / 36e5)];

          }
        },
        template: '<div class="bdsharebuttonbox"  style="display:inline;" data-tag="share_2" ng-init="init();"><a data-cmd="more" style="background-image:none;margin:0 auto;padding:0 auto;font-size:12px;float:none;padding-left:0px;">分享</a></div>',

      }

    }
  ])
