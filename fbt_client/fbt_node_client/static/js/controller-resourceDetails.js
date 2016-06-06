/* vim: set sw=2 ts=2 : */
'use strict';

app.controller('ResourceDetailsController', function($scope, $rootScope, $routeParams, $route, star, toast, Comment, Rate, downloader, $modal, $window, InformBad, WinManager, Summary, $timeout, $location, share, Message) {
  $scope.currentCommentPage = 1;
  $scope.resource = $routeParams.resource;
  $scope.isPrivate = $routeParams.isPrivate;
  $scope.isMy = $routeParams.isMy;
  $scope.returnUrl = $routeParams.returnUrl;
  $scope.searchUrl = $routeParams.searchUrl;

  console.log($scope.returnUrl)
  if($scope.returnUrl) {
    $timeout(function() {
      $('.quick-nav a').first().text('个人中心').attr('href', '#' + $scope.returnUrl);
    });
    if($scope.returnUrl.match('/myspace') != null
      || $scope.returnUrl.match('/friend_res') != null)
      $rootScope.$broadcast('refreshSubheaderEvent', '/home');
  }
  if($scope.searchUrl) {
    $timeout(function() {
      $('.quick-nav a').first().text('资源检索').attr('href', '#' + $scope.searchUrl);
    });
  }

  Comment.getComment(
    $scope.resource.file_hash,
    $scope.resource.file_size,
    $scope.comments && $scope.comments.length ? $scope.comments.slice(-1)[0].ctime : 1,
    /*$scope.currentCommentPage,*/
    function(error, data) {
    $scope.comments = data;
  });

  if($scope.resource.ext_info && $scope.resource.ext_info.summary)
    Summary.getSummaryById($scope.resource.file_id, function(err, summary) {
      if(!err)
        $scope.summary = summary;
    });

  //star.render(Math.ceil($scope.resource.avg_grade/2), 5, 'details', function(score) {
  star.render(0, 5, 'details', function(score) {
    Rate.rate($scope.resource.file_hash, score, $scope.resource.file_size, $scope.resource.file_name);
  });

  $scope.publishCommentClickHandler = function(comment) {
    if (comment.trim().length) {
      Comment.postComment($scope.resource.file_hash, $scope.resource.file_size, $scope.resource.file_name, comment, function() {
        $route.reload();
      });
    }
  };

  $scope.viewMoreCommentClickHandler = function() {
    $scope.currentCommentPage += 1;
    Comment.getComment(
      $scope.resource.file_hash,
      $scope.resource.file_size,
      $scope.comments && $scope.comments.length ? $scope.comments.slice(-1)[0].ctime : 1,
      /*$scope.currentCommentPage, */
      function(error, data) {
      if (!data.length)
        toast.showNoticeToast('没有更多评论啦');
      else
        $scope.comments = $scope.comments.concat(data);
    });
  };

  $scope.downloadResourceClickHandler = function() {
    var tmp_resource_list = [$scope.resource];
    preHandleRes(tmp_resource_list);

    if (tmp_resource_list[0].isDir) {
      $scope.curRes = tmp_resource_list;
      $modal.open({
        backdrop: false, 
        keyboard: false,
        animation: true,
        templateUrl: 'folderModal.html',
        controller: 'folderModalCtrl',
        scope: $scope,
        resolve: {
          index: function () {
            return 0;
          },  
          canDownload: function(){
            return true;
          },
          rid: function(){
            return '';
          }   
        }   
      });   
    }
    else {
      $modal.open({
        backdrop: false,
        keyboard: false,
        animation: true,
        templateUrl: 'downloadModal.html',
        controller: 'downloadModalCtrl'
      });
      downloader.download($scope.resource, $scope.isPrivate);
    }
  };

  $scope.showDouban = function(file_name) { 
    var nameIndex = file_name.lastIndexOf('.') == -1?file_name.length:file_name.lastIndexOf('.');
    var name = file_name.substring(0,nameIndex);
    WinManager.open('http://www.douban.com/search?q=' + name);
  };     

  $scope.sendMessage = function(owner) { 
    $scope.to_who = owner;
    $modal.open({
      backdrop: false,
      keyboard: false,
      animation: true,
      templateUrl: 'messageModal.html',
      scope: $scope,
      controller: 'messageModalCtrl'
    });
  };

  $scope.informBad = function(resource) {
    InformBad.inform(resource.file_hash, resource.file_size);
  };

  $scope.returnLastPage = function() {
    $('.quick-nav a').last().prev().click();
  };

  $timeout(function() {
    $scope.height = $('.details-info').height() + 'px';
  });

  /*
  window.baiduShare = {
    file_name: $scope.resource.file_name,
    fbtUID: $window.fbtUID,
    link: 'http://fbt-image.b0.upaiyun.com' + $scope.resource.link
  };
  */
  //TODO
  $scope.shareResourceClickHandler = function() {
    //$('#baidu-share a').first()[0].click()
    share.show({
      title: '后六维时代,资源下载哪家强？',
      desc: '小伙伴们，我刚用FBT下载了“' + $scope.resource.file_name + '”！' +
        'FBT，是北大清华中科院小伙伴联合开发的校内影视、学习资源分享平台，免流量神速下载，最高可到20M/s，百度一下FBT。',
      url: 'http://www.friendsbt.com/?uid=' + $window.fbtUID + '&file_id=' + $scope.resource.file_id,
      weixin: 'http://weixin.qq.com/r/MXULEy7E-XOCrWpw9yAj',
      image: 'http://fbt-image.b0.upaiyun.com' + $scope.resource.link
    });
  };
});

app.controller("messageModalCtrl", function($scope, $modalInstance, Message, toast) {
  $scope.close = function(){
    $modalInstance.dismiss('cancel');
  };
  $scope.send = function(flag, content) {
    $modalInstance.dismiss('cancel');
    if (flag == 0) {
      return;
    }

    Message.sendMsg($scope.to_who, content, function(err) {
      if (err)
        return toast.showNoticeToast('发送失败，请稍后重试~');
      return toast.showNoticeToast('已经发送给小伙伴啦~');
    });
  }
});
