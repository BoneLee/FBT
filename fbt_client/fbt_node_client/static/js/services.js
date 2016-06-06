/* vim: set sw=2 ts=2 : */
'use strict';

function buildGetUri(router, kwargs) {
  var baseUri = 'http://127.0.0.1:12345';
  var args = [];
  Object.keys(kwargs).forEach(function(key) {
    if(kwargs[key] || kwargs[key] == 0)
      args.push(key + '=' + kwargs[key]);
  });
  var uri = baseUri + '/' + router;
  uri += args.length!=0 ? '?' + args.join('&') : '';
  return uri;
}
app.directive('myMaxlength', ['$compile', function($compile) {
  return {
    restrict: 'A',
    require: 'ngModel',
    link: function (scope, elem, attrs, ctrl) {
      attrs.$set("ngTrim", "false");
      var maxlength = parseInt(attrs.myMaxlength, 10);
      ctrl.$parsers.push(function (value) {
          if (value.length > maxlength)
          {
              value = value.substr(0, maxlength);
              ctrl.$setViewValue(value);
              ctrl.$render();
          }
          return value;
      });
    }
  };
}]);
app.directive('contenteditable', function() {
  return {
    restrict: 'A', // only activate on element attribute
    require: '?ngModel', // get a hold of NgModelController
    link: function(scope, element, attrs, ngModel) {
      if(!ngModel) return; // do nothing if no ng-model

      // Specify how UI should be updated
      ngModel.$render = function() {
        element.html(ngModel.$viewValue || '');
      };

      // Listen for change events to enable binding
      element.on('blur keyup change', function() {
        scope.$apply(read);
      });
      element.on('mouseleave', function(){
        scope.updateShuo(htmlencode(element.html()));
      });
      read(); // initialize

      // Write data to the model
      function read() {
        var html = element.html();
        // When we clear the content editable the browser leaves a <br> behind
        // If strip-br attribute is provided then we strip this out
        if( attrs.stripBr && html == '<br>' ) {
          html = '';
        }
        html.
          replace(/&/g, '&amp;').
          replace(/</g, '&lt;').
          replace(/>/g, '&gt;');
        ngModel.$setViewValue(html);
      }
    }
  };
});
app.directive('ngRightClick', function($parse) {
    return function(scope, element, attrs) {
        var fn = $parse(attrs.ngRightClick);
        element.bind('contextmenu', function(event) {
            scope.$apply(function() {
                event.preventDefault();
                fn(scope, {$event:event});
            });
        });
    };
});
app.directive('fancyTree', function() {
  return {
    restrict: 'A',
    link : function(scope, element, attrs){
      $(element).fancytree({
        extensions: ["table"],
        checkbox: true,
        autoCollapse: true,
        autoScroll: true,
        selectMode: 3,
        table: {
          //indentation: 20,      // indent 20px per node level
          nodeColumnIdx: 1,     // render the node title into the 2nd column
          checkboxColumnIdx: 0  // render the checkboxes into the 1st column
        },
        source: scope.treeData,
        renderColumns: function(event, data) {
          var node = data.node,
          $tdList = $(node.tr).find(">td");
          if(typeof(scope.render) == "function")
            scope.render($tdList, node);
        },
        select: function(event, data) {
          /*var filesCount = 0;
          data.tree.visit(function(node){
            if(!node.folder) filesCount += 1;
          });*/
          var selectedFiles = $.map(data.tree.getSelectedNodes(), function(node){
            if(node.folder) return null;
            return node.key;
          });
          scope.select(selectedFiles);
          // Download callback
          //$('#btn-download-selected-files').text('下载(' + selectedFiles.length + '/' + filesCount + ')');
        }
      });
    }
  }
});
app.directive('switch', function(){
  return {
    restrict: 'AE'
  , replace: true
  , transclude: true
  , template: function(element, attrs) {
      var html = '';
      html += '<span';
      html +=   ' class="switch' + (attrs.class ? ' ' + attrs.class : '') + '"';
      html +=   attrs.ngModel ? ' ng-click="' + attrs.ngModel + '=!' + attrs.ngModel + (attrs.ngChange ? '; ' + attrs.ngChange + '()"' : '"') : '';
      html +=   ' ng-class="{ checked:' + attrs.ngModel + ' }"';
      html +=   '>';
      html +=   '<small></small>';
      html +=   '<input type="checkbox"';
      html +=     attrs.id ? ' id="' + attrs.id + '"' : '';
      html +=     attrs.name ? ' name="' + attrs.name + '"' : '';
      html +=     attrs.ngModel ? ' ng-model="' + attrs.ngModel + '"' : '';
      html +=     ' style="display:none" />';
      html +=     '<span class="switch-text">'; /*adding new container for switch text*/
      html +=     attrs.on ? '<span class="on">'+attrs.on+'</span>' : ''; /*switch text on value set by user in directive html markup*/
      html +=     attrs.off ? '<span class="off">'+attrs.off + '</span>' : ' ';  /*switch text off value set by user in directive html markup*/
      html += '</span>';
      return html;
    }
  }
});
app.directive('pbar', function(){
    var html = '<div class="progress active-bar" style="text-align: center">'+
      '<div style="position: relative;z-index: 10;top: inherit;left: inherit;">{{oneDownloadItem.value}}'+
      '</div><div class="progress-bar" style="margin-top: -20px; position: relative; z-index: 0; top: inherit; left: inherit; width: 100%; border-radius: 3px; height: inherit;width: {{oneDownloadItem.progress}}%"></div></div>';
    return {
    restrict: 'E',
    replace: true,
    template: html,
    link: function(scope, elem, attrs){
      scope.oneDownloadItem = scope[attrs.value];
      scope.isDigit = function (value) {
        var patrn = /^[0-9]*$/;
        if (patrn.exec(value) == null || value == "") {
          return false
        } else {
          return true
        }
      };
      scope.shouldShowInfo = function(val){
        if(scope.isDigit(val))
          return false;
        return true;
      };
    }
  }
});
app.filter('escapeHTML', function() {
  return function (text) {
    if (text) {
      return text.
          replace(/&/g, '&amp;').
          replace(/</g, '&lt;').
          replace(/>/g, '&gt;');
    }
    return '';
  };
});
app.directive('autocomplete', function() {
  var index = -1;

  return {
    restrict: 'E',
    scope: {
      searchParam: '=ngModel',
      suggestions: '=data',
      onType: '=onType',
      onSelect: '=onSelect',
      autocompleteRequired: '='
    },
    controller: ['$scope', function($scope){
      // the index of the suggestions that's currently selected
      $scope.selectedIndex = -1;

      $scope.initLock = true;

      // set new index
      $scope.setIndex = function(i){
        $scope.selectedIndex = parseInt(i);
      };

      this.setIndex = function(i){
        $scope.setIndex(i);
        $scope.$apply();
      };

      $scope.getIndex = function(i){
        return $scope.selectedIndex;
      };

      // watches if the parameter filter should be changed
      var watching = true;

      // autocompleting drop down on/off
      $scope.completing = false;

      // starts autocompleting on typing in something
      $scope.$watch('searchParam', function(newValue, oldValue){

        if (oldValue === newValue || (!oldValue && $scope.initLock)) {
          return;
        }

        if(watching && typeof $scope.searchParam !== 'undefined' && $scope.searchParam !== null) {
          $scope.completing = true;
          $scope.searchFilter = $scope.searchParam;
          $scope.selectedIndex = -1;
        }

        // function thats passed to on-type attribute gets executed
        if($scope.onType)
          $scope.onType($scope.searchParam);
      });

      // for hovering over suggestions
      this.preSelect = function(suggestion){

        watching = false;

        // this line determines if it is shown
        // in the input field before it's selected:
        //$scope.searchParam = suggestion;

        $scope.$apply();
        watching = true;

      };

      $scope.preSelect = this.preSelect;

      this.preSelectOff = function(){
        watching = true;
      };

      $scope.preSelectOff = this.preSelectOff;

      // selecting a suggestion with RIGHT ARROW or ENTER
      $scope.select = function(suggestion){
        if(suggestion){
          $scope.searchParam = suggestion;
          $scope.searchFilter = suggestion;
          if($scope.onSelect)
            $scope.onSelect(suggestion);
        }
        watching = false;
        $scope.completing = false;
        setTimeout(function(){watching = true;},1000);
        $scope.setIndex(-1);
      };


    }],
    link: function(scope, element, attrs){

      setTimeout(function() {
        scope.initLock = false;
        scope.$apply();
      }, 250);

      var attr = '';

      // Default atts
      scope.attrs = {
        "placeholder": "start typing...",
        "class": "",
        "id": "",
        "inputclass": "",
        "inputid": ""
      };

      for (var a in attrs) {
        attr = a.replace('attr', '').toLowerCase();
        // add attribute overriding defaults
        // and preventing duplication
        if (a.indexOf('attr') === 0) {
          scope.attrs[attr] = attrs[a];
        }
      }

      if (attrs.clickActivation) {
        element[0].onclick = function(e){
          if(!scope.searchParam){
            setTimeout(function() {
              scope.completing = true;
              scope.$apply();
            }, 200);
          }
        };
      }

      var key = {left: 37, up: 38, right: 39, down: 40 , enter: 13, esc: 27, tab: 9};

      document.addEventListener("keydown", function(e){
        var keycode = e.keyCode || e.which;

        switch (keycode){
          case key.esc:
            // disable suggestions on escape
            scope.select();
            scope.setIndex(-1);
            scope.$apply();
            e.preventDefault();
        }
      }, true);

      document.addEventListener("blur", function(e){
        // disable suggestions on blur
        // we do a timeout to prevent hiding it before a click event is registered
        setTimeout(function() {
          scope.select();
          scope.setIndex(-1);
          scope.$apply();
        }, 150);
      }, true);

      element[0].addEventListener("keydown",function (e){
        var keycode = e.keyCode || e.which;

        var l = angular.element(this).find('li').length;

        // this allows submitting forms by pressing Enter in the autocompleted field
        if(!scope.completing || l == 0) return;

        // implementation of the up and down movement in the list of suggestions
        switch (keycode){
          case key.up:

            index = scope.getIndex()-1;
            if(index<-1){
              index = l-1;
            } else if (index >= l ){
              index = -1;
              scope.setIndex(index);
              scope.preSelectOff();
              break;
            }
            scope.setIndex(index);

            if(index!==-1)
              scope.preSelect(angular.element(angular.element(this).find('li')[index]).text());

            scope.$apply();

            break;
          case key.down:
            index = scope.getIndex()+1;
            if(index<-1){
              index = l-1;
            } else if (index >= l ){
              index = -1;
              scope.setIndex(index);
              scope.preSelectOff();
              scope.$apply();
              break;
            }
            scope.setIndex(index);

            if(index!==-1)
              scope.preSelect(angular.element(angular.element(this).find('li')[index]).text());

            break;
          case key.left:
            break;
          case key.right:
          case key.enter:
          case key.tab:

            index = scope.getIndex();
            // scope.preSelectOff();
            if(index !== -1) {
              scope.select(angular.element(angular.element(this).find('li')[index]).text());
              if(keycode == key.enter) {
                e.preventDefault();
              }
            } else {
              if(keycode == key.enter) {
                scope.select();
              }
            }
            scope.setIndex(-1);
            scope.$apply();

            break;
          case key.esc:
            // disable suggestions on escape
            scope.select();
            scope.setIndex(-1);
            scope.$apply();
            e.preventDefault();
            break;
          default:
            return;
        }

      });
    },
    template: '\
        <div class="autocomplete {{ attrs.class }}" id="{{ attrs.id }}">\
          <input\
            type="text"\
            ng-model="searchParam"\
            placeholder="{{ attrs.placeholder }}"\
            class="{{ attrs.inputclass }}"\
            id="{{ attrs.inputid }}"\
            ng-required="{{ autocompleteRequired }}" />\
          <ul ng-show="completing && searchParam && (suggestions | filter:searchFilter).length > 0">\
            <li\
              suggestion\
              ng-repeat="suggestion in suggestions | filter:searchFilter | orderBy:\'toString()\' track by $index"\
              index="{{ $index }}"\
              ng-class="{ active: ($index === selectedIndex) }"\
              ng-click="select(suggestion)"\
              ng-bind-html="suggestion | highlight:searchParam">{{ suggestion }}</li>\
          </ul>\
        </div>'
  };
});

app.filter('highlight', ['$sce', function ($sce) {
  return function (input, searchParam) {
    if (typeof input === 'function') return '';
    if (searchParam) {
      var words = '(' +
            searchParam.split(/\ /).join(' |') + '|' +
            searchParam.split(/\ /).join('|') +
          ')',
          exp = new RegExp(words, 'gi');
      if (words.length) {
        input = input.replace(exp, "<span class=\"highlight\">$1</span>");
      }
    }
    return $sce.trustAsHtml(input);
  };
}]);

app.directive('suggestion', function(){
  return {
    restrict: 'A',
    require: '^autocomplete', // ^look for controller on parents element
    link: function(scope, element, attrs, autoCtrl){
      element.bind('mouseenter', function() {
        autoCtrl.preSelect(attrs.val);
        autoCtrl.setIndex(attrs.index);
      });

      element.bind('mouseleave', function() {
        autoCtrl.preSelectOff();
      });
    }
  };
});

app.service('toast', function(toaster){
  this.showErrorToast = function(msg){
    toaster.pop('error', '系统提示', msg, true);
  };
  this.showNoticeToast = function(msg){
    toaster.pop('note', '系统提示', msg, true);
  };
  this.showSuccessToast = function(msg){
    toaster.pop('success', '系统提示', msg, true);
  };
  this.showWarningToast = function(msg){
    toaster.pop('warning', '系统提示', msg, true);
  };

  this.showStickyErrorToast = function(msg){
    toaster.pop('error', '系统提示', msg, false);
  };
  this.showStickyNoticeToast = function(msg){
    toaster.pop('note', '系统提示', msg, false);
  };
  this.showStickySuccessToast = function(msg){
    toaster.pop('success', '系统提示', msg, false);
  };
  this.showStickyWarningToast = function(msg){
    toaster.pop('warning', '系统提示', msg, false);
  };
});

app.factory('localSocket', function ($rootScope, toast, $window, $modal, remoteSocket) {
  $window.uploadProgress = {};
  $window.uploadSize = {};
  $window.msgCenter = [];
  $window.global = {};
  $window.upload_count = 0;
  $window.global["isLogin"] = false;
  var socket = io('http://localhost');
  $window.socket = socket;
  socket.on("index", function(data){
    data = JSON.parse(data);
    $window.nick_name = data["nick_name"];
    $window.msgCenter = data["msg"];
    //console.log($window.msgCenter)
    $window.global.msgCount = data["count"];
  });
  socket.on('inform', function(data){
    toast.showNoticeToast(data);
  });
  socket.on('inform_sticky', function(data){
    toast.showStickyNoticeToast(data);
  });
  socket.on('file_name', function(data){
    $("#resourceName").val(data);
  });
  socket.on("douban", function(data){
    $window.shouldUpload = true;
    $("#err_tips").html("");
    if(data)
    {
        $window.uploadDoubanData = JSON.parse(data);
        var summary = $window.uploadDoubanData["summary"];
        if(summary.length > 100)
            summary = summary.substr(0,100)+"...";
        var html = common_html_0+$window.uploadDoubanData["year"]+common_html_1+$window.uploadDoubanData["countries"]+
        common_html_2+summary
        +common_html_3+$window.uploadDoubanData["link"]+common_html_4;
        $("#upload_exp_info").remove();
        $("#upload_panel").append(html);
        delete $window.uploadDoubanData.link;
    }
    else{
      var val = $("#resourceName").val();
      if(!val || !isChinese(val)){
        toast.showErrorToast("资源信息获取失败，填写一个中文资源名称试试~");
      }
      else {
        toast.showErrorToast("资源信息获取失败，请尝试修改资源名");
      }
    }
  });
  socket.on("net",function(){
    toast.showErrorToast("目前网络状况不佳，有操作未能完成，请检查网络或者重试");
  });
  socket.on("update",function(){
    $modal.open({
      backdrop: false, 
      keyboard: false,
      animation: true,
      templateUrl: 'updateModal.html',
      controller: 'updateCtrl',
    });
  });
  socket.on('start_sock',function(data){
    var tmp_data;
    try{
        tmp_data = JSON.parse(data);
    }
    catch(e){
        tmp_data = data;
    }
    data = tmp_data;
    $window.fbtUID = $window.parseInt(data["uid"]);
    $window.user = data["user"];
    console.log("start remote sock, uid:"+$window.fbtUID);
    remoteSocket.initSocket();
  });
  socket.on('checkOnline', function(data){
    try{
        remoteSocket.send(JSON.stringify({"uid":$window.fbtUID,"token":$window.token,"type":10,"uid_list":data}));
        console.log("check offline");
    }
    catch(e){
        console.log("sock offline");
    }
  });
  socket.on('s_upload', function(data){
    //console.log(data);
    try{
        remoteSocket.send(JSON.stringify({"uid":$window.fbtUID,"token":$window.token,"data":data,"type":11}));
    }
    catch(e){
      if(!$window.uploadData){
        $window.uploadData = [];
      }
      $window.uploadData.push(data);
    }
  });
  socket.on('upload', function(data){
    var tmp_data;
    try{
        tmp_data = JSON.parse(data);
    }
    catch(e){
        tmp_data = data;
    }
    data = tmp_data;
    if(data != ""){
        if(data["type"] == 2){
          if(data["id"] in $window.uploadProgress)
            return;
          $window.uploadProgress[data["id"]] = data;
          $window.uploadProgress[data["id"]]['showCancel'] = true;
          $window.uploadProgress[data["id"]]['showError'] = false;
          $window.uploadProgress[data["id"]]['progress'] = '等待上传';
          $window.uploadSize[data["id"]] = data["size"];
        }
        else if(data["type"] == 1){
          if("msg" in data)
            toast.showSuccessToast(data["msg"]);
          else
          {
            if(data["id"] in $window.uploadProgress) {
              $window.uploadProgress[data["id"]]['showCancel'] = false;
              $window.uploadProgress[data["id"]]['showError'] = true;
            }
            toast.showErrorToast(data["error"]);
          }
          if($window.upload_count > 0)
              $window.upload_count--;
          if($window.upload_count == 0)
            $window.showUploadingHint = false;
        }
        else if(data["type"] == 0)
        {
          $window.uploadProgress[data["id"]]['showCancel'] = false;
          $window.uploadProgress[data["id"]]['showError'] = true;
          toast.showErrorToast(data["error"]);
        }
        else if(data["type"] == 3){
          $window.uploadProgress[data["id"]]['progress'] = data["progress"];
          if(data["progress"] == "100%")
            $window.uploadProgress[data["id"]]['showCancel'] = false;
          else
            $window.uploadProgress[data["id"]]['showCancel'] = true;
        }              
    }
  });
  return {
    on: function (eventName, callback) {
      socket.on(eventName, function () {  
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    },
    send: function(eventName, data){
      socket.emit(eventName, data);
    }
  };
});

app.factory('remoteSocket', function ($window, $http, toast, AllFriend, $rootScope, safeApply, $location){
  $window.groupChats = [];
  $window.singleChats = {};
  var ws = null;
  var shouldReconnect = true;
  var reconnect = function(){
    var t = (new Date()).getTime();
    if(t-$window.r_heart>360000 && ws){
      ws.close();
    }
  }
  var sendHeart = function(){
      $window.socket.emit('tick');
      $window.setTimeout(reconnect, 120000);
      try{
        ws.send(JSON.stringify({type: 9}));
      }
      catch(e){
        console.log(e.stack);
      }
  }
  var sendUpload = function (){
      if(!$window.uploadData || $window.uploadData.length == 0){
        clearInterval($window.uploadInterval);
        delete $window.uploadInterval;
      }
      else{
        var data = $window.uploadData.shift();
        ws.send(JSON.stringify({"uid":$window.fbtUID,"token":$window.token,"data":data,"type":11}));
      }
  }
  var doReconnect = function (){
    toast.showNoticeToast("系统已经自动重连");
    console.log("sock restart"+(new Date()).getTime());
    //tell user reconnect
    $window.global.isUserOnline = true;
    ws.send(JSON.stringify({connect:1,token:$window.token,type: 0, uid: $window.fbtUID, user: $window.user}));
  }
  var createSock = function(){
    if(!ws){
      // 修改服务器URL直接切换注释即可
      //ws = new WebSocket('ws://211.149.223.64:8888/socket');
      //ws = new WebSocket('ws://211.149.207.145:8888/socket');
      ws = new WebSocket('ws://socket.friendsbt.com:8888/socket');
      ws.onopen = function(){
        //ws.send( "0"+$("b.user").html());
        if($window.sock_restart){
          if(shouldReconnect){
              setTimeout(doReconnect, 3000);
              //$window.uploadInterval = window.setInterval(sendUpload, 10000);
          }
          clearInterval($window.sock_restart);
          delete $window.sock_restart;
        }
        else{
          console.log("sock open");
          ws.send(JSON.stringify({connect:0,token:$window.token,type: 0, uid: $window.fbtUID, user: $window.user}));
          //$.get("/startServer/local", function(data){console.log("local server start.");},true);
        }
        shouldReconnect = true;
        $window.r_heart = (new Date()).getTime();
        if($window.heart)
          clearInterval($window.heart);
        $window.heart = $window.setInterval(sendHeart,180000);
      };
      ws.onmessage = function(event) {
        //console.log(event.data);
        var data;
        try{
          data = JSON.parse(event.data);
        }
        catch(e){
          toast.showNoticeToast("网络通信出现了一点小问题，请重试");
          return;
        }
        //type 0 for sys, 1 for left, 2 for single chat, 3 fro group chat, 4 for coin, 5 for login repeat
        //6 for remove friend, 7 for sys info, 8 for update,9 for heart
        if(!("type" in data))
        {
          toast.showNoticeToast("网络通信出现了一点小问题，请重试");
          return;
        }
        if(data["type"] == 0){
          if("ip" in data){
            $http.get("/startServer/local?ip="+data["ip"]).success(function(data){console.log("local server start.");});
          }
          else if("id" in data){
            if("nick" in data){
              safeApply($rootScope, function() {
                toast.showNoticeToast(data["nick"]+"想加你为好友");
              });
            }
            $window.msgCenter.push(data);
            $window.global.msgCount ++;
          }
          else if("message_type" in data){
            var MESSAGE={"OPEN_UDP_SERVER": 1};//more....
            if(data["message_type"]==MESSAGE["OPEN_UDP_SERVER"]){
              //json.dumps({"message_type": OPEN_UDP_SERVER, "file_hash": file_hash,"what": "open udp server","for": for_who})
              $http.get("/startServer/nat?for="+data["for"]+"&hash="+data["file_hash"]+"&size="+data["file_size"]).success(function(data){console.log("nat server start.");});
            }//TODO FIXME more mesaage processing here
          }
          else if("user" in data){
            if(data['uid']+'' in AllFriend.friendsUids)
            {
              console.log("friend exist");
              return;
            }
            var friendGroup = AllFriend.friendGroups[1];
            friendGroup["total"]++;
            AllFriend.info.count ++;
            AllFriend.friendsUids[data['uid']+''] = 0;
            if(data["online"] == 1){
              friendGroup["online"]++;
              friendGroup["friends"].unshift(data);
            }
            else
              friendGroup["friends"].push(data);
          }
          else if("sys" in data){
            var friendGroup = AllFriend.friendGroups[1];
            var friends = friendGroup["friends"];
            for(var i = 0; i < friends.length; i++){
              if(parseInt(friends[i]["uid"]) == parseInt(data["sys"])){
                friends[i]["online"] = 1;
                var tmp = friends[i];
                friends.splice(i, 1);
                friends.unshift(tmp);
                break;
              }
            }
            if(friendGroup["online"] < friendGroup["total"])
              friendGroup["online"]++;
            if($window.setting["friends_online_inform"] == 1)
              toast.showNoticeToast(data["msg"]);
          }
          else if("err" in data){
            toast.showErrorToast(data["err"]);
          }
          else{
            toast.showNoticeToast(data["msg"]);
          }
        }
        else if(data["type"] == 1){
          var friendGroup = AllFriend.friendGroups[1];
          var friends = friendGroup["friends"];
          for(var i = 0; i < friends.length; i++){
            if(parseInt(friends[i]["uid"]) == parseInt(data["user"])){
              friends[i]["online"] = 0;
              var tmp = friends[i];
              friends.splice(i, 1);
              friends.push(tmp);
              break;
            }
          }
          if(friendGroup["online"] > 0)
            friendGroup["online"]--;
          if($window.setting["friends_online_inform"] == 1)
            toast.showNoticeToast(data["msg"]);
        }
        else if(data["type"] == 3){
          //{"type":3,"recv":"","sender":who,"msg":content,"time":time}                        
          //appendGroupChatToView(data);
          //how to tell people group chat have received
          $window.groupChats.push(data);
          safeApply($rootScope, function() {
            $window.global.hasNewGroupChat = true;
          });
          $rootScope.$broadcast('chatbox-message');
        }
        else if(data["type"] == 2){
          if(!$window.singleChats[data["sender"]])
            $window.singleChats[data["sender"]] = [];
          data["nick_name"] = htmlencode(data["nick_name"]);
          data["msg"] = htmlencode(data["msg"]); 
          $window.singleChats[data["sender"]].push(data);   
          safeApply($rootScope, function() {
            $window.global.hasNewSingleChat = true;        
          });
          $rootScope.$broadcast('chatbox-message');
        }
        else if(data["type"] == 4){
          if(data["add"] == 1){
            $window.global.fbCoin += window.parseInt(data["coin"]);
          }
          else
            $window.global.fbCoin = window.parseInt(data["coin"]);
        }
        else if(data["type"] == 5){
          toast.showWarningToast("您的账号在其他地方登录了，如果不是本人操作，请重新登录，并修改自己的密码。");
          clearCookie();
          //TODO FIX ME: I should handle this
          shouldReconnect = false;
          $window.global.shouldDisconnect = true;
          $location.path("/login");
        }
        else if(data["type"] == 6){
          //friend delete you
          var friendGroup = AllFriend.friendGroups[1];
          var friends = friendGroup["friends"];
          for(var i = 0; i < friends.length; i++){
            if(parseInt(friends[i]["uid"]) == parseInt(data["sys"])){
              friends.splice(i, 1);
              break;
            }
          }
          delete AllFriend.friendsUids[data["sys"]];
          if(AllFriend.info.count > 0)
            AllFriend.info.count --;
          if(friendGroup["online"] > 0)
            friendGroup["online"]--;
          if(friendGroup["total"] > 0)
            friendGroup["total"]--;
        }
        else if(data["type"] == 7){
          if("msg" in data && data["msg"] == 1){
            $window.msgCenter.push(data);
            $window.global.msgCount ++;
          }
          else{
            if(data["sticky"] == 0){
              toast.showNoticeToast(data["content"]);
            }
            else{
              toast.showStickyNoticeToast(data["content"]);
            }
          }
        }
        else if(data["type"] == 8){
          //re-connect friend restore
          var all_uid = data["uid"];
          var uidMap = {};
          var l = all_uid.length;
          for(var i = 0; i < l; i++){
            uidMap[all_uid[i]+""] = true;
          }
          var friendGroup = AllFriend.friendGroups[1];
          if(friendGroup["online"] < friendGroup["total"])
              friendGroup["online"] += l;
          var friends = friendGroup["friends"];
          for(var i = 0; i < friends.length; i++){
            if(friends[i]["uid"]+"" in uidMap){
              friends[i]["online"] = 1;
            }
          }
        }
        else if(data["type"] == 9){
          $window.socket.emit("offline", data["uid"]);
        }
        else if(data["type"] == 11){
          $window.socket.emit("s_upload", event.data);
        }
        else if(data["type"] == 12){
          /*if("friend_size" in data){
              
          }*/
        }
        else if(data["type"] == 13){
          $window.r_heart = (new Date()).getTime();
        }
      };
      ws.onclose = function(event){
        console.log(event);
        ws = null;
        if($window.heart)
        {
          clearInterval($window.heart);
          delete $window.heart;
        }
        if($window.fbtUID && !$window.sock_restart){
          var friendGroup = AllFriend.friendGroups[1];
          friendGroup["online"] = 0;
          var friends = friendGroup["friends"];
          for(var i = 0; i < friends.length; i++){
            friends[i]["online"] = 0;
          }
          $window.global.isUserOnline = false;
          $window.sock_restart = $window.setInterval(createSock, 2000);
        }           
      };
    }
  }
  return{
    send: function(msg){
      if(ws)
        ws.send(msg);
      else
        toast.showErrorToast("网络通信出现了一点小问题，请重试");
    },
    initSocket: function(){
      createSock();
    }
  }
});
/*socket.on('init', function (data) {
  $scope.name = data.name;
  $scope.users = data.users;
});
socket.emit('change:name', {
  name: $scope.newName
}, function (result) {
  if (!result) {
    alert('There was an error changing your name');
  } else {

    changeName($scope.name, $scope.newName);

    $scope.name = $scope.newName;
    $scope.newName = '';
  }
});*/
app.factory('Reward', function($http) {
  return {
    all_reward: function(callback, res_type, time, page, sort_by) {
      if(!sort_by)
        sort_by = 0;
      var kwargs = {
        time: time,
        page: page,
        sort_by: sort_by
      };
      if(res_type !== -1)
        kwargs.res_type = res_type;

      var uri = buildGetUri('all_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    offer_reward: function(callback, uid, res_type, desc, fileName, fb, res_year, res_country) {
      var kwargs = {
        uid: uid,
        res_type: res_type,
        desc: desc,
        fileName: fileName,
        fb: fb,
        res_year: res_year,
        res_country: res_country
      };

      var uri = buildGetUri('offer_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    append_reward: function(callback, rid, appendFb) {
      var kwargs = {
        rid: rid,
        appendFb:appendFb
      };

      var uri = buildGetUri('append_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    my_reward: function(callback, res_type, page) {
      var kwargs = {
        page: page
      };
      if(res_type !== -1)
        kwargs.res_type = res_type;

      var uri = buildGetUri('my_reward', kwargs);
      return $http.get(uri).success(callback);
    },
    cancel_reward: function(callback, rid, res_type){
      var kwargs = {
        rid: rid,
        res_type: res_type
      };

      var uri = buildGetUri('cancel_reward', kwargs);
      return $http.get(uri).success(callback);
    },
  };
});
app.service("AllFriend", function($http, $window){
  this.friendGroups = [];
  this.friendsUids = {};
  this.info = {};
  var sortBy = function(o1, o2){
    return o2.online - o1.online;
  };
  this.getInfo = function(uid){
    var friends = this.friendGroups[1].friends;
    for(var i = 0; i < friends.length; i++){
      if(friends[i]["uid"] == uid){
        return friends[i];
      }
    }
    return null;
  };
  this.get = function(callback){
    var uri = buildGetUri('mySpace', {});
    //console.log(uri);
    return $http.get(uri).success(callback);
  };
  this.init = function(){
    var that = this;
    this.get(function(data){
      that.friendsUids[$window.fbtUID+''] = 0;
      that.friendsUids['null'] = 0;
      if(data){          
        that.info.icon = data["icon"];
        that.info.nick_name = data["nick_name"];
        $window.global.fbCoin = data["fb_coin"];
        that.info.shuo = data["shuo"];
        that.info.count = data["count"];
        that.info.resSize = data["size"];
        var starFriendGroup = {"index":0,"title":"我粉的","id":"friendstar","online":0,"total":0,"friends":[]};
        that.friendGroups.push(starFriendGroup);
        data["friends"] = data["friends"].sort(sortBy);
        var friendGroup = {"index":1,"title":"好友","id":"myfriend","online":data["count_online"],"total":data["count"],"friends":data["friends"]};
        that.friendGroups.push(friendGroup);
        for (var i = 0; i < data["friends"].length; i++) {
          that.friendsUids[data["friends"][i]["uid"]+''] = 0;
        }
      };        
    });
  };
});
app.factory("AllMyInfo", function($http){
  return {
    get: function(callback){
      var uri = buildGetUri('myInfo', {});
      //console.log(uri);
      return $http.get(uri).success(callback);
    }
  };
});
app.factory("FriendSpace", function($http, $window){
  return {
    getInfo: function(uid, isPublic, callback){
      var kwargs = {
        public: isPublic,
        uid: uid
      };

      var uri = buildGetUri('friend_res', kwargs);
      return $http.get(uri).success(callback);
    }
  };
});
app.factory("AllRes", function($http, $window, toast, Cache){
  return {
    getAllRes: function(resType, page, sortBy,callback){
      var cacheKey = ['AllRes', resType, page, sortBy].join(' ');
      var cached = Cache.get(cacheKey);
      if(cached != null) {
        callback(0, cached);
        return;
      }

      var kwargs = {
        op: 4,
        user: $window.fbtUID,
        page: page,
        res_type: resType,
        sort_by: sortBy
      };

      var uri = buildGetUri('res', {});
      //type, size, resource_list, isPrivateDownload
      return $http.post(uri, kwargs).success(function(data){
        if(data["type"] == 1){
          preHandleRes(data.resource_list);
          Cache.set(cacheKey, data);
          callback(0, data);
        }
        else{
          callback(1);
          toast.showErrorToast("获取资源失败，请检查网络状况");
        }
      });
    }
  };
});
app.factory("MyRes", function($http, $window){
  return {
    getMyRes: function(page, friend, isPrivateDownload, callback){
      //type, size, resource_list, isPrivateDownload
      var kwargs = {
        op: 8, 
        uid: $window.fbtUID,
        friend: friend,
        page: page,
        isPrivateDownload: isPrivateDownload
      };

      var uri = buildGetUri('res', {});
      $http.post(uri, kwargs).success(function(data){
        callback(data);
      });
    }
  };
});
app.factory('HisRes', function($http, $window, toast, downloader){
  return{
    getHis: function(){
      $http.post("/res", {"op":10,"user":$window.fbtUID}).success(function(data){
        if(data["type"] == 1){
          for (var i = 0; i < data["resource_list"].length; i++) {
            downloader.parseDownloadInfo(data["resource_list"][i], data["resource_list"][i]["isPrivateDownload"]
            , data["resource_list"][i]["file_hashes"], data["resource_list"][i]["file_sizes"], true);
          }
        }
        else{
          toast.showErrorToast("获取我的下载信息失败，请检查网络状况");
        }
      });
    }
  };
});
app.factory("AllFriendRes", function($http, $window, toast, Cache){
  return{
    getRes: function(resType, sort, page, callback){
      var cacheKey = ['AllFriendRes', resType, sort, page].join(' ');
      var cached = Cache.get(cacheKey);
      if(cached != null) {
        callback(0, cached);
        return;
      }

      if(resType == -1)
      {
        //sort 0 is time, 1 is hot
        $http.post("/res", {"op":9, "user":$window.fbtUID, "sort": sort, "page": page}).success(function(data){
          if(data["type"] == 1){
            preHandleRes(data.resource_list);
            Cache.set(cacheKey, data);
            callback(0, data);
          }
          else{
            callback(1, data);
            toast.showErrorToast("获取朋友圈资源失败，请检查网络状况");
          }
        });
      }else{
        //sort 0 is time, 1 is hot
        $http.post("/res", {"op":9, "user":$window.fbtUID, "type": resType, "sort": sort, "page": page}).success(function(data){
          if(data["type"] == 1){
            preHandleRes(data.resource_list);
            Cache.set(cacheKey, data);
            callback(0, data);
          }
          else{
            callback(1, data);
            toast.showErrorToast("获取朋友圈资源失败，请检查网络状况");
          }
        });
      }
    }
  };
});
app.factory("SearchRes", function($http, $window, toast, Cache){
  var validKeyWord = function(keyWord){
    return keyWord.length > 0 && keyWord.length<=20;
  };
  return{
    getResByKey: function(keyWord, page, isFriend, callback){
      //param: private is to check if the searching is in friends, you can use any num, e.g. number 1
      //result: type, size, resource_list, isPrivateDownload
      keyWord = keyWord.trim();
      if(validKeyWord(keyWord)){
        var cacheKey = ['SearchRes', keyWord, page, isFriend].join(' ');
        var cached = Cache.get(cacheKey);
        if(cached != null) {
          callback(0, cached);
          return;
        }

        $http.post("/res", {"private": isFriend, "op":7,"key_word":keyWord, "page": page,  "sort_by": 1,"user":$window.fbtUID}).success(function(data){
          if(data["type"] == 1){
            preHandleRes(data.resource_list);
            Cache.set(cacheKey, data);
            callback(0, data);
          }
          else{
            callback(1, data);
            toast.showErrorToast("搜索失败，请重试");
          }
        });
      }
      else{
        toast.showErrorToast("搜索关键词没有填写或者过长");
      }
    },
    getResByTag: function(tag, page, isFriend, callback){
      tag = tag.split(" ")[0];
      getResByKey(tag, page, isFriend, callback);
    }
  };
});
app.factory("BeDownloading", function($http, toast){
  return{
    getFiles: function(callback){
      $http.get('/beingDownloadedFiles').success(function(data) {
        callback(data)
      });
    }
  }
});
app.service('downloader', function($http, $window, localSocket, toaster, downloadState) {
  //downloadInfo: fileHash, fileSize, fileName, state, isDir, downloadSize, progress,isPause,
  //              fileHashs, fileSizes,curIdx,private,folderInfo, downloadStart
  var that = this;
  this.allDownloads = [];
  this.allDownloadsMap = {};
  $window.downloadFolderName = {};
  this.parseDownloadInfo = function(fileInfo, isPrivateDownload, fileHashs, fileSizes, isHis, isDownloadCb){
    var fileId = gen_file_id(fileInfo["file_hash"], fileInfo["file_size"]);
    var fileNames = {};
    var downloadInfo = {};
    if (fileId in this.allDownloadsMap) {
      if (fileHashs) {
        downloadInfo = this.allDownloads[this.allDownloadsMap[fileId]];
        downloadInfo["fileHashs"].concat(fileHashs);
        downloadInfo["fileSizes"].concat(fileSizes);
        var fileIds = [];
        var hashList = fileHashs.split(",");
        var sizeList = fileSizes.split(",");
        for (var i = 0; i < hashList.length; i++) {
          fileIds.push(gen_file_id(hashList[i], sizeList[i]));
        }
        for (var i = 0; i < fileIds.length; i++) {
          downloadInfo["folderInfo"][fileIds[i]] = {};
          downloadInfo["folderInfo"][fileIds[i]]["complete"] = 0;
          downloadInfo["folderInfo"][fileIds[i]]["fileSize"] = normalizeFileSize(sizeList[i]);
          downloadInfo["folderInfo"][fileIds[i]]["fileName"] = $window.downloadFolderName[fileId][fileIds[i]];
          fileNames[fileIds[i]] = $window.downloadFolderName[fileId][fileIds[i]];
        }
      } else {
        if(!isHis)
          toaster.pop('warning', "系统提示", "无需重复下载", true);
        if(isDownloadCb)
          isDownloadCb();
        return;
      }
    } else {
      if(isHis){
        downloadInfo["downloadStart"] = true;
        downloadInfo["progress"] = fileInfo["progress"];
        if("isContinue" in fileInfo){
          downloadInfo["state"] = downloadState["downloading"];
          downloadInfo["value"] = "已下载"+fileInfo["progress"]+"%";
        }
        if("finish" in fileInfo){
          downloadInfo["state"] = downloadState["downloaded"];
          downloadInfo["progress"] = 100;
          downloadInfo["value"] = "已下完";
        }
      }
      else{
        downloadInfo["downloadStart"] = false;
        downloadInfo["progress"] = 0;
        downloadInfo["state"] = downloadState["queue"];
        downloadInfo["value"] = "排队中";
      }
      downloadInfo["fileHash"] = fileInfo["file_hash"];
      downloadInfo["fileSize"] = fileInfo["file_size"];
      downloadInfo["fileName"] = fileInfo["file_name"];
      downloadInfo["downloadSize"] = 0;      
      downloadInfo["isPause"] = false;
      downloadInfo["private"] = isPrivateDownload;
      if (fileHashs) {
        downloadInfo["isDir"] = true;
        downloadInfo["fileHashs"] = fileHashs;
        downloadInfo["fileSizes"] = fileSizes;
        var fileIds = [];
        var hashList = fileHashs.split(",");
        var sizeList = fileSizes.split(",");
        for (var i = 0; i < hashList.length; i++) {
          fileIds.push(gen_file_id(hashList[i], sizeList[i]));
        }
        downloadInfo["folderInfo"] = {};
        if (fileId in $window.downloadFolderName) {
          for (var i = 0; i < fileIds.length; i++) {
            downloadInfo["folderInfo"][fileIds[i]] = {};
            downloadInfo["folderInfo"][fileIds[i]]["complete"] = 0;
            downloadInfo["folderInfo"][fileIds[i]]["fileSize"] = normalizeFileSize(sizeList[i]);
            downloadInfo["folderInfo"][fileIds[i]]["fileName"] = $window.downloadFolderName[fileId][fileIds[i]];
            fileNames[fileIds[i]] = $window.downloadFolderName[fileId][fileIds[i]];
          }
        }
        downloadInfo["curIdx"] = 0;
      } else {
        downloadInfo["isDir"] = false;
      }
      this.allDownloadsMap[fileId] = this.allDownloads.length;
      this.allDownloads.push(downloadInfo);
    }
    return [fileId, fileNames, downloadInfo];
  };
  this.download = function(){
    if(arguments.length == 2){
      this.doDownload(arguments[0], arguments[1]);
    }
    else if(arguments.length == 3){
      if(typeof(arguments[2])==='function'){
        this.doDownload(arguments[0], arguments[1], null, null, arguments[2]);
      }
      else{
        this.doDownload(arguments[0], arguments[1], null, null, null, arguments[2]);
      }
    }
    else if(arguments.length == 5)
      this.doDownload(arguments[0], arguments[1],arguments[2], arguments[3], null, arguments[4]);
  }
  this.doDownload = function(fileInfo, isPrivateDownload, fileHashs, fileSizes, isDownloadCb, rid) {
    var ret = this.parseDownloadInfo(fileInfo, isPrivateDownload, fileHashs, fileSizes, null, isDownloadCb);
    if(!ret)
      return;
    var downloadInfo = ret[2];
    if(!rid)
      rid = '';
    localSocket.emit('download', JSON.stringify({
      "hasError": 0,
      "fileNames": ret[1],
      "dirName": downloadInfo["fileName"],
      "fileHashs": downloadInfo["fileHashs"],
      "fileSizes": downloadInfo["fileSizes"],
      "size": downloadInfo["fileSize"],
      "type": 0,
      "private": downloadInfo["private"],
      "hash": downloadInfo["fileHash"],
      "html": ret[0],
      "rid": rid
    }));
    toaster.pop('note', "系统通知", "已添加到右下角我的下载", true);
  };
  this.continueDownload = function(idx) {
    var tmp = this.allDownloads[idx];
    var fileId = gen_file_id(tmp["fileHash"], tmp["fileSize"]);
    tmp["state"] = downloadState["queue"];
    tmp["value"] = "正在请求文件下载信息";
    var send = JSON.stringify({
      "continue": 1,
      "hasError": 0,
      "fileNames": {},
      "progress": tmp["progress"],
      "dirName": tmp["fileName"],
      "fileHashs": tmp["fileHashs"],
      "fileSizes": tmp["fileSizes"],
      "size": tmp["fileSize"],
      "type": 0,
      "private": tmp["private"],
      "hash": tmp["fileHash"],
      "html": fileId
    });
    //console.log(send);
    localSocket.emit('download', send);
  };
  this.reDownload = function(idx) {
    var tmp = this.allDownloads[idx];
    var fileId = gen_file_id(tmp["fileHash"], tmp["fileSize"]);
    tmp["state"] = downloadState["queue"];
    var fileNames = {};
    if (tmp["isDir"])
      fileNames = $window.downloadFolderName[fileId];
    localSocket.emit('download', JSON.stringify({
      "hasError": 1,
      "fileNames": fileNames,
      "dirName": tmp["fileName"],
      "fileHashs": tmp["fileHashs"],
      "fileSizes": tmp["fileSizes"],
      "size": tmp["fileSize"],
      "type": 0,
      "private": tmp["private"],
      "hash": tmp["fileHash"],
      "html": fileId
    }));
  };
  this.cancelDownload = function(idx) {
    var tmp = this.allDownloads[idx];
    var fileId = gen_file_id(tmp["fileHash"], tmp["fileSize"]);
    localSocket.emit('cancelFileDownload', JSON.stringify({
      "size": tmp["fileSize"],
      "type": 5,
      "html": fileId,
      "hash": tmp["fileHash"],
      "isDir": tmp["isDir"]
    }));
    delete this.allDownloadsMap[fileId];
    tmp["shouldHide"] = true;
    //this.allDownloads.splice(idx, 1);
    delete $window.downloadFolderName[fileId];
  };
  this.openDir = function(idx) {
    var tmp = this.allDownloads[idx];
    localSocket.emit("open_dir", JSON.stringify({
      "file_hash": tmp["fileHash"]
    }));
  };
  this.viewFolderInfo = function(dirName, dirHash, dirSize, my_uid, callback) {
    var param = {};
    param["dirHash"] = dirHash;
    param["dirSize"] = dirSize;
    if (my_uid != 0)
      param["uid"] = my_uid;
    //console.log(param);
    $http.post('/getDirDetail', param).success(function(data) {
      if (data["type"] == 0) {
        if (data["error"])
          callback(1, data["error"]);
        else
          callback(1, "获取文件夹信息失败，请重试");
      } else {
        var dirId = gen_file_id(dirHash, dirSize);
        var shouldSave = true;
        if (dirId in $window.downloadFolderName)
          shouldSave = false;
        else
          $window.downloadFolderName[dirId] = {};
        var children = [];
        for (var i in data["result"]) {
          var item = data["result"][i];
          var one_file = {};
          one_file['title'] = item["file_name"];
          one_file["key"] = gen_file_id(item["file_hash"], item["file_size"]);
          one_file["file_size"] = normalizeFileSize(item["file_size"]);
          one_file['download_num'] = item["download_num"];
          one_file["online_owners_num"] = item['online_owners_num'];
          one_file['all_owner_num'] = item['all_owner_num'];
          children.push(one_file);
          if (shouldSave)
            $window.downloadFolderName[dirId][one_file["key"]] = item["file_name"];
        }
        var folder = {
          title: dirName,
          folder: true,
          "file_size": dirSize,
          expanded: true,
          children: children
        }
        var fill = [folder];
        callback(0, fill, children.length);
      }
    });
  };
  //////////////////////////////////////////////////////
  localSocket.on('download_error', function(data){
    var downloadInfo = that.allDownloads[that.allDownloadsMap[data]];
    downloadInfo["downloadStart"] = true;
    downloadInfo["state"] = downloadState["error"];
    downloadInfo["value"] = "貌似抽风了，请重试";
  });
  localSocket.on('download_start', function(fileId) {
    var downloadInfo = that.allDownloads[that.allDownloadsMap[fileId]];
    downloadInfo["downloadStart"] = true;
    downloadInfo["value"] = "排队中";
    //TODO show an animation to tell the user the resource is downloading
    //TODO modify the type of the resource to identify the resource shouldn't be download again
  });
  localSocket.on('download', function(data) {
    //console.log("Sock recv");
    //console.log(data);
    var tmp_data;
    try {
      tmp_data = JSON.parse(data);
    } catch (e) {
      toaster.pop('warning', "系统提示", "网络通信出现了一点小问题，请重试", true);
      return;
    }
    data = tmp_data;
    if (data["type"] == 1) {
      var downloadInfo = that.allDownloads[that.allDownloadsMap[data["html"]]];
      downloadInfo["downloadStart"] = true;
      downloadInfo["state"] = downloadState["error"];
      if(data["error"])
        downloadInfo["value"] = data["error"];
      else
        downloadInfo["value"] = "貌似抽风了，请重试";
      //$("#download_file_hash"+data["html"]).removeAttr('download');
    } else if (data["type"] == 2) {
      var downloadInfo = that.allDownloads[that.allDownloadsMap[data["html"]]];
      if(downloadInfo["state"] != downloadState["error"] && downloadInfo["state"] != downloadState["downloaded"]){
        downloadInfo["value"] = data["value"];
        if(data["progress"])
          downloadInfo["progress"] = data["progress"];
      }
    }
  });
  localSocket.on("dir_download_continue", function(data) {
    data = JSON.parse(data);
    var hashList = data["hashList"];
    var sizeList = data["sizeList"];
    var nameList = data["nameList"];
    var fileIds = [];
    for (var i = 0; i < hashList.length; i++) {
      fileIds.push(gen_file_id(hashList[i], sizeList[i]));
    }
    var dirId = data["dirId"];
    var downloadInfo;
    if (dirId in that.allDownloadsMap) {
      downloadInfo = that.allDownloads[that.allDownloadsMap[dirId]]
    } else {
      downloadInfo = {};
    }
    if (!(dirId in $window.downloadFolderName)) {
      $window.downloadFolderName[dirId] = {};
    }
    for (var i = 0; i < fileIds.length; i++) {
      downloadInfo["folderInfo"][fileIds[i]] = {};
      if (i < data["curIndex"])
        downloadInfo["folderInfo"][fileIds[i]]["complete"] = 1;
      else {
        downloadInfo["folderInfo"][fileIds[i]]["complete"] = 0;
      }
      downloadInfo["folderInfo"][fileIds[i]]["fileSize"] = normalizeFileSize(sizeList[i]);
      $window.downloadFolderName[dirId][fileIds[i]] = nameList[fileIds[i]];
      downloadInfo["folderInfo"][fileIds[i]]["fileName"] = $window.downloadFolderName[dirId][fileIds[i]];
    }
    downloadInfo["downloadStart"] = true;
    downloadInfo["value"] = "排队中";
  });
  localSocket.on("download_over", function(data) {
    data = JSON.parse(data);
    var downloadInfo = that.allDownloads[that.allDownloadsMap[data["html"]]];
    if ("name" in data) {
      downloadInfo["progress"] = 100;
      downloadInfo["value"] = "已下完";
      downloadInfo["state"] = downloadState["downloaded"];
      toaster.pop('success', "系统提示", data["name"] + "下载完成", true);
      if ($window.setting["voice"] == 1)
        $("#audio").trigger('play');
    }
  });
  localSocket.on("single_download_progress", function(data) {
    data = JSON.parse(data);
    var dirId = data["dirId"];
    var fileId = data["fileId"];
    var downloadInfo = that.allDownloads[that.allDownloadsMap[dirId]];
    downloadInfo["folderInfo"][fileId]["progress"] = data["progress"];
  });
  localSocket.on("single_download_over", function(data) {
    data = JSON.parse(data);
    var dirId = data["dirId"];
    var downloadInfo = that.allDownloads[that.allDownloadsMap[dirId]];
    downloadInfo["folderInfo"][data["fileId"]]["complete"] = 1;
    downloadInfo["value"] = "正在请求下一个文件的下载信息";
  });
  localSocket.on('his_del', function(data) {
    var tmp_data;
    try {
      tmp_data = JSON.parse(data);
    } catch (e) {
      tmp_data = data;
    }
    data = tmp_data;
    var dirId = data["html"];
    var idx = that.allDownloadsMap[dirId];
    var tmp = that.allDownloads[idx];
    tmp["shouldHide"] = true;
    //that.allDownloads.splice(idx, 1);
  });
  //////////////////////////////////////////////////////
});
app.factory("WinManager", function(localSocket, $window, $modal){
  return{
    open: function(url){
      //localSocket.emit("winopen", url);
      if($window.setting.version > 8)
        localSocket.emit("winopen", url);
      else{
        var win = window.open(url, '_blank' ,'scrollbars=yes,menubar=yes,resizable=yes,toolbar=yes,location=no,status=no');
        win.moveTo(0,0);
        win.resizeTo($window.screen.availWidth, $window.screen.availHeight);
      } 
    },
    openExternal: function(url){
      localSocket.emit("winopenex", url);
    },
    min: function(){
      localSocket.emit('winmin');
    },
    max: function(){
      localSocket.emit('winmax');
    },
    close: function(){
      if(!($window.setting.platform == "win32" && $window.setting.tray == 1))
        $modal.open({
          backdrop: false, 
          keyboard: false,
          animation: true,
          templateUrl: 'closeModal.html',
          controller: 'closeController',
        });
      else
        localSocket.emit('winclose');
    }
  }
});
app.factory('safeApply', function($rootScope) {
  return function(scope, fn) {
      var phase = scope.$root.$$phase;
      if (phase == '$apply' || phase == '$digest') {
          if (fn && ( typeof (fn) === 'function')) {
              fn();
          }
      } else {
          scope.$apply(fn);
      }
  }
});
app.factory('Subheader', function() {
  var index = -1;
  var tab = null;
  //{0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其它"}
  var tabMapper = {
    '全部':-1,
    '电影':0,
    '剧集':1,
    '学习':2,
    '音乐':3,
    '动漫':4,
    '游戏':5,
    '综艺':6,
    '体育':7,
    '软件':8,
    '其它':9,
    '':-1,
    'movie':0,
    'episode':1,
    'study':2,
    'music':3,
    'cartoon':4,
    'game':5,
    'variety':6,
    'sport':7,
    'software':8,
    'other':9
  };
  return {
    setIndex: function(i) {
      tab = i;
      index = tabMapper[i] ? tabMapper[i] : -1;
    },
    getIndex: function() {
      return index; 
    },
    getTab: function() {
      return tab;
    },
    getIndexByTab: function(tab) {
      return tabMapper[tab];
    },
    getTabByIndex: function(index) {
      for(var k in tabMapper) {
        if(k.match(/[a-zA-Z]/) != null && tabMapper[k] == index)
          return k;
      }
      return null;
    }
  };
});
app.factory('ResType', function() {
  var index = 0;
  var allTabs = ["电影", "剧集", "学习", "音乐", "动漫", "游戏", "综艺", "体育", "软件", "其它"];
  var idxMapper = {0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其它"};
  var tabMapper = {
    '请选择类别':-1,
    '电影':0,
    '剧集':1,
    '学习':2,
    '音乐':3,
    '动漫':4,
    '游戏':5,
    '综艺':6,
    '体育':7,
    '软件':8,
    '其它':9
  };
  var subIdx = {
    "标清(默认)":"0",
    "高清":"1",
    "超清":"2"
  };
  return {
    getSubIdx: function(t){
      return subIdx[t];
    },
    getTabIdx: function(t){
      return tabMapper[t];
    },
    setIndex: function(idx){
      if(index != idx)
        index = idx;
    },
    getIndex: function() {
      return index; 
    },
    getTab: function(){
      return idxMapper[index]; 
    },
    getTabByIndex: function(idx){
      return idxMapper[idx]; 
    },
    getAllTabs: function(){
      return allTabs;
    }
  };
});
app.factory('Tag', function() {
  var typeMapper = {
    '请选择类别': [],
    '剧集': ['喜剧', '古装', '伦理', '武侠', '纪录片', '玄幻', '冒险', '警匪', '军事', '神话', '科幻', '搞笑', '偶像', '悬疑', '历史', '儿童', '都市', '家庭', '言情'],
    '电影': ['喜剧', '古装', '伦理', '恐怖', '纪录片', '爱情', '动作', '科幻', '武侠', '战争', '犯罪', '惊悚', '剧情', '玄幻', '冒险', '动画'],
    '音乐': ['流行','摇滚','舞曲','电子','HIP-HOP','乡村','民族','古典','音乐剧','轻音乐'],
    '动漫': ['热血','恋爱','搞笑','LOLI','神魔','科幻','真人','美少女','运动','亲子','励志','剧情','校园','历史'],
    '游戏': ['动作','冒险','模拟','角色扮演','休闲','视频','其它'],
    '综艺': ['晚会','生活','访谈','音乐','游戏','旅游','真人秀','美食','益智','搞笑','纪实','汽车'],
    '体育': ['篮球','足球','台球','羽毛球','乒乓球','田径','水上项目','体操','其它'],
    '软件': ['系统','应用','管理','行业','安全防护','多媒体','网络软件','教学方面','即时通讯','娱乐','图形处理','编程'],
    '其它': ['其它'],
    '学习': ['课后作业和答案','课堂笔记','往届考题','电子书或视频等辅助资料','课程课件','课程资料合集','学习心得','TED','百家讲坛','软件教学','其它']
  };

  return {
    getIdx: function(t){
      return Object.keys(typeMapper).indexOf(t);
    },
    getByType: function(type) {
      var tags = ['请选择标签'];
      tags = tags.concat(typeMapper[type]);
      return tags;
    },
  };
});
app.factory('fileDialog', [function(){
  var callDialog = function(dialog, callback) {
    dialog.addEventListener('change', function() {
      var result = [dialog.files[0], dialog.value];
      callback(result);
    }, false);
    dialog.click();
  };

  var dialogs = {};
  
  dialogs.saveAs = function(callback, defaultFilename, acceptTypes) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    dialog.nwsaveas = defaultFilename || '';
    if (angular.isArray(acceptTypes)) {
      dialog.accept = acceptTypes.join(',');
    } else if (angular.isString(acceptTypes)) {
      dialog.accept = acceptTypes;
    }
    callDialog(dialog, callback);
  };
  
  dialogs.openFile = function(callback, multiple, acceptTypes) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    if (multiple === true) {
      dialog.multiple = 'multiple';
    }
    if (angular.isArray(acceptTypes)) {
      dialog.accept = acceptTypes.join(',');
    } else if (angular.isString(acceptTypes)) {
      dialog.accept = acceptTypes;
    }
    callDialog(dialog, callback);
  };
  
  dialogs.openDir = function(callback) {
    var dialog = document.createElement('input');
    dialog.type = 'file';
    dialog.nwdirectory = 'nwdirectory';
    callDialog(dialog, callback);
  };
  
  return dialogs;
}]);

app.factory('Rate', function($http, toast){
  return {
    rate: function(fileHash, score, fileSize, fileName){
      $http.post("/res", {"op":6,"fileHash":fileHash,"score": score, "size":fileSize, "rname": fileName}).success(function(data){
        if(data["type"] == 0)
          toast.showErrorToast("评分失败，请重试");
        else
          toast.showSuccessToast("评分成功");
      });
    }
  }
});

app.factory('InformBad', function($http, toast, $window){
  return {
    inform: function(fileHash, fileSize){
      $http.get('/inform?uid='+$window.fbtUID+"&file_hash="+fileHash+"&size="+fileSize).success(function(data) {
        if(data["type"] == 0)
          toast.showErrorToast("举报失败，请重试");
        else
          toast.showSuccessToast("您的举报信息已提交，我们将及时处理。");
      });
    }
  }
});

app.factory('Comment', function($http, toast){
  return {
    getComment: function(fileHash, fileSize, time, callback){
      $http.get("/comment?op=0&hash="+fileHash+"&size="+fileSize+"&time="+time).success(function(data){
        if(data["type"] == 0){
          toast.showErrorToast("获取评论失败，请重试");
        }
        else{
          //{rid, rname, uid, uname, uicon, comment, ctime}
          //console.log(data);
          for(var i = 0; i < data["result"].length; i++){
            data["result"][i]["comment"] = waveDecrypt(data["result"][i]["comment"]);
          }
          callback(0, data["result"]);
        }
      }).error(function(){
        callback(1);
        toast.showErrorToast("获取评论失败，请重试");
      });
    },
    postComment: function(fileHash, fileSize, fileName, content, callback){
      content = htmlencode(content);
      $http.get("/comment?op=1&hash="+fileHash+"&size="+fileSize+"&comment="+content+"&rname="+fileName).success(function(data){
        if(data["type"] == 0){
          toast.showErrorToast("评论失败，请重试");
        }
        else{
          toast.showSuccessToast("评论成功");
          callback();
        }
      }).error(function(){
        toast.showErrorToast("评论失败，请重试");
      });
    }
  }
});

app.factory('Feed', function($http, toast){
  return {
    getFeed: function(time, page, callback){
      $http.get("/feed?time="+time+"&page="+page).success(function(data){
        console.log(data);
        if(data["type"] == 0){
          callback(1);
          toast.showErrorToast("获取动态失败，请重试");
        }
        else{
          //{fid, rid, rname, uid, type, content, ctime, icon, nick_name, link, desc}
          //暂时动态的显示是：头像+nick_name+type+rname, link和desc只有上传动作才有，且从豆瓣拿到数据才有
          //其他时候都是空
          callback(0, data["result"]);
        }
      }).error(function(){
        callback(1);
        toast.showErrorToast("获取动态失败，请重试");
      });
    }
  }
});

app.factory('OneRes', function($http, toast){
  return {
    getRes: function(fileId, callback){
      $http.get("/get_file_info?fileId="+fileId).success(function(data){
        if(data["type"] == 0){
          toast.showErrorToast("获取文件信息失败，请重试");
        }
        else if(data['result']){
          var tmp = [data["result"]];
          preHandleRes(tmp);
          callback(0, tmp[0]);
        }
        else {
          callback(1);
          toast.showErrorToast("获取文件信息失败，请重试");
        }
      }).error(function(){
        callback(1);
        toast.showErrorToast("获取文件信息失败，请重试");
      });
    }
  }
});

app.factory('Summary', function($http, toast){
  return {
    getSummaryById: function(fileId, callback){
      $http.get("/get_summary?fileId="+fileId).success(function(data){
        if(data["type"] == 1 && data['result']){
          callback(0, data['result']);
        }
        else {
          callback(0, "");
        }
      }).error(function(){
        callback(0, "");
      });
    }
  }
});

app.factory('Message', function($http, $window, toast){
  return {
    //to_who：昵称，content：内容
    sendMsg: function(to_who, content, callback){
      $http.post("/send_msg", {"content": $window.nick_name+"说："+content, "to": to_who}).success(function(data){
        if(data["type"] == 1){
          callback(0);
        }
        else{
          callback(1);
        }
      });
    }
  }
});

app.factory('Cache', function($window) {
  var capacity = 200;
  var expire = 30*60*1000;//ms
  var cache = null;

  var clone = function(object) {
    return JSON.parse(JSON.stringify(object));
  };
  var push_item = function(key, value) {
    cache[key] = {
      data: clone(value),
      time: new Date()
    }
  };
  var get_item = function(key) {
    return key in cache ? clone(cache[key].data) : null;
  };
  var pop_item = function() {
    var key = null;
    var time = new Date();
    for(var k in cache) {
      if(cache[k].time <= time) {
        time = cache[k].time;
        key = k;
      }
    }
    delete cache[key];
  };

  var refresh = function() {
    if(!$window.FBTCache)
      $window.FBTCache = {};
    cache = $window.FBTCache;

    var trash = [];
    var now = new Date();
    for(var k in cache) {
      if(now - cache[k].time >= expire) {
        trash.push(k);
      }
    }
    trash.forEach(function(k) {
      delete cache[k];
    });


    while(Object.keys(cache) >= capacity) {
      pop_item();
    }
  };
  return {
    get: function(key) {
      refresh();
      return get_item(key);
    },
    set: function(key, value) {
      refresh();
      push_item(key, value);
    }
  }
});

app.factory('Adv', function($http, $rootScope){
  this.image = '';
  this.title = '';
  this.source = '';
  var that = this;
  return {
    init: function(){
      $http.get("/ad").success(function(data) {
        if(data["type"] == 1)
        {
          var result = data["result"];
          $rootScope.$broadcast('update-adv', {
            image : result.image,
            title : result.title,
            source : result.source
          });
        }
      }).error(
        function(data){
          console.log(data);
        }
      );
    },
    image: this.image,
    title: this.title,
    source: this.source
  };
});
