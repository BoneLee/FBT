app.controller('testCtrl', function($scope, $window, AllRes, Rate, Comment, Feed, OneRes){
	$scope.print = function(msg){
		$window.console.log(msg);
	}
	$scope.init = function(data){
		if(data["type"] && data["type"] == 1)
        {
          var res = data["resource_list"];
          //Rate.rate(res[0]["file_hash"], 4, res[0]["file_size"], res[0]["file_name"]);
          $scope.print(res[0]["file_hash"]);

          //Comment.postComment(res[0]["file_hash"], res[0]["file_size"], res[0]["file_name"], "test haha");
          Comment.getComment(res[0]["file_hash"], res[0]["file_size"], 1, function(err, data){
          	if(err)
          		$scope.print("comment error");
          	else{
          		$scope.print(data);
          	}
          });

          /*Feed.getFeed(1, function(err, data){
          	if(err)
          		$scope.print("feed error");
          	else{
          		$scope.print(data);
          	}
          });

          OneRes.getRes(res[0]["file_hash"]+"_"+res[0]["file_size"], function(err, data){
          	if(err)
          		$scope.print("feed error");
          	else{
          		$scope.print(data);
          	}
          });*/
        }
        else{
          $scope.print(data);
          $scope.print("error");
        }
	}
	AllRes.getAllRes(1, 1, 0, $scope.init);
});