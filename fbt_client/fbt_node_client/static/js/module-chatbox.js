/* vim: set sw=2 ts=2 expandtab : */
'use strict';
angular.module('chatbox', ['luegg.directives', 'emoji'])
.service('chatbox', function($rootScope, $timeout) {
  return {
    show: function(uid) {
      $timeout(function() {
        $rootScope.$broadcast('chatbox-show', {
          'currentUid':uid
        });
      })
    }
  };
})
.directive('chatboxContainer', ['chatbox', '$window', 'remoteSocket', 'AllFriend', 'toast', 'safeApply', '$http',
  function(chatbox, $window, remoteSocket, AllFriend, toast, safeApply, $http) {
  var template = '\
    <div id="chatbox-container" ng-show="display" ng-init="display=false">\
      <div class="skin"></div>\
      <div class="chat-close" ng-click="display=false">×</div>\
      <div class="window">\
        <div class="tabs">\
          <div class="tab" ng-class="{\'choosed\': choosedChat == \'群聊\'}" ng-click="chooseChat(\'群聊\')" ng-init="choosedChat=\'群聊\'">\
            <span class="mark" ng-show="hasUnreadMessage(\'群聊\')">·</span>\
            <img src="img/avatar.jpg">\
            <label>群聊</label>\
          </div>\
          <div class="tab" ng-class="{\'choosed\': choosedChat == uid}" ng-mouseenter="showCloseButton=true" ng-mouseleave="showCloseButton=false" ng-click="chooseChat(uid)" ng-repeat="(uid, chats) in singleChats">\
            <span class="mark" ng-show="hasUnreadMessage(uid)">·</span>\
            <img ng-src="{{ getIconFromUid(uid) }}">\
            <span class="chat-close" ng-show="showCloseButton" ng-click="removeChat(uid)">×</span>\
            <label>{{ getNickNameFromUid(uid) }}</label>\
          </div>\
        </div>\
        <div class="chat">\
          <div class="message allowselect" scroll-glue>\
            <span ng-class="{true:\'send\', false:\'receive\'}[chat.uid == fbtUID || chat.sender == fbtUID]" ng-repeat="chat in currentChats">\
              <i>{{ chat.name }} {{ chat.time }}</i> <i title="加为好友" class="fa fa-plus-circle" ng-click="addFriendByNick(chat.name)" ng-hide="isMyFriend(chat.uid) || choosedChat != \'群聊\'"></i>\
              <i ng-bind-html-unsafe="chat.msg | emoji"></i>\
            </span>\
          </div>\
          <div class="emotion" ng-show="emotion">\
            <span ng-repeat="emojiItem in emojis"><i class="cur_p emoji emoji_{{emojiItem}}" ng-click="chooseEmotionClickHandler($index)">{{emojiItem}}</i></span>\
          </div>\
          <div class="input">\
            <textarea ng-model="typedMessage"\
              ng-init="typedMessage = \'\'"\
              ng-keypress="sendMessageKeyPressHandler($event)"\
              placeholder="Ctrl+回车可以快速发送消息哦"></textarea>\
            <button class="smile" ng-click="showEmotion()"><i class="fa fa-smile-o fa-2x"></i></button>\
            <button ng-click="sendMessage()">发送</button>\
        </div>\
      </div>\
    </div>\
  ';
  return {
    restrict: 'E',
    replace: true,
    link: function(scope, elem, attrs) {
      $('#chatbox-container .tabs').easydrag({
        dialog: $('#chatbox-container')
      });
      scope.emojis = ["1","-1","100","angry","beers","birthday","bowtie","cold_sweat","dizzy_face","dog","flushed","ghost","heart_eyes","joy","kissing_heart","laughing","moneybag","muscle","ok_hand","pensive","pig","pray","rage","relieved","scream","clap","shit","skull","sleeping","sleepy","smile","sob","stuck_out_tongue_winking_eye","sunglasses","tada","tired_face","triumph","unamused","v","yum"]; 

      scope.sendMessageKeyPressHandler = function(event) {
        var keynum = event.keyCode || event.which;
        if(event.ctrlKey && keynum == 13 || keynum == 10) {
          scope.sendMessage();
        }
      };

      scope.sendMessage = function() {
        var sendGroupMessage = function(data) {
          remoteSocket.send(JSON.stringify(data));
          $window.groupChats.push(data);

          //根据用户发送内容，自动回复
          if($window.setting['chat_robot'] == 1) {
            (function autoReply(content) {
              var rules = {
                '积分规则': '点击【排行榜】（资源库右上角），可进入查看【积分规则】。因细小变动，具体请以官网为准',
                '赚积分': '多多上传【优质资源、首发资源】、ps：学习资源积分更多哟；多多在线，做种【供水】；多去【朋友圈】或者好友个人中心下载资源(免费)；多多【分享】',
                '赚F币': '多多上传【优质资源、首发资源】、ps：学习资源积分更多哟；多多在线，做种【供水】；多去【朋友圈】或者好友个人中心下载资源(免费)；多多【分享】',
                '网络不佳': '对方突然下线或者不在线，或者您已掉线，请等待…或者重启软件，还是不行的话请联系管理员: 1026250255',
                '稍后重试': '对方突然下线或者不在线，或者您已掉线，请等待…或者重启软件，还是不行的话请联系管理员: 1026250255',
                '排队中': '最多同时下载两个，剩余任务显示排队中，请稍后',
                '加群': '新用户欢迎加入【FBT官方群】6群339674514，或7群194239857，或8群389730107。加群后请先看群公告，谢谢您的支持！ 另，欢迎关注【fbt百度贴吧】，发帖留言你的疑问和建议，我们会不断改进 ~！O(∩_∩)O~',
                '批量': '暂时只能上传单个资源，或者压缩包。【文件夹上传、显示、下载】功能正在完善中。。。敬请期待。。O(∩_∩)O~~',
                '文件夹': '暂时只能上传单个资源，或者压缩包。【文件夹上传、显示、下载】功能正在完善中。。。敬请期待。。O(∩_∩)O~~',
                '怎么加好友': '好友列表右下角【+添加FBT好友】',
                '查看我的': '点击资源库主页【我的分享图标】，或者点击聊天室【个人头像】',
                '查看上传': '点击资源库右下角【N个资源正在上传】，可查看正在上传的资源和上传进度，以及取消上传',
                '下载不了': '检查自己是否有连接【ipv6】校园网，软件暂不支持ipv4下载；查看资源是否有人【在线】即 [在线数/总数]；检查自己是否【掉线】；实在米办法就【重启软件】试试……',
                '卡': 'O.O不可能吧，程序猿已经优化了。。。O(∩_∩)O~~',
                '上传的搜不到': '资源上传后，请【等待审核】…审核菌也是蛮拼的，最迟第二天即可显示； fbt已有一样的资源，你的资源信息被合并在首发者名下，可在评论里看到',
                '怎么删除': '【上传途中的资源】可点X取消上传；【上传完成的资源】可选择:移动电脑原文件、更改资源名、删除文件等方式删除',
                '电视看不了': '重装一下Windows Media Player，在CMD里输入regsvr32 wmnetmgr.dll，regsvr32 wmstream.dll'
              }
              for(var ruleKey in rules) {
                if(content.indexOf(ruleKey) > -1) {
                  var time = (new Date()).Format('hh:mm MM-dd');
                  var data = {
                    'uid':null,
                    'token':$window.token,
                    'type': 3,
                    'recv':'',
                    'sender':getCookie('fbt_user'),
                    'msg':'关于【' + htmlencode(ruleKey) + '】：' + rules[ruleKey],
                    'time':time,
                    'name':'FBT小兔'
                  };
                  $window.groupChats.push(data);
                }
              }
            }(scope.typedMessage));
          }
        }
        var sendSingleMessage = function(recv_uid, data) {
          remoteSocket.send(JSON.stringify(data));
          if($window.singleChats[recv_uid]
              && Object.keys($window.singleChats[recv_uid]).length)
            $window.singleChats[recv_uid].push(data);
          else
            $window.singleChats[recv_uid] = [data];
        };

        scope.typedMessage = scope.typedMessage.trim();
        if(!scope.typedMessage) {
          toast.showNoticeToast('内容为空不能发送，请重新输入');
          return;
        }
        if(scope.typedMessage.length > 200) {
          toast.showNoticeToast('内容过长，应少于200字哦');
          return;
        }
        var time = (new Date()).Format('hh:mm MM-dd');

        if (scope.choosedChat == '群聊') {
          var data = {
            'uid':$window.fbtUID,
            'token':$window.token,
            'type': 3,
            'recv':'',
            'sender':getCookie('fbt_user'),
            'msg':scope.typedMessage,
            'time':time,
            'name':$window.nick_name
          };
          sendGroupMessage(data);
        }
        else {
          var data = {
            'token':$window.token,
            'type': 2,
            'nick_name': $window.nick_name,
            'recv':scope.choosedChat,
            'sender':getCookie('fbt_user_id'),
            'msg':scope.typedMessage,
            'time':time,
            'name':$window.nick_name
          };     
          sendSingleMessage(scope.choosedChat, data);
        }
        scope.typedMessage = '';
      };

      scope.$on('chatbox-show', function(event, d) {
        scope.display = true;

        scope.fbtUID = $window.fbtUID;
        scope.singleChats = $window.singleChats;

        //scope.currentChats = scope.window.groupChats;
        scope.choosedChat = d['currentUid'] ? d['currentUid'] : '群聊';
        scope.chooseChat(scope.choosedChat);
      });
      
      scope.$on('chatbox-message', function() {
        safeApply(scope, function() {
          scope.chooseChat(scope.choosedChat);
        });
      });

      scope.$on('chatbox-hide', function(event, d) {
        scope.display = false;
      });

      scope.hasUnreadMessage = function(uid) {
        return false;
      };

      scope.removeChat = function(uid) {
        delete $window.singleChats[uid];
      }

      scope.chooseChat = function(uid) {
        if(uid == '群聊') {
          scope.currentChats = $window.groupChats;
        }
        else {
          scope.currentChats = $window.singleChats[uid];
        }
        scope.choosedChat = uid;
      };

      scope.showEmotion = function() {
        scope.emotion = !scope.emotion;
        //scope.emotion = !scope.emotion;//scope.emotion ? !scope.emotion : true;
      };

      scope.chooseEmotionClickHandler = function(emotionIndex) {
        scope.typedMessage += ':' + scope.emojis[emotionIndex] + ':';
        scope.emotion = false;//close emotion panel
        $('textarea').focus();
      };

      scope.getNickNameFromUid = function(uid) {
        return uid == '群聊' ? uid : AllFriend.getInfo(uid).nick_name;
      };

      scope.getIconFromUid = function(uid) {
        return uid == '群聊' ? null : AllFriend.getInfo(uid).icon;
      };

      scope.isMyFriend = function(uid) {
        return uid == scope.fbtUID || AllFriend.getInfo(uid) ? true : false;
      };

      scope.addFriendByNick = function(nick) {
        var param = {}
        param['op'] = 8;
        param['nick_name'] = nick;
        $http.post('/myFriend', param).success(function(data) {
          if(data["type"] && data["type"] == 1) {
            toast.showNoticeToast(data["result"]["result"]);
          }
          else {
            toast.showErrorToast(data["error"]);
          }
        });
      };
    },
    scope: {},
    template: template
  };
}]);
