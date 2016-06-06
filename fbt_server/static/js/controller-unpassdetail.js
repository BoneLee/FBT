app.controller('unpassDetailController', ['$scope', '$routeParams', '$http', '$window', '$location', '$timeout', 'toaster', 'classSrv', 'universityCollegeSrv', function($scope, $routeParams, $http, $window, $location, $timeout, toaster, classSrv, universityCollegeSrv) {
	$scope.normalizeFileSize = function(filesize) {
		return normalizeFileSize(filesize); //定义在utils.js中
	};
	$scope.isCurrentOrder = function(order) {
	  return order == $scope.show_order;
	};

	$scope.universityClickHandler = function() {
	  $scope.show_order = 1;
	};

	$scope.chooseProvince = function(province) {
	  universityCollegeSrv.fetchUniversities(province);
	  $scope.show_order = 2;
	};

	$scope.chooseUniversity = function(university) {
	  $scope.formdata.university = university;
	  $scope.formdata.college = "";
	  universityCollegeSrv.fetchColleges(university);
	  $scope.show_order = 3;
	};

	$scope.chooseCollege = function(college) {
	  $scope.formdata.college = college;
	  $scope.show_order = 0;
	};

	$scope.collegeClickHandler = function() {
	  var currentUniversity = $scope.formdata.university;
	  if (currentUniversity) {
	    universityCollegeSrv.fetchColleges(currentUniversity);
	    $scope.show_order = 3;
	  }
	};

	$scope.getCourses = function() {
	    if (!($scope.formdata.university && $scope.formdata.college)) return;
	    $http({
	      url: '/course/list',
	      method: 'GET',
	      params: {
	        university: $scope.formdata.university,
	        college: $scope.formdata.college
	      }
	    })
	    .success(function(response) {
	        $scope.courses = response.err ? [] : response.course_list;
	    })
	    .error(function(data, status, headers, config) {
	      // 失败处理
	      alert('加载失败，请重试！')
	    });
	  };

	$scope.init = function () {
		$scope.show_order = 0; // 0 for no selector, 1 for province, 2 for university, 3 for college
		$scope.prov_list = universityCollegeSrv.getProvList();
		$scope.universities = universityCollegeSrv.getUniversities();
		$scope.colleges = universityCollegeSrv.getColleges();
		$scope.courses = [];

		$scope.details_info = angular.fromJson($routeParams.str);
		$scope.refer_url = $routeParams.url; //取三个参数用来跳转到前一页面
		$scope.refer_page_num = $routeParams.page_num;
		$scope.refer_r_type = $routeParams.r_type;


		$scope.tags = resourceTags; //定义在uploaderController中
		$scope.formdata = {};


		$scope.formdata.file_id = $scope.details_info.file_id;
		$scope.formdata.resource_name = $scope.details_info.resource_name;
		$scope.formdata.university = $scope.details_info.university;
		$scope.formdata.college = $scope.details_info.college;
		$scope.formdata.teacher = $scope.details_info.teacher;
		$scope.formdata.course = $scope.details_info.course;
		$scope.formdata.description = $scope.details_info.description;
		$scope.formdata.tag = $scope.details_info.tag;
	};

	$scope.updateResInfo = function() {
		if ($scope.changeInfoForm.$valid) {
			var req = {
				method: 'POST',
				url: "/change_upload",
				timeout: 10000,
				headers: {
					"X-CSRFToken": getCookie("_xsrf"),
				},
				data: $scope.formdata,
			};

			$http(req).success(function(data, status, headers, config) {
				//回调成功
				var r = angular.fromJson(data);
				if (r.err == 0) {

					toaster.pop('success', '资源信息已更改,感谢您的分享!', '资源通过审核后，您将获得F币奖励！', true);

				} else if (r.err == 1) {


					toaster.pop('error', '系统提示', '未经授权上传！', false);

				} else if (r.err == 2) {

					toaster.pop('error', '系统提示', '上传表单参数不正确,请在上传表单中更正后点击重试按钮！', false);

				}

			}).error(function(data, status, headers, config) {
				//回调失败
				if (status == 500) {
					//500服务器内部错误

					toaster.pop('error', '系统提示', '服务器处理失败,请点击重试按钮！', false);

				} else if (status == 408) {
					//请求超时

					toaster.pop('error', '系统提示', '请求超时,请点击重试！', false);

				}
			});

		} else {
			toaster.pop('error', '系统提示', '上传表单未通过验证，请修改后再上传！', false);
		}



	}

	$scope.removeRes = function() {
		var confirm = $window.confirm("此操作不可恢复，确定删除？");
		if (confirm) {
			var req = {
				method: 'POST',
				url: "/resource/remove",
				timeout: 10000,
				headers: {
					"X-CSRFToken": getCookie("_xsrf"),
				},
				data: [$scope.details_info.file_id],
			};


			$http(req).success(function(data, status, headers, config) {
				data = angular.fromJson(data);
				if (data.err == 0) {
					alert("资源删除成功,3秒后跳转到前一页面");
					$timeout(function() {
						$location.path($scope.refer_url).search({
							r_type: $scope.refer_r_type,
							page_num: $scope.refer_page_num
						});
					}, 3000);

					// setTimeout()
				} else if (data.err == 1) {
					alert("未经授权操作！");
				}

			}).error(function(data, status, headers, config) {
				alert("资源删除失败");
			})
		} else {
			//点取消了什么都不做
		}
	};
}]);