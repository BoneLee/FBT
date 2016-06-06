app.controller('FriendSpaceController', function($scope, $location, FriendSpace, $rootScope, $window, AllFriend){
    $scope.isMy = false;
    var s = $location.search();
    var return_url = s["return_url"];
    if($window.parseInt(s["public"]) == 0 || s["uid"]+'' in AllFriend.friendsUids)
    	$scope.sideMenus = [
    	  	{"title":"好友资源", "url": "partials/spacePartials/resource.html"},
    	  	{"title":"好友信息", "url": "partials/friendPerson.html"}
    	];
    else
        $scope.sideMenus = [
            {"title":"好友资源", "url": "partials/spacePartials/resource.html"}
        ];

    $scope.idx = 0;
	$scope.spaceTemplate = "partials/spacePartials/resource.html";
    //$scope.selected = $scope.sideMenus[idx];
    $scope.loadPage = function (menu, index) {
        //$scope.selected = menu;
        $(".myspace .space_sidemenu_wrap .active").removeClass('active');
        $($(".myspace .space_sidemenu_wrap li")[index]).addClass('active')
        $scope.spaceTemplate = menu.url;
    };

	$scope.info = {};
	FriendSpace.getInfo(s["uid"], s["public"], function(data){
	  $scope.shuo = data["shuo"];
      $scope.info.resSize = data["size"];
      $scope.user = data["user"];
      if($window.parseInt($scope.user["gender"]) == 0)
        $scope.user["gender"] = "女";
      else
        $scope.user["gender"] = "男";
	});
    
    $scope.viewResourceDetailClickHandler = function(resource, isMy) {
      $location.path('/home/details/').search({'resource':resource, 'isMy':isMy});
    };

    $scope.goHome = function() {
        if(return_url == "home"){
          $location.path('/home');
          $rootScope.$broadcast('refreshSubheaderEvent', $location.url().replace(/\?.+/, '').split('-').splice(-1)[0]);
        }
        else{
          $location.path('/'+return_url);
        }
    };
});
app.controller('FriendInfoController', function($scope){
	$scope.friendinfo = $scope.$parent.user;
});
