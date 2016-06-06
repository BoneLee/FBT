var upload_html = {
  "请选择类别": "",
  "剧集": '<div><input style="margin-left:15px;margin-right: 18px;" class="col-xs-9" id="resourceName" type="text" value="" placeholder="请填写剧集资源名称，如“吸血鬼日记”"/>'+
          '<input class="col-xs-2" id="resourceNum" type="text" value="" placeholder="集数"/></div>' +
          '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
          '<span class="glyphicon glyphicon-edit" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></span></div>',
  "电影": '<div><input style="margin-left: 15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写电影资源名称，如“星际穿越”" /></div>' +
          '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
          '<span class="glyphicon glyphicon-edit" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></span></div>',
  "音乐": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写音乐资源名称，如“青花瓷”"/>'+
          '<input class="col-xs-3" style="margin-right: 5px;" id="resourceArt" type="text" value="" placeholder="音乐家"/>'+
          '<input class="col-xs-2" id="resourceAlbum" type="text" value="" placeholder="专辑名"/></div>',
  "动漫": '<div><input style="margin-left:15px;margin-right: 18px;" class="col-xs-9" id="resourceName" type="text" value="" placeholder="请填写动漫资源名称，如“海贼王”"/>'+
          '<input class="col-xs-2" id="resourceNum" type="text" value="" placeholder="集数"/></div>' +
          '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
          '<span class="glyphicon glyphicon-edit" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></span></div>',
  "游戏": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写游戏资源名称，如“实况足球”"/>'+
          '<input class="col-xs-3" style="margin-right: 5px;" id="resourceEnName" type="text" value="" placeholder="英文名"/>'+
          '<input class="col-xs-2" id="resourceVersion" type="text" value="" placeholder="版本号"/></div>',
  "综艺": '<div><input style="margin-left:15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写综艺资源名称，如“爸爸去哪儿”"/></div>' +
          '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
          '<span class="glyphicon glyphicon-edit" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></span></div>',
  "体育": '<div><input style="margin-left:15px;margin-right: 15px;" class="col-xs-8" id="resourceName" type="text" value="" placeholder="请填写体育资源名称"/>'+
          '<input class="col-xs-3" id="resourceDay" type="text" value="" placeholder="日期"/></div>' +
          '<div><input style="margin-left:15px;width: 86%;margin-right: 22px;" class="col-xs-9" id="resourceEnName" type="text" value="" placeholder="0day英文名/版本信息(显示为资源副标题),点击右侧按钮提取文件名"/>' +
          '<span class="glyphicon glyphicon-edit" style="margin-top: 2px;font-size: 32px;cursor:pointer" onclick="getFilename();" title="提取文件名"></span></div>',
  "软件": '<div><input style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写软件资源名称，如“会声会影”"/>'+
          '<input class="col-xs-3" style="margin-right: 5px;" id="resourcePlantform" type="text" value="" placeholder="平台"/>'+
          '<input class="col-xs-2" id="resourceVersion" type="text" value="" placeholder="版本号"/></div>',
  "其它": '<div><input style="margin-left:15px;width: 95%;" id="resourceName" type="text" value="" placeholder="请填写一个中文名或者纯英文名" /></div>',
  "学习": '<div><input data="0" style="margin-left:15px;margin-right: 11px;" class="col-xs-6" id="resourceName" type="text" value="" placeholder="请填写一个中文名称"/>'+
          '<input data="1" class="col-xs-3" style="margin-right: 5px;" id="resourceCourse" type="text" value="" placeholder="课程名"/>'+
          '<input data="1" class="col-xs-2" id="resourceTeacher" type="text" value="" placeholder="授课老师"/></div>'+
          '<div><input data="1" style="margin-left:15px;margin-right: 18px;" class="col-xs-8" id="resourceSchool" type="text" value="" placeholder="资源所属学校名"/>'+
          '<input data="1" class="col-xs-3" id="resourceAcademy" type="text" value="" placeholder="资源所属院系名"/></div>'
};
function getFilename() {
    var filePath;
    var val = window.fileSel;
    if(val == "1"){
        filePath=$('#resourceFile').val();
    }
    else{
        filePath=$('#resourceDir').val();
    }

    if (!filePath) {
        showNoticeToast("请选择分享的文件，便于为您提取0day命名");
        return;
    }
    var idx1 = filePath.lastIndexOf('/') + 1;
    var idx2 = filePath.lastIndexOf('\\') + 1;
    idx1 = idx1 > idx2 ? idx1 : idx2;
    if (idx1 < 0) idx1 = 0;
    var filename = filePath.substring(idx1);
    $('#resourceEnName').empty();
    $('#resourceEnName').val(filename);
    var chEng = lenOfChAndEng(filename);
    if (chEng[0] > 0) {
        showStickyNoticeToast("资源0day命名含有中文字符，请检查是否正确");
    }
}
//download part
//type 0 is download, 1 is error, 2 is action, 3 is pause, 4 is resume, 5 is cancel
//6 is cancel callback
//action 0 is html, 1 is inc, 2 is append, 3 is css, 4 is attr
function action(obj, act, val){
  if(act == 0){
    $(obj).html(val);
  }
  else if(act == 1){
    $(obj).text(window.parseInt($(obj).text())+1);
  }
  else if(act == 2){
    $(obj).append(val);
  }
  else if(act == 3){
    $(obj).css(val);
  } 
  else if(act == 4){
    $(obj).attr(val);
  } 
}
function downloadFile(forceDownload, dirName,fileHashs,fileSizes,size,flag,fileHash,isPrivateDownload,isContinue,progress) {
  var whichHtmlElement = fileHash+flag.trim()+size;
  var obj = $("#download_file_hash"+whichHtmlElement);
  if((!obj[0].hasAttribute('error') || parseInt(obj.attr('error')) != 1) && $("#collapseMyDownload"+whichHtmlElement).is(':hidden'))
    handleComment(fileHash,3,flag,size);
  if(!forceDownload){
    if(parseInt(obj.attr("data")) == 1 && (!obj[0].hasAttribute('error') || parseInt(obj.attr('error')) != 1)){
      if(fileHashs)
        viewFolderDownload(dirName, gen_file_id(fileHash,size));
      return;
    }
    if(!obj.attr('error') && !isContinue && !obj.attr("download") && $("#container_download_resources").children("#item"+fileHash).length > 0)
    {
      showWarningToast("此资源不需要重复下载。");
      $('#download_progress' + whichHtmlElement).html("无需重复下载");
      return;
    }
  }
  var hasError = obj.attr('error') ? 1 : 0;
  var fileNames = {};
  if(!isContinue && fileHashs){
    var fileIds = [];
    var hashList = fileHashs.split(",");
    var sizeList = fileSizes.split(",");
    for (var i = 0; i < hashList.length; i++) {
      fileIds.push(gen_file_id(hashList[i], sizeList[i]));
    }
    var dirId = gen_file_id(fileHash,size);
    if(!(dirId in window.downloadFolder)){
      window.downloadFolder[dirId] = {};
      //window.downloadFolderFlag[dirId] = {};
    }
    //window.downloadFolderFlag[dirId]["canShow"] = false;
    for (var i = 0; i < fileIds.length; i++) {
      window.downloadFolder[dirId][fileIds[i]] = {};
      window.downloadFolder[dirId][fileIds[i]]["complete"] = 0;
      window.downloadFolder[dirId][fileIds[i]]["fileSize"] = normalizeFileSize(sizeList[i]);
      window.downloadFolder[dirId][fileIds[i]]["fileName"] = window.downloadFolderName[dirId][fileIds[i]];     
    }
    fileNames = window.downloadFolderName[dirId];
    //console.log(window.downloadFolder);
    //getFileName(dirId, fileIds);
  }
/*  if(window.isFirst != 1)
    
  else
    window.isFirst = 1;*/
  obj.attr("data", "1");
  obj.attr('error','1').removeAttr('error');
  $("#paused"+whichHtmlElement).text(0);
  var btn_pause = $("#button_pause_download"+whichHtmlElement);
  if(btn_pause.hasClass('glyphicon-play'))
    btn_pause.removeClass('glyphicon-play').addClass('glyphicon-pause');
  /*if(!window.state_html[fileHash+""])
  {
    window.state_html[fileHash+""] = $("#collapseMyDownload"+whichHtmlElement).html();
  }
  else{
    $("#collapseMyDownload"+whichHtmlElement).html(window.state_html[fileHash+""]);
  }*/
  console.log("Sock have created , send");
  if(isContinue)
    window.socket.emit('download', JSON.stringify({"continue":isContinue,"hasError":hasError,"fileNames":fileNames,"dirName":dirName,"fileHashs":fileHashs,"fileSizes":fileSizes,"size":size,"progress":progress,"type":0,"private": isPrivateDownload,"hash":fileHash, "html":whichHtmlElement}));
  else if(obj.attr("download"))
    window.socket.emit('download', JSON.stringify({"hasError":hasError,"fileNames":fileNames,"dirName":dirName,"fileHashs":fileHashs,"fileSizes":fileSizes,"size":size,"progress":0,"type":0,"private": isPrivateDownload,"hash":fileHash, "html":whichHtmlElement}));
  else
    window.socket.emit('download', JSON.stringify({"hasError":hasError,"fileNames":fileNames,"dirName":dirName,"fileHashs":fileHashs,"fileSizes":fileSizes,"size":size,"type":0,"private": isPrivateDownload,"hash":fileHash, "html":whichHtmlElement}));
}
function download(which){
  $("#download_file_hash"+which).click();
}
function pauseFileDownload(fileHash,size,isDir) {
  console.log("pauseFileDownload");
  window.socket.emit('pauseFileDownload', JSON.stringify({"size":size,"type":3, "hash":fileHash,"isDir":isDir}));
}

function resumeFileDownload(fileHash,size,isDir) {
  console.log("resumeFileDownload");
  window.socket.emit('resumeFileDownload', JSON.stringify({"size":size,"type":4, "hash":fileHash,"isDir":isDir}));
}

function cancelFileDownload(fileHash,flag,size,isDir) {
  var whichHtmlElement = fileHash+flag.trim()+size;
  handleDelHis(whichHtmlElement, fileHash, size);
  console.log("cancelFileDownload");
  window.socket.emit('cancelFileDownload', JSON.stringify({"size":size,"type":5, "html":whichHtmlElement ,"hash":fileHash,"isDir":isDir}));
}
function pause(th){
  if(th.className == 'glyphicon glyphicon-play'){
  th.className = 'glyphicon glyphicon-pause';
  }else{
  th.className = 'glyphicon glyphicon-play';
  }
}
function handleComment(fileHash,flag,f,size){
  //console.log(fileHash);
  if(flag == 4){
    $.get('/inform?uid='+window.fbtUID+"&file_hash="+fileHash+"&size="+size, function(data) {
      /*optional stuff to do after success */
      var tmp;
      try{
        tmp = JSON.parse(data);
      }
      catch(e){
        tmp = data;
      }
      if(tmp["type"] == 0)
        showErrorToast("举报失败，请重试");
      else
        showSuccessToast("您的举报信息已提交，我们将及时处理。");
    },true);
    return;
  }
  fileHash = fileHash + f.trim()+size;
  //console.log(fileHash);
  var ids = ["#collapseAllComment", "#collapseMyComment", "#collapseMyDownload"];
  var comment = $("#comment"+fileHash);
  if(comment.is(":hidden"))
    comment.show();
  else
    comment.hide();
  var data = comment.attr("collapse");
  var tmp = comment.attr("show");
  console.log(fileHash+","+data+","+tmp);
  if(data)
  {
    $(ids[window.parseInt(data)-1]+fileHash).hide();
    $(ids[window.parseInt(data)-1]+fileHash).slideUp();
    if(flag == window.parseInt(data) && tmp && window.parseInt(tmp) == 1){
      comment.attr("show",0);
      if($("#download_file_hash"+fileHash).attr("download")){
        if(window.parseInt(data)-1 == 0 || window.parseInt(data)-1 == 1){
          comment.attr("show",1);
          comment.attr("collapse",3);
          $(ids[2]+fileHash).slideDown();
          $(ids[2]+fileHash).show();
          $("#collapseMyDownload"+fileHash).css("overflow","inherit");
          comment.hide();
        }
      }
      return;
    }
  }  
  comment.attr("show",1);
  comment.attr("collapse",flag);
  $(ids[flag-1]+fileHash).slideDown();
  $(ids[flag-1]+fileHash).show();
  if(flag == 3){
    $("#collapseMyDownload"+fileHash).css("overflow","inherit");
  }
  comment.hide();
}
function longer(x){
  document.getElementById(x).style.width="100%";
}
function shorter(x){
  document.getElementById(x).style.width="60%";
}
//resource part
function getResListCallback(len,flag,res,container,page_tips,resource_type) {
  $("#pageloading").hide();
  $("#pageloading1").hide();
    var type = res["type"];
    if (type == 1) {
        var html = res["html"];
        var resourceList = res["resource_list"];
        //console.log(resourceList);
        if($(container).children().length == 0 || resourceList){
          var resourceContainer = $(container);
          /*if(resourceContainer.children('center').length > 0)
            resourceContainer.html(html);
          else
            resourceContainer.append(html);*/
          resourceContainer.html(html);
          resourceContainer.find('.container_score').slice(-resourceList.length).each(function (index, element) {
              var myScore = 0;
              var fileHash = resourceList[index]['file_hash'];
              var size = resourceList[index]['file_size'];
              var grade = resourceList[index]['grades'];
              if(window.fbtUID in grade){
                  myScore=resourceList[index]['grades'][window.fbtUID]/2;
              }            
              $(this).raty({
                  half: true,
                  //hints: ['1', '2', '3', '4', '5'],
                  path: "images",
                  starOff: 'star-off.png',
                  starOn: 'star-on.png',
                  size: 30,
                  score: myScore, //parseFloat($(this).find('.text_score_value').text()),
                  // target: '#result',
                  targetKeep: true,
                  click: function (score, evt) {
                      //这里就能获取用户的分数
                      //alert('u selected '+score);
                      //var grades=[0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10];
                      score=Math.round(score*2);
                      //var score = $(this).find('input[name="score"]').val();
                      $.post("/res", {"op":6,"fileHash":fileHash,"score": score,"size":size}, function(item, textStatus, xhr){
                          //console.log(item);
                          var tmp;
                          try{
                            tmp = JSON.parse(item);
                          }
                          catch(e){
                            tmp = item;
                          }
                          if(tmp["type"] == 0)
                            showErrorToast("评分失败，请重试");
                          else
                            showSuccessToast("评分成功");
                        });
                  }
              });
              var span = '<span class="pst">('+getJsonLength(grade)+'人)</span>';
              $(this).append(span);
          });
          resourceContainer.find("a.new_win").each(function(index, el) {
            $(el).click(function(event) {
              /* Act on the event */
              event.preventDefault();
              window.open($(this).attr("href"), "_blank");
              //window.socket.emit("jieba", $(this).attr("data"));
            });
          });
          if($("#container_resources").is(":visible") && $("#index_online").is(':checked')){
            var len = 0;
            $("#container_resources").find(".canhide").each(function(index, el) {
              $(el).hide();
              len ++;
            });
            if(len == resourceList.length){
              showStickyNoticeToast("很抱歉，当前页没有在线资源，请尝试浏览其他页。");
            }
          }
        }
        var MAX_RES_CNT_PER_PAGE = 20; //the server is set to 20
        if (len < MAX_RES_CNT_PER_PAGE) {
          hideGetMoreResourceButton(flag); // no more resources
        } else {
          resetGetMoreResourceButton(flag);
        }
        if(resource_type)
          $(resource_type).show();
        $(page_tips).hide();
        if(searchMode){
          var searchTime = ((new Date()).getTime() - curTime.getTime())/1000;
          var c = "搜索到"+resourceList.length+"个资源，用时"+searchTime+"s";
          $("#search_time").text(c);
          /*if(len >= MAX_RES_CNT_PER_PAGE)
            $("#btn_get_more_resources0").show();*/
          inSearch();
        }
        else{
          notInSearch(flag);
        }
    } else {
      $(page_tips).show();
      $(page_tips).html("<center><h3>资源列表请求失败！</h3></center>");
    }
}
function getHisListCallback(res) {
    var type = res["type"];
    if (type == 1) {
        var html = res["html"];
        var resourceList = res["resource_list"];
        if(!resourceList || (resourceList.length == 0)){
          $("#text_his_page_tips").show();
          $("#text_his_page_tips").html("<center><h3>下载列表为空！</h3></center>");
          return;
        }
        //console.log(html);
        var resourceContainer = $("#container_download_resources");
        resourceContainer
          .empty()
          .append(html);
        resourceContainer.find('.container_score').slice(-resourceList.length).each(function (index, element) {
            var myScore = 0;
            var fileHash = resourceList[index]['file_hash'];
            var size = resourceList[index]['file_size'];
            var grade = resourceList[index]['grades'];
            if(window.fbtUID in grade){
                myScore=resourceList[index]['grades'][window.fbtUID]/2;
            }            
            $(this).raty({
                half: true,
                //hints: ['1', '2', '3', '4', '5'],
                path: "images",
                starOff: 'star-off.png',
                starOn: 'star-on.png',
                size: 30,
                score: myScore, //parseFloat($(this).find('.text_score_value').text()),
                // target: '#result',
                targetKeep: true,
                click: function (score, evt) {
                    //这里就能获取用户的分数
                    //alert('u selected '+score);
                    //var grades=[0.5,1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10];
                    score=Math.round(score*2);
                    //var score = $(this).find('input[name="score"]').val();
                    $.post("/res", {"op":6,"fileHash":fileHash,"score": score,"size":size}, function(item, textStatus, xhr){
                        //console.log(item);
                        //console.log(item);
                        var tmp;
                        try{
                          tmp = JSON.parse(item);
                        }
                        catch(e){
                          tmp = item;
                        }
                        if(tmp["type"] == 0)
                          showErrorToast("评分失败，请重试");
                        else
                          showSuccessToast("评分成功");
                      });
                }
            });
            var span = '<span class="pst">('+getJsonLength(grade)+'人)</span>';
            $(this).append(span);
        });
        resourceContainer.find("a.new_win").each(function(index, el) {
          $(el).click(function(event) {
            /* Act on the event */
            event.preventDefault();
            window.open($(this).attr("href"), "_blank");
          });
        });
        $("#text_his_page_tips").hide();
    } else {
      $("#text_his_page_tips").show();
      $("#text_his_page_tips").html("<center><h3>资源列表请求失败！</h3></center>");
    }
}
function inSearch(){
  $("#search_time").show();
  $("#select_resource_type").hide();
  $("#more_resources0_top").hide();
  $("#more_resources0_bottom").hide();
}
function notInSearch(flag){
  $("#search_time").hide();
  //$("#btn_get_more_resources0").hide();
  if(flag == 0){
    $("#more_resources0_top").show();
    $("#more_resources0_bottom").show();
    $("#select_resource_type").show();
  }
}
function hideGetMoreResourceButton(num) {
  //$('#btn_get_more_resources'+num).hide();
}
function displayGetMoreResourceButton(num) {
  //$('#btn_get_more_resources'+num).show();
}
function resetGetMoreResourceButton(num) {
  /*$('#btn_get_more_resources'+num).show();
  $("#btn_get_more_resources"+num).attr("disabled", false);
  $("#loadingText"+num).text("查看更多");
  $("#loadingGif"+num).hide();*/
}
function resetResourcePage() {
    currentPage = 1;
    $('#text_home_page_tips').show();
    $('#text_home_page_tips').html("<center><h3>正在请求资源列表<img src='../images/loading3.gif'></img></h3></center>");
    $('#select_resource_type').hide();
    $("#more_resources0_top").hide();
    $("#more_resources0_bottom").hide();
    $('#container_resources').html("");
    hideGetMoreResourceButton(0);
    if(!searchMode){
      $('#input_search_resource').val("");
    }
}
function validKeyWord(keyWord){
    return keyWord.length > 0 && keyWord.length<=20;
}
function refreshResourceView(shouldpages) {
  $("#search_time").hide();
  var sortType = $('#select_resource_type').find("input:checked").val();
  if(shouldpages){
    if($("#more_resources_top").length > 0)
    {
      $("#more_resources_top").remove();
      $("#more_resources_bottom").remove();
    }
    $("#more_resources0_top").empty().addClass('get_more_resources0');
    $("#more_resources0_bottom").empty().addClass('get_more_resources0');
  }
  if(searchMode){
    var keyWord=$.trim($('#input_search_resource').val());
    if(validKeyWord(keyWord)){
      $.post("/res", {"op":7,"key_word":keyWord, "page": currentPage,  "sort_by": 1,"user":window.fbtUID}, function(item, textStatus, xhr){
        var tmp;
        try{
          tmp = JSON.parse(item);
        }
        catch(e){
          tmp = item;
        }
        var data = {};
        data["type"] = tmp["type"];
        data["resource_list"] = tmp["resource_list"];
        data["html"] = tmp["html"];
        var len = tmp["resource_list"].length;
        if("len" in tmp)
          len = tmp["len"];
        if($("#more_resources_top").length <= 0 && tmp["size"] > 20){
          totalP = tmp["size"] / 20;
          if(tmp["size"] % 20 != 0)
            totalP += 1;
          var options = {
            currentPage: 1,
            totalPages: totalP,
            numberOfPages:10,
            size:'large',
            alignment:'center',
            tooltipTitles: function (type, page, current) {
              switch (type) {
                case "prev":
                    return "上一页";
                case "next":
                    return "下一页";
                case "page":
                    return "第 " + page + "页";
              }
            },
            itemContainerClass: function (type, page, current) {
              return (page === current) ? "active" : "cur_p";
            },
            shouldShowPage:function(type, page, current){
              switch(type)
              {
                  case "first":
                  case "last":
                      return false;
                  default:
                      return true;
              }
            },
            onPageClicked: function(e,originalEvent,type,page){
              var currentTarget = $(e.currentTarget);
              var pages = currentTarget.bootstrapPaginator("getPages");
              if(pages.current == page)
                return;
              $("#pageloading").show();
              $("#container_resources").html("");
              searchMode = true;
              curTime = new Date();
              currentPage = page;
              refreshResourceView();
              if(currentTarget.attr("id") == "more_resources_top")
                $("#more_resources_bottom").bootstrapPaginator("show", currentPage);
              else{
                $("#more_resources_top").bootstrapPaginator("show", currentPage);
                window.scrollTo(0,0);
              }
            }
          }
          $("#container_resources").before("<div id='more_resources_top' class='get_more_resources' style='padding-top: 43px;height: 72px'></div>");
          $("#container_resources").after("<div id='more_resources_bottom' class='get_more_resources'></div>");
          $('.get_more_resources').each(function(index, el) {
            $(el).bootstrapPaginator(options);
          });
          $("#container_resources").css("margin-top","0px");
        }
        else if(shouldpages){
          $("#container_resources").css("margin-top","50px");
        }
        getResListCallback(len,0,data,'#container_resources','#text_home_page_tips','#select_resource_type');
      });
    }
  }else{
    $.post("/res", {"op":4,"res_type": currentResourceType, "page": currentPage,  "sort_by": sortType,"user":window.fbtUID}, function(item, textStatus, xhr){
      var tmp;
      try{
        tmp = JSON.parse(item);
      }
      catch(e){
        tmp = item;
      }
      var data = {};
      data["type"] = tmp["type"];
      data["resource_list"] = tmp["resource_list"];
      data["html"] = tmp["html"];
      var len = tmp["resource_list"].length;
      if("len" in tmp)
        len = tmp["len"]
      getResListCallback(len,0,data,'#container_resources','#text_home_page_tips','#select_resource_type');
      if(shouldpages){
        var size = tmp["size"];
        if(size > 20){
          totalP = size / 20;
          if(size % 20 != 0)
            totalP += 1;
          var options = {
            currentPage: 1,
            totalPages: totalP,
            numberOfPages:10,
            size:'large',
            alignment:'center',
            tooltipTitles: function (type, page, current) {
              switch (type) {
                case "prev":
                    return "上一页";
                case "next":
                    return "下一页";
                case "page":
                    return "第 " + page + "页";
              }
            },
            itemContainerClass: function (type, page, current) {
              return (page === current) ? "active" : "cur_p";
            },
            shouldShowPage:function(type, page, current){
              switch(type)
              {
                  case "first":
                  case "last":
                      return false;
                  default:
                      return true;
              }
            },
            onPageClicked: function(e,originalEvent,type,page){
              var currentTarget = $(e.currentTarget);
              var pages = currentTarget.bootstrapPaginator("getPages");
              if(pages.current == page)
                return;
              $("#pageloading").show();
              $("#container_resources").html("");
              curTime = new Date();
              currentPage = page;
              searchMode = false;
              refreshResourceView();
              if(currentTarget.attr("id") == "more_resources0_top")
                $("#more_resources0_bottom").bootstrapPaginator("show", currentPage);
              else{
                $("#more_resources0_top").bootstrapPaginator("show", currentPage);
                window.scrollTo(0,0);
              }
            }
          }
          $('.get_more_resources0').each(function(index, el) {
            $(el).bootstrapPaginator(options);
          });
        }
        $("#container_resources").css("margin-top","0px");
      }
      else if(shouldpages){
        $("#container_resources").css("margin-top","50px");
      }
    });
  }
}
function showFriendPages(size){
  if(size > 20){
    totalP = size / 20;
    if(size % 20 != 0){
      totalP += 1;
    }
    var option = {
      currentPage: 1,
      totalPages: totalP,
      numberOfPages:10,
      size:'large',
      alignment:'center',
      tooltipTitles: function (type, page, current) {
        switch (type) {
          case "prev":
              return "上一页";
          case "next":
              return "下一页";
          case "page":
              return "第 " + page + "页";
        }
      },
      itemContainerClass: function (type, page, current) {
        return (page === current) ? "active" : "cur_p";
      },
      shouldShowPage:function(type, page, current){
        switch(type)
        {
            case "first":
            case "last":
                return false;
            default:
                return true;
        }
      },
      onPageClicked: function(e,originalEvent,type,page){
        var currentTarget = $(e.currentTarget);
        var pages = currentTarget.bootstrapPaginator("getPages");
        if(pages.current == page)
          return;
        $("#pageloading1").show();
        $("#container_allFriend_resources").html("");
        $.post("/res", {"op":9, "user":window.fbtUID,"page": page}, function(item, textStatus, xhr){
          var tmp;
          try{
            tmp = JSON.parse(item);
          }
          catch(e){
            tmp = item;
          }
          var data = {};
          data["type"] = tmp["type"];
          data["resource_list"] = tmp["resource_list"];
          data["html"] = tmp["html"];
          var len = tmp["resource_list"].length;
          if("len" in tmp)
            len = tmp["len"]
          getResListCallback(len,2,data,'#container_allFriend_resources','#text_all_friend_tips');
        });
        if(currentTarget.attr("id") == "more_resources2_top")
          $("#more_resources2_bottom").bootstrapPaginator("show", page);
        else{
          $("#more_resources2_top").bootstrapPaginator("show", page);
          window.scrollTo(0,0);
        }
      }
    }
    $('.get_more_resources2').each(function(index, el) {
      $(el).bootstrapPaginator(option);
    });
    $("#more_resources2_bottom").show();
    $("#more_resources2_top").show();
    $("#container_allFriend_resources").css("margin-top","0px");
  }
  else{
    $('.get_more_resources2').hide();
    $("#container_allFriend_resources").css("margin-top","30px");
  }
}
function getCurrentCommentCnt(commentText) {
  return parseInt(commentText.replace(/[^0-9]/g, ''));
  }
function commentPress(event,flag,whichHtmlElement, fileHash,size){
    keynum = event.keyCode || event.which;
    if(event.ctrlKey && keynum == 13 || keynum == 10){
      commentResource(flag,whichHtmlElement, fileHash,size);
    }
  }
function commentResource(flag,whichHtmlElement, fileHash,size) {
  whichHtmlElement = whichHtmlElement+flag.trim()+size;
  var rawComment = $('#editbox_comment_content' + whichHtmlElement).val().trim();
  if (rawComment.length == 0) {
    showNoticeToast("评论不能为空");
    return;
  }
  else if (rawComment.length > 200){
    showNoticeToast("评论过长，请保持在200以内");
    return;
  }
  rawComment = htmlencode(rawComment);
  $.post("/res", {"size":size,"op":5, "fileHash":fileHash, "comment": rawComment}, function(item, textStatus, xhr){
    $('#editbox_comment_content' + whichHtmlElement).val("");
    if(window.parseInt(item["type"] == 0))
        showErrorToast("评论失败，请重试");
    else
        showSuccessToast("评论成功");
  });
  var all_comments = $('#text_all_comments' + whichHtmlElement).html();
  $('#text_all_comments' + whichHtmlElement).html(all_comments + "<strong>我</strong>(刚刚)：" + rawComment + "<br/>");
  var commentsCntText = $('#text_view_comments' + whichHtmlElement).text();
  $('#text_view_comments' + whichHtmlElement).text("(查看" + (getCurrentCommentCnt(commentsCntText) + 1) + "人评论)");
  $("#collapseMyComment" + whichHtmlElement).slideUp();
  $("#collapseMyComment" + whichHtmlElement).hide();
  if($("#download_file_hash"+whichHtmlElement).attr("download")){
    var comment = $("#comment"+whichHtmlElement);
    comment.attr("show",1);
    comment.attr("collapse",3);
    $("#collapseMyDownload"+whichHtmlElement).slideDown();
    $("#collapseMyDownload"+whichHtmlElement).show();
    $("#collapseMyDownload"+fileHash).css("overflow","inherit");
    comment.hide();
  }
  else
    $("#comment"+whichHtmlElement).show();
}
function typeChange(){
  var all_tag = {
    "请选择类别": [],
    "剧集": ["喜剧", "古装", "伦理", "武侠", "纪录片", "玄幻", "冒险", "警匪", "军事", "神话", "科幻", "搞笑", "偶像", "悬疑", "历史", "儿童", "都市", "家庭", "言情"],
    "电影": ["喜剧", "古装", "伦理", "恐怖", "纪录片", "爱情", "动作", "科幻", "武侠", "战争", "犯罪", "惊悚", "剧情", "玄幻", "冒险", "动画"],
    "音乐": ["流行","摇滚","舞曲","电子","HIP-HOP","乡村","民族","古典","音乐剧","轻音乐"],
    "动漫": ["热血","恋爱","搞笑","LOLI","神魔","科幻","真人","美少女","运动","亲子","励志","剧情","校园","历史"],
    "游戏": ["动作","冒险","模拟","角色扮演","休闲","视频","其它"],
    "综艺": ["晚会","生活","访谈","音乐","游戏","旅游","真人秀","美食","益智","搞笑","纪实","汽车"],
    "体育": ["篮球","足球","台球","羽毛球","乒乓球","田径","水上项目","体操","其它"],
    "软件": ["系统","应用","管理","行业","安全防护","多媒体","网络软件","教学方面","即时通讯","娱乐","图形处理","编程"],
    "其它": ["其它"],
    "学习": ["课后作业和答案","课堂笔记","往届考题","电子书或视频等辅助资料","课程课件","课程资料合集","学习心得","TED","百家讲坛","软件教学","其它"]
  };
  //console.log($("#resourceMainType option:selected").text());
  var t = $("#resourceMainType option:selected").text().trim();
  /*if(t == "电影"){
    $("#resourceChName").show();
  }
  else{
    $("#resourceChName").hide();
  }*/

  //显示上传规范
  if(t == '请选择类别') $('#guifan-link > span').text('');
  else $('#guifan-link > span').text('[' + t + ']');
  var id = 'guifan-' + Object.keys(all_tag).indexOf(t);
  var clickcode = $('#guifan-link > a').attr('onclick');
  clickcode = clickcode.replace(/#.*?"/, '#' + id + '"');
  $('#guifan-link > a').attr('onclick', clickcode);

  var list = all_tag[t];
  $("#resourceLabel").empty();
  tagElements = [];
  $("#label_tags").empty();
  $("#upload_panel").html(upload_html[t]);
  if(t == "电影" || t=="剧集" || t=="综艺" || t=="动漫")
  {
    window.shouldUpload = false;
    $("#resourceName").blur(function(event) {
      /* Act on the event */
      var val = $("#resourceName").val();
      if(val.length > 0)
      {
        window.socket.emit("douban", val);
        $("#err_tips").html("正在为您获取资源详情，请耐心等候...");
      }
      //if(!val || !isChinese(val)){
      //  showNoticeToast("请填写一个中文名称<br/>可以帮助找到漂亮配图哟~");
      //}        
    }).focus(function(event) {
      /* Act on the event */
      $("#err_tips").html("");
      $("#upload_exp_info").remove();
      delete window.uploadDoubanData;
    });
    $("#upload_subType").show();
  }
  else{
    $("#upload_subType").hide();
  }
  $('#resourceLabel').append("<option value='请选择标签'>请选择标签</option>");
  for(var i = 0; i < list.length; i++){
    var item = list[i];
    var tmp = "<option data='"+i+"' value='"+item+"'>" + item + "</option>";
    $("#resourceLabel").append(tmp);
  }
}
var tagElements = [];
var tagNumMax = 5;
function tagChange(){
  var tag = $('#resourceLabel').val();
  var idx = tagElements.indexOf(tag);
  if (idx == -1) {
      if (tagElements.length < tagNumMax) {
          tagElements.push(tag);
      } else {
          showNoticeToast("最多可以添加" + tagNumMax + "个标签");
      }
  } else {
      tagElements.splice(idx, 1);
  }
  $('#label_tags').empty();
  var tags = "";
  for (var i = 0; i < tagElements.length; i++) {
      console.log(tagElements[i])
      tags += "<a style='cursor:pointer;' id='tag" + i + "'><span style='margin-left:10px;cursor:pointer;' class='glyphicon glyphicon-tag'></span>" + tagElements[i] +"</a>";
  }
  $('#label_tags').html(tags);
  $('#resourceLabel').val("请选择标签");

  var clickHandler = function(id) {
      var tag = $(id).text();
      var _idx = tagElements.indexOf(tag);
      tagElements.splice(_idx, 1);
      var tags = "";
      for (var i=0; i < tagElements.length; i++) {
          tags += "<a id='tag" + i + "'><span style='margin-left:10px;' class='glyphicon glyphicon-tag'></span>" + tagElements[i] +"</a>";
      }
      $('#label_tags').html(tags);
      for(var i=0; i<tagElements.length; i++) {
        $('#tag' + i).off('click');
        (function(x) {
            $('#tag' + x).click(function() {
                clickHandler('#tag' + x);
            });
        }(i));
      }
  }

  for(var i=0; i<tagElements.length; i++) {
    $('#tag' + i).off('click');
    (function(x) {
        $('#tag' + x).click(function() {
            clickHandler('#tag' + x);
        });
    }(i));
  }

  var t = $.trim($("#resourceMainType option:selected").text());
  if(t === "学习"){
    //var d = window.parseInt($("#resourceLabel option:selected").attr("data"));
    var d = tagElements.length;
    var exclusiveInStudy = ["TED","百家讲坛","软件教学","其它"];
    for (var i = 0; i < tagElements.length; i++) {
        d = 1;
        if (exclusiveInStudy.indexOf(tagElements[i]) == -1) {
            d = 0;
            break;
        }
    }
    if(d > 0){
      $("#upload_panel").find("input[data='1']").attr("disabled","disabled");
    }
    else
      $("#upload_panel").find("input[data='1']").removeAttr('disabled'); 
  }
}
function fileChange(){
  var path = "";
  if(window.fileSel == "1"){
    path=$('#resourceFile').val();
  }
  else if(window.fileSel == "3"){
    path=$('#resourceDir').val();
  }  
  //window.socket.emit('file_name',path);
  //console.log(path);
  if(path)
    $("#upload_flag").show();
  else
    $("#upload_flag").hide();
  $("#upload_flag").parent("button").css('width', '100%');
}
function fileSelChange(t){
  var val = $(t).attr("data");
  if(val == "1"){
    $("#resourceFile").trigger('click');
  }
  else{
    $("#resourceDir").trigger('click');
  }
  window.fileSel = val;
  $(t).parent('li').parent('ul').siblings('button').children('strong').html($(t).html());
}
function validateUpload(upload_type){
  var exp_info = {};
  var ret = [];
  switch(upload_type) {
    case 0:case 6:
      var enName = $("#resourceEnName").val();
      if (enName && enName.length > 0) {
        ret.push(true);
        exp_info["resource_en_name"] = enName;
        ret.push(exp_info);
      }
      break;
    case 1:case 4:
      var num = $("#resourceNum").val();
      var reg = new RegExp("^[0-9]+$");
      if(!reg.test(num)){
        showErrorToast("集数只能为纯数字");
        ret.push(false);
        return ret;
      }
      ret.push(true);
      exp_info["resource_num"] = num;
      var enName = $("#resourceEnName").val();
      if (enName && enName.length > 0) {
        exp_info["resource_en_name"] = enName;
      }
      ret.push(exp_info);
      break;
    case 3:
      var art = $("#resourceArt").val();
      var album = $("#resourceAlbum").val();
      if(!art || !album){
        showErrorToast("请将上传信息填写完整");
        ret.push(false);
        return ret;
      }
      ret.push(true);
      exp_info["resource_art"] = art;
      exp_info["resource_album"] = album;
      ret.push(exp_info);
      break;
    case 2:
      //var d = window.parseInt($("#resourceLabel option:selected").attr("data"));
        var d = tagElements.length;
        var exclusiveInStudy = ["TED","百家讲坛","软件教学","其它"];
        for (var i = 0; i < tagElements.length; i++) {
            d = 1;
            if (exclusiveInStudy.indexOf(tagElements[i]) == -1) {
                d = 0;
                break;
            }
        }
        if(d == 0){
        var course = $("#resourceCourse").val();
        var teacher = $("#resourceTeacher").val();
        var school = $("#resourceSchool").val();
        var academy = $("#resourceAcademy").val();
        if(!course || !teacher || !school || !academy){
          showErrorToast("请将上传信息填写完整");
          ret.push(false);
          return ret;
        }
        exp_info["resource_course"] = course;
        exp_info["resource_teacher"] = teacher;
        exp_info["resource_school"] = school;
        exp_info["resource_academy"] = academy;
      }
      ret.push(true);
      ret.push(exp_info);
      break;
    case 5:
      var enName = $("#resourceEnName").val();
      var version = $("#resourceVersion").val();
      if(!version){
        showErrorToast("请填写版本号");
        ret.push(false);
        return ret;
      }
      ret.push(true);
      exp_info["resource_en_name"] = enName;
      exp_info["resource_version"] = version;
      ret.push(exp_info);
      break;
    case 7:
      var date = $("#resourceDay").val();
      if(!date){
        showErrorToast("请填写资源日期");
        ret.push(false);
        return ret;
      }
      ret.push(true);
      exp_info["resource_date"] = date;
      var enName = $("#resourceEnName").val();
      if (enName && enName.length > 0) {
        exp_info["resource_en_name"] = enName;
      }
      ret.push(exp_info);
      break;
    case 8:
      var platform = $("#resourcePlantform").val();
      var version = $("#resourceVersion").val();
      if(!version || !platform){
        showErrorToast("请将上传信息填写完整");
        ret.push(false);
        return ret;
      }
      ret.push(true);
      exp_info["resource_platform"] = platform;
      exp_info["resource_version"] = version;
      ret.push(exp_info);
      break;
    default:
      ret.push(true);
      ret.push(exp_info);
      break;    
  }
  return ret;
}
function fileUpload(){
  var t = $.trim($("#resourceMainType option:selected").text());
  if(!window.shouldUpload && (t == "电影" || t=="剧集" || t=="综艺" || t=="动漫"))
  {
    showNoticeToast("正在为您获取资源信息，请耐心等候");
    return;
  }
  $('#err_tips').html("");
  var filePath;
  var val = window.fileSel;
  if(val == "1"){
    filePath=$('#resourceFile').val();
  }
  else{
    filePath=$('#resourceDir').val();
  }
  //console.log($('#resourceFile').val());
  //console.log($('#resourceDir').val());
  if (!filePath) {
  $('#err_tips').html("请选择分享的文件");
  return;
  }
  var mainType = window.parseInt($('#resourceMainType').val());
  if(mainType == -1)
  {
    $('#err_tips').html("请选择类别");
    return;
  }
  var subType = $('#resourceSubType').val();
  if(!subType)
  {
    $('#err_tips').html("请选择类型");
    return;
  }
  var fileName = $('#resourceName').val();
  if (!fileName) { 
    $('#err_tips').html("请填写资源名");
    return;
  }
  //var label = $('#resourceLabel').val();
  if (tagElements.length == 0) {
      $('#err_tips').html("请至少选择一个标签");
      return;
  }
  var label = tagElements.join(',');
  var isPublic = 1;
  if ($("#checkbox_is_public").is(':checked')) {
  isPublic = 0;
  }
  var comment = $('#resourceComment').val().trim();
  if (!comment) {
    comment = "珍藏的好资源分享给大家，希望大家喜欢。";
  }
  if(comment.length > 200){
    showNoticeToast("评论过长，请保持在200以内");
    return;
  }
  comment = htmlencode(comment);
  //var grade = $("input:radio[name ='radio_grade']:checked").val();
  var grade = $('#text_my_socre').text();
  if (!grade) {
    grade = 5;
  }
  else
    grade = parseFloat(grade).toFixed(1);//10分制
  var ret = validateUpload(mainType);
  if(!ret[0]){
    return;
  }
  //TODO FIX 之后修改为按照文件夹上传就不加，按照文件方式上传才加后缀
  if(t=="剧集" || t=="动漫")
    fileName = fileName+"_"+$("#resourceNum").val();
  fileName = htmlencode(fileName);
  var param = {};
  param["op"] = 0;
  param["path"] = filePath;
  param["name"] = fileName;
  param["mainType"] = mainType;
  param["subType"] = subType;
  param["label"] = label;
  param["desc"] = comment;
  param["grade"] = grade;
  param["isPublic"] = isPublic;
  param["nick_name"] = window.nick_name;
  param["ext_info"] = {};
  if(window.uploadDoubanData){
    param["ext_info"] = window.uploadDoubanData;
  }
  for(var key in ret[1]){
    param["ext_info"][key] = ret[1][key];
  } 
  param["ext_info"] = JSON.stringify(param["ext_info"]);
  if(val == '3'){
    param["isDir"] = 1;
  }
  else{
    param["isDir"] = 0;
  }
  //console.log(param);
  /*var time = (new Date()).getTime();
  param["time"] = time;*/
  //console.log(param);
  $('#resourceFile').val("");
  $('#resourceDir').val("");
  $.ajax({
    url:"/res",
    type:"POST",
    data:param,
    timeout:600000,
    dataType:"json",
    success:function(item){
      //console.log(item);
      delete window.uploadDoubanData;
    },
    error:function(){
      delete window.uploadDoubanData;
      console.log("upload error");
      showErrorToast("上传失败，请检查文件是否存在或者重试");
      window.upload_count--;
      if(window.upload_count == 0)
        $("a#tab3 > span.uploadHint").hide();
    }
  });
  //hide the file upload dialog
  window.upload_count++;
  $("a#tab3 > span.uploadHint").show();
  showNoticeToast("正在上传，请稍后");
  $('#uploadModal').modal("hide");            
}
function show_to_top(){
  var bt = $("div.show").find('.topcontrol');
    if(bt.length > 0){
      var st = $(window).scrollTop(); 
     if(st > 30){ 
             bt.show(); 
     }else{ 
             bt.hide(); 
     }
  } 
}
function refreshBeingDownloadedFiles() {
    $.get('/beingDownloadedFiles', function(data) {
        try {
            result = JSON.parse(data);
        } catch(e) {
            console.error(e);
            return;
        }
        data = result;
        var html = "暂无供水";
        if (data.length > 0) {
            html = "<li><a>" + data.join("</a></li><li><a>") + "</a></li>";
        }
        $('#beingDownloadedFiles').html(html);
        $('#beingDownloaded_count').text(data.length);
    });
}
/*function refreshDownloadView(){
  if(!window.ws)
  {
    return;
  }
  $.post("/res", {"op":10,"user":window.fbtUID}, function(item, textStatus, xhr){
    var tmp;
    try{
      tmp = JSON.parse(item);
    }
    catch(e){
      tmp = item;
    }
    //render history
    var his = {};
    his["resource_list"] = tmp["his_list"];
    his["type"] = tmp["type"];
    his["html"] = tmp["his_html"];
    // refresh owners
    his['resource_list'].forEach(function(item) {
      $('#online' + item['file_hash'] + 'm').text(item['online_owners_num'] + '/' + item['total_owners_num']);
    });
    //showSuccessToast("刷新下载列表成功");
  });
}*/
function canUse(){
  var fbTime = $("#fbTime");
  var curTime = parseInt(fbTime.text())
  if(curTime == 0){
    $("#fbRuleModal").modal('hide');
    $("a#set").trigger('click');
    showStickyNoticeToast("点击右上角的积分榜图标可看到积分规则和积分排行,点击积分榜左边的分享图标可看到自己的所有分享,点击积分榜右边的小人图标可进入个人中心.");
    window.setting["first"] = 0;
    window.socket.emit("first", "1");
  }
  else{
    curTime --;
    fbTime.text(curTime);
    setTimeout(canUse, 1000);
  }
}
function firstGetRes(){
  if(!window.ws)
  {
    return;
  }
  if(!window.shouldInterval)
    return;
  window.shouldInterval = false;
  clearInterval(window.getRes);
  $.post("/res", {"op":10,"user":window.fbtUID}, function(item, textStatus, xhr){
    //console.log(item);
    delete window.getRes;
    var tmp;
    try{
      tmp = JSON.parse(item);
    }
    catch(e){
      tmp = item;
    }
    //render history
    var his = {};
    his["resource_list"] = tmp["his_list"];
    his["type"] = tmp["type"];
    his["html"] = tmp["his_html"];
    getHisListCallback(his);
  });
  $.post("/res", {"op":4,"user":window.fbtUID}, function(item, textStatus, xhr){
    if($('#list_resource_view a:first').hasClass("sel")){
      var tmp;
      try{
        tmp = JSON.parse(item);
      }
      catch(e){
        tmp = item;
      }
      var data = {};
      data["type"] = tmp["type"];
      data["resource_list"] = tmp["resource_list"];
      data["html"] = tmp["html"];
      var len = tmp["resource_list"].length;
      if("len" in tmp)
        len = tmp["len"]
      getResListCallback(len,0,data,'#container_resources','#text_home_page_tips','#select_resource_type');
      var size = tmp["size"];
      if(size > 20){
        totalP = size / 20;
        if(size % 20 != 0)
          totalP += 1;
        var options = {
          currentPage: 1,
          totalPages: totalP,
          numberOfPages:10,
          size:'large',
          alignment:'center',
          tooltipTitles: function (type, page, current) {
            switch (type) {
              case "prev":
                  return "上一页";
              case "next":
                  return "下一页";
              case "page":
                  return "第 " + page + "页";
            }
          },
          itemContainerClass: function (type, page, current) {
            return (page === current) ? "active" : "cur_p";
          },
          shouldShowPage:function(type, page, current){
            switch(type)
            {
                case "first":
                case "last":
                    return false;
                default:
                    return true;
            }
          },
          onPageClicked: function(e,originalEvent,type,page){
            var currentTarget = $(e.currentTarget);
            var pages = currentTarget.bootstrapPaginator("getPages");
            if(pages.current == page)
              return;
            $("#pageloading").show();
            $("#container_resources").html("");
            curTime = new Date();
            currentPage = page;
            refreshResourceView();
            if(currentTarget.attr("id") == "more_resources0_top")
              $("#more_resources0_bottom").bootstrapPaginator("show", currentPage);
            else{
              $("#more_resources0_top").bootstrapPaginator("show", currentPage);
              window.scrollTo(0,0);
            }
          }
        }
        $('.get_more_resources0').each(function(index, el) {
          $(el).bootstrapPaginator(options);
        });
        $("#container_resources").css("margin-top","0px");
      }
      else{
        $("#container_resources").css("margin-top","50px");
      }
    }
    if(("first" in window.setting) && window.setting["first"] != 0){
      $("#fbRuleModal").modal({
        backdrop: 'static'
      });
      setTimeout(canUse, 1000);
    }
  });
}
function index_init(){
  console.log("index init");
  window.fbtUID = window.parseInt(getCookie("fbt_user_id"));
  window.nick_name = $("#nick_name").text().trim();
  console.log("nick_name: "+window.nick_name);
  resourceMainType = {0: "电影", 1: "剧集", 2: "音乐", 3: "动漫", 4: "游戏", 5: "综艺", 6: "体育", 7: "软件", 8: "其它"};
  resourceTypes = Object.keys(resourceMainType);
  window.state_html = {};
  window.singleChat = {};
  window.uploadSize = {};
  window.upload_count = 0;
  window.downloadFolder = {}; 
  //window.downloadFolderFlag = {};
  window.downloadFolderName = {};
  //window.downloadFolderSize = {};
  window.shouldUpload = true;
  window.shouldInterval = true;
  $(window).scroll(function() {
      show_to_top();     
  });
  $("#label_online").trigger('click');
  $("#label_online").trigger('click');
  $("#index_online").change(function(event) {
    /* Act on the event */
    //console.log($(this).is(':checked'));
    if($(this).is(':checked')){
      var len = 0;
      $("#container_resources").find(".canhide").each(function(index, el) {
        $(el).hide();
        len ++;
      });
      if(len == $("#container_resources").children().length){
        showStickyNoticeToast("很抱歉，当前页没有在线资源，请尝试浏览其他页。");
      }
    }
    else{
      $("#container_resources").find(".canhide").each(function(index, el) {
        $(el).show();
      });
    }
  });
  $("#home").click(function(event) {
    /* Act on the event */
    event.preventDefault();
    window.open("http://www.friendsbt.com", "_blank");
  });

  $.get("/html/modal_index.html", function(data){
    $("body").append(data);
    //$("#menu").addClass("dropdown-menu");
    if(window.setting["upload_speed"]){
      var delta = 1024*1024;
      var speed = (window.parseInt(window.setting["upload_speed"])/delta).toFixed(2);
      $("#set_upload_speed").val(speed);
    }
    else
      $("#set_upload_speed").val("2.00");
    if (window.setting["downloadSaveDir"]) {
      $('#text_download_path').text(window.setting["downloadSaveDir"]);
    } else {
        $('#text_download_path').text("尚未设置下载目录");
    }
    var tray = $("#settingModal").find("label#exit_tray");
    if(window.setting["tray"] == 0){
      tray.trigger('click');
      tray.trigger('click');
    }
    else{
      tray.trigger('click');
    }
    var auto = $("#settingModal").find("label#auto_login");
    if(window.setting["boot"] == 0){
      auto.trigger('click');
      auto.trigger('click');
    }
    else{
      auto.trigger('click');
    }
    var auto_log = $("#settingModal").find("label#auto_log");
    if(window.setting["auto_log"] == 0){
      auto_log.trigger('click');
      auto_log.trigger('click');
    }
    else{
      auto_log.trigger('click');
    }
    /*var auto_log = $("#settingModal").find("label#allow_v4_download");
    if(window.setting["allow_v4_download"] == 0){
      auto_log.trigger('click');
      auto_log.trigger('click');
    }
    else{
      auto_log.trigger('click');
    }*/
    var voice = $("#settingModal").find("label#voice");
    if(window.setting["voice"] == 0){
      voice.trigger('click');
      voice.trigger('click');
    }
    else{
      voice.trigger('click');
    }
    var chat_robot = $("#settingModal").find("label#chat_robot");
    if(window.setting["chat_robot"] == 0){
      chat_robot.trigger('click');
      chat_robot.trigger('click');
    }
    else{
      chat_robot.trigger('click');
    }
    var allow_bg = $("#settingModal").find("label#allow_bg");
    if(window.setting["allow_bg"] == 0){
      allow_bg.trigger('click');
      allow_bg.trigger('click');
    }
    else{
      allow_bg.trigger('click');
    }
    var friends_online_inform = $("#settingModal").find("label#friends_online_inform");
    if(window.setting["friends_online_inform"] == 0){
      friends_online_inform.trigger('click');
      friends_online_inform.trigger('click');
    }
    else{
      friends_online_inform.trigger('click');
    }
    $("#button_download_path").click(function(){
      $("#editbox_download_path").trigger('click');
    });
    $('#star').raty({
      half: true,
      //hints: ['1', '2', '3', '4', '5'],
      path: "images",
      starOff: 'star-off.png',
      starOn: 'star-on.png',
      size: 30,
      // target: '#result',
      targetKeep: true,
      click: function (score, evt) {
          //这里就能获取用户的分数
          //alert('u selected '+score);
          score=Math.round(score*2);
          $('#text_my_socre').text(score);
          //var score = $(this).find('input[name="score"]').val();
      }
    });
    var label = $("#uploadModal").find("div.modal-footer").find("label.checkbox");
    label.trigger('click');
    label.trigger('click');
    $("#resourceComment").val("");         
  });
  window.getRes = setInterval(firstGetRes,1000);                    
  //setInterval(refreshDownloadView, 10*60*1000);//定时刷新下载列表,10分钟刷一次

  setInterval(refreshBeingDownloadedFiles, 5 * 60 * 1000); // 5分钟刷一次

  $('.home_nav > li > a.clickable').click(function () {
    $(".home_nav > li > a.clickable").css({"border-bottom": "3px solid #ecf0f1"});
    $(this).css({"border-bottom": "3px solid #1abc9c"});
  });
  $("#tab4").click(function() {
    /* Act on the event */
    if($(this).attr("data") == 1 || $(this).attr("data") == "1")
      return;
    showNoticeToast("这里是好友资源的集中营，下载无需F币");
    $(this).attr("data","1");
    var that = this;
    if($("#text_all_friend_tips").is(":hidden")){
      $("#text_all_friend_tips").html("<center><h3>正在努力请求资源列表<img src='../images/loading3.gif'></img></h3></center>");
      $("#container_allFriend_resources").empty();
      $(".get_more_resources2").hide();
      $("#more_resources2_top").hide();
      $("#more_resources2_bottom").hide();
      $("#text_all_friend_tips").show();
    }   
    $.post("/res", {"op":9,"user":window.fbtUID}, function(item, textStatus, xhr){
      var tmp;
      try{
        tmp = JSON.parse(item);
      }
      catch(e){
        tmp = item;
      }
      var data = {};
      data["type"] = tmp["type"];
      data["resource_list"] = tmp["resource_list"];
      data["html"] = tmp["html"];
      var len = tmp["resource_list"].length;
      if("len" in tmp)
        len = tmp["len"]
      getResListCallback(len,2,data,'#container_allFriend_resources','#text_all_friend_tips');
      $("#more_resources2_top").empty().addClass('get_more_resources2');
      $("#more_resources2_bottom").empty().addClass('get_more_resources2');
      var size = tmp["size"];
      showFriendPages(size);
      $("#more_resources2_top").show();
      $("#more_resources2_bottom").show();
      $(that).attr("data","0");
    });
  });

  currentFPage = 1;
  currentPage = 1;
  currentResourceType = 0; //movie
  searchMode=false;
  curTime = 0;
  $("#btn_get_more_resources0").click(function () {
      $(this).attr("disabled", true);
      $("#loadingText0").text("正在获取更多...");
      $("#loadingGif0").show();
      curTime = new Date();
      currentPage += 1;
      refreshResourceView();
  });
  $("#btn_get_more_resources2").click(function () {
      $(this).attr("disabled", true);
      $("#loadingText2").text("正在获取更多...");
      $("#loadingGif2").show();
      currentFPage += 1;
      $.post("/res", {"op":9, "user":window.fbtUID,"page": currentFPage}, function(item, textStatus, xhr){
        var tmp;
        try{
          tmp = JSON.parse(item);
        }
        catch(e){
          tmp = item;
        }
        var data = {};
        data["type"] = tmp["type"];
        data["resource_list"] = tmp["resource_list"];
        data["html"] = tmp["html"];
        var len = tmp["resource_list"].length;
        if("len" in tmp)
          len = tmp["len"]
        getResListCallback(len,2,data,'#container_allFriend_resources','#text_all_friend_tips');
      });
  });
  $('#list_resource_view a').each(function (index) {
    $(this).on("click", function () {
      $("#list_resource_view").find(".sel").removeClass('sel').addClass('not_sel');
      $(this).addClass('sel').removeClass('not_sel');
      if($(this).attr("data")){
        if($("#more_resources_top").length > 0)
        {
          $("#more_resources_top").remove();
          $("#more_resources_bottom").remove();
        }
        $("#more_resources0_top").empty().addClass('get_more_resources0').css("height","0px");
        $("#more_resources0_bottom").empty().addClass('get_more_resources0');
        if(window.platform == 'darwin')
        {
          showWarningToast("很抱歉，您的操作系统暂时不支持该功能");
          return;
        }
        if($("#container_resources").children('iframe').length > 0)
          return;
        var frame = $("<iframe></iframe>");
        frame.attr("src","http://127.0.0.1:12345/ipv6");
        frame.attr("width", $(document).width());
        frame.attr("height", $(document).height());
        var left = $("#container_resources").css("margin-left");
        var p_left = $("#container_resources").css("padding-left");
        left = window.parseInt(left.replace("px","")) + window.parseInt(p_left.replace("px",""));
        frame.css("margin-left",-left+"px");
        $("#container_resources").html(frame);
        $("#btn_get_more_resources0").hide();
        $("#pageloading").hide();
        return;
      }
      else if($(this).attr("meta")){
        if($("#more_resources_top").length > 0)
        {
          $("#more_resources_top").remove();
          $("#more_resources_bottom").remove();
        }
        $("#more_resources0_top").empty().addClass('get_more_resources0').css("height","0px");
        $("#more_resources0_bottom").empty().addClass('get_more_resources0');
        var frame = $("<iframe></iframe>");
        frame.attr("src","http://127.0.0.1:12345/home");
        frame.attr("width", $(document).width());
        frame.attr("height", $(document).height());
        var left = $("#container_resources").css("margin-left");
        var p_left = $("#container_resources").css("padding-left");
        left = window.parseInt(left.replace("px","")) + window.parseInt(p_left.replace("px",""));
        frame.css("margin-left",-left+"px");
        $("#container_resources").html(frame);
        $("#btn_get_more_resources0").hide();
        $("#pageloading").hide();

        //移出旧版本Navbar
        $('.nav.nav-tabs').hide();
        $('#home_type').hide();
        $('#more_resources0_top').hide();
        $('#resources').css('padding', '0px');
        $('#text_home_page_tips').hide();
        $('#container_sns_share').hide();
        $('#container_resources').removeClass('container');
        $('iframe').css('position', 'absolute');
        $('iframe').css('width', '100%');
        $('iframe').css('height', '100%');
        $('iframe').css('top', 0);
        $('iframe').css('margin', 0);
        $('#upload_control').hide();
        $('html').css('overflow', 'hidden');
        return;
      }
      else
      {
        $("#more_resources0_top").css("height","72px");
      }
      if(!$("#select_resource_type").find('input:radio[name="radio"]').first().is(':checked')){
        $("#list_resource_view").attr("data","1");
        $("#select_resource_type").find('input:radio[name="radio"]').first().click();
      }        
      searchMode=false;
      currentResourceType = index;
      currentPage = 1;
      resetResourcePage();
      refreshResourceView(true);
    });
  });
  $("#select_resource_type").find('input:radio[name="radio"]').change(
    function(){
        if ($(this).is(':checked')) {
          if($("#list_resource_view").attr("data") == "1")
          {
            $("#list_resource_view").attr("data","0");
            return;
          }
          currentPage = 1;
          resetResourcePage();
          refreshResourceView(true);
        }
  });
  $('#input_search_resource').keyup(function(e){
      if(e.keyCode == 13)//enter key
      {
        searchMode=true;
        $("#list_resource_view").find(".sel").removeClass('sel').addClass('not_sel');
        curTime = new Date();
        var keyWord=$('#input_search_resource').val().trim();
        if(validKeyWord(keyWord)){
            if(!$("#resources").hasClass('active')){
              $("#tab1").click();
            }
            currentPage = 1;
            resetResourcePage();
            refreshResourceView(true);
        }
      }
  });
  $("#tab3").click(function(event) {
    /* Act on the event */
    $("#resourceName").val("");
    $("#resourceComment").val("");
    $("#upload_flag").hide();
    $("#upload_panel").empty();
    $("#resourceMainType").val("-1");
    $("#resourceLabel").empty();
    $("#resourceDir").val("");
    $("#resourceFile").val("");
    $("#err_tips").html("");
    tagElements = [];
    $("#label_tags").empty();
    $("#uploadModal").modal({
      backdrop: 'static'
    });
  });
  //openDir("","");//TODO FIXME
}
function searchTag(tag){
  searchMode=true;
  curTime = new Date();
  tag = tag.split(" ")[0];
  $('#input_search_resource').val(tag);
  var keyWord=$.trim($('#input_search_resource').val());
  if(validKeyWord(keyWord)){
      if(!$("#resources").hasClass('active')){
        $("#tab1").click();
      }
      currentPage = 1;
      resetResourcePage();
      refreshResourceView(true);
  }
}
function downloadGrumble(){
  showNoticeToast("已经添加到我的下载");
  $('#tab2').find(".downloadHint").fadeIn('400', function() {
    setTimeout(out, 2000);
  });
  function out(){
    $('#tab2').find(".downloadHint").fadeOut('400', function() {
      
    });
  }
}
function copyMsg(dest){
  var tmp = $(".index li.dropdown._");
  var a = tmp.find("a.dropdown-toggle");
  var ul = tmp.find("ul.menu");
  var a_clone = a.clone(true,true);
  var ul_clone = ul.clone(true,true);
  var d = $(dest).find("li.dropdown");
  d.append(a_clone);
  d.append(ul_clone);
}
function settingChange() {
  var value = $("#editbox_download_path").val();
  if(value)
    $('#text_download_path').text(value);
}

function saveSettings(){
  var speed = $("#set_upload_speed").val();
  var path = $('#text_download_path').text();
  var tray;
  var boot;
  var auto;
  var v4 = 1;
  var voice;
  var chat_robot;
  var bg;
  if($("#voice").hasClass('checked'))
    voice = 1;
  else
    voice = 0;
  if($("#auto_log").hasClass('checked'))
    auto = 1;
  else
    auto = 0;
  if($("#auto_login").hasClass('checked'))
    boot = 1;
  else
    boot = 0;
  if($("#exit_tray").hasClass('checked'))
    tray = 1;
  else
    tray = 0;
  if($("#chat_robot").hasClass('checked'))
    chat_robot = 1;
  else
    chat_robot = 0;
  /*if($("#allow_v4_download").hasClass('checked'))
    v4 = 1;
  else
    v4 = 0;*/
  if($("#allow_bg").hasClass('checked'))
    bg = 1;
  else
    bg = 0;
  if($("#friends_online_inform").hasClass('checked'))
    friends_online_inform = 1;
  else
    friends_online_inform = 0;
  $.get("/setting/save?path="+path+"&tray="+tray+"&boot="+boot+"&auto_log="+auto+"&allow_v4_download="+v4+"&voice="+voice+"&upload_speed="+speed+"&chat_robot="+chat_robot+"&allow_bg="+bg+"&friends_online_inform="+friends_online_inform, function(data){
    data = JSON.parse(data);
    if (data["type"] == 1) {
      //点击保存设置后 隐藏对话框
      $('#settingModal').modal('hide');
      if(window.setting["allow_bg"] != bg){
        if(bg == 1){
          $("html").css("background", "url(images/fbt_bg1.png) fixed");
        }
        else{
          $("html").css("background", "None");
        }
      }
      window.setting["downloadSaveDir"] = $("#editbox_download_path").val();
      window.setting["auto_log"] = auto;
      window.setting["allow_v4_download"] = v4;
      window.setting["allow_bg"] = bg;
      window.setting["voice"] = voice;
      window.setting["tray"] = tray;
      window.setting["boot"] = boot;
      window.setting["chat_robot"] = chat_robot;
      window.setting["upload_speed"] = speed;
      window.setting["friends_online_inform"] = friends_online_inform;
      showSuccessToast("保存成功");
    } else {
      $('#text_download_path').text('无效下载路径');
      showErrorToast("保存失败");
    }
  },true); 
}
function resetSettings(){
  window.setting["downloadSaveDir"] = window.setting["defaultDownloadDir"];
  $('#text_download_path').text(window.setting["downloadSaveDir"]);
  var path = window.setting["downloadSaveDir"];
  var tray = 1;
  window.setting["tray"] = 1;
  var boot = 0;
  window.setting["boot"] = 0;
  var auto = 0;
  window.setting["auto_log"] = 0;
  var v4 = 0;
  var bg = 1;
  window.setting["allow_v4_download"] = v4;
  window.setting["allow_bg"] = bg;
  var voice = 1;
  window.setting["voice"] = 1;
  var speed = 2;
  var chat_robot = 1;
  window.setting["upload_speed"] = 2;
  window.setting["friends_online_inform"] = 1;
  $.get("/setting/save?path="+path+"&tray="+tray+"&boot="+boot+"&auto_log="+auto+"&allow_v4_download="+v4+"&voice="+voice+"&upload_speed="+speed+"&chat_robot="+chat_robot+"&allow_bg="+bg+"&friends_online_inform="+friends_online_inform, function(data){
    var tmp_data;
    try{
        tmp_data = JSON.parse(data);
    }
    catch(e){
        tmp_data = data;
    }
    data = tmp_data;
    if (data["type"] == 1) {
      showSuccessToast("恢复默认成功");
      $("#set_upload_speed").val("2.00");
      if(!$("#voice").hasClass('checked'))
        $("#voice").trigger("click");
      if($("#auto_log").hasClass('checked'))
        $("#auto_log").trigger("click");
      if($("#auto_login").hasClass('checked'))
        $("#auto_login").trigger("click");
      if(!$("#exit_tray").hasClass('checked'))
        $("#exit_tray").trigger("click");
      if(!$("#chat_robot").hasClass('checked'))
        $("#chat_robot").trigger("click");
      /*if($("#allow_v4_download").hasClass('checked'))
        $("#allow_v4_download").trigger("click");*/
      if(!$("#allow_bg").hasClass('checked'))
        $("#allow_bg").trigger("click");
      if(!$("#friends_online_inform").hasClass('checked'))
        $("#friends_online_inform").trigger("click");
      $("html").css("background", "url(images/fbt_bg1.png) fixed");
    } else {
      $('#text_download_path').text('无效下载路径');
    }
  },true); 
}
function handle(nick,id, sender, flag){
  //console.log($(".msg"+id));
  if(!$(".msg"+id).hasClass('unRead'))
  {
    showNoticeToast("消息已处理");
    return;
  }
  if(flag)
  {
    $(".msg"+id).each(function(index, el) {
      $(el).removeClass('unRead').addClass('read');
    });    
    var msg_count = $("li.dropdown > a.dropdown-toggle > span.msg_count");
    var count = window.parseInt(msg_count.html());
    if(count != 0)
      count --;
    msg_count.each(function(index, el) {
      $(el).html(count);
    });

    //跳转到聊天窗口
    $('a[href="/mySpace"]').trigger('click');
    var nickname = $('.msg' + id).first().text().replace(/给您发了一条私信.+/,'')
    $("b[onclick*='" + nickname + "']").first().trigger('click');
    return;
  }
  else if(nick == "0" && sender == "0")
  {
    var param = {};
    param["op"] = 6;
    param["id"] = id;
    $.post('/myFriend', param, function(data, textStatus, xhr) {
      $(".msg"+id).each(function(index, el) {
        $(el).removeClass('unRead').addClass('read');
      });    
      var msg_count = $("li.dropdown > a.dropdown-toggle > span.msg_count");
      var count = window.parseInt(msg_count.html());
      if(count != 0)
        count --;
      msg_count.each(function(index, el) {
        $(el).html(count);
      });
    });
    return;
  }
  var add = $("#addModal");
  add.find("#addModalNick").text(nick);
  add.find("#addModalOk").attr("mid",id);
  add.find("#addModalOk").attr("send",sender);
  add.modal("show");
}
function handleFriend(flag){
  var id = $("#addModal").find("#addModalOk").attr("mid");
  var sender = $("#addModal").find("#addModalOk").attr("send");
  var param = {};
  param["op"] = 2;
  param["user"] = sender;
  param["id"] = id;
  param["flag"] = flag;
  $("#addModal").modal("hide");
  $.post('/myFriend', param, function(data, textStatus, xhr) {
  /*optional stuff to do after success */
  //console.log(data);
  //data = $.parseJSON(data)
  if(data["type"] && data["type"] == 1)
  {
  $(".msg"+id).each(function(index, el) {
      $(el).removeClass('unRead').addClass('read');
    });
  /*data = $.parseJSON(data["result"])*/
  showSuccessToast(data["result"]["result"]);
  var msg_count = $("li.dropdown > a.dropdown-toggle > span.msg_count");
  var count = window.parseInt(msg_count.html());
  if(count != 0)
    count --;
  msg_count.each(function(index, el) {
    $(el).html(count);
  });
  }
  else{
  showErrorToast(data["error"]);
  }
  });
}
function clearAllMsg() {
  if($('.msg_count').text() === '0') {
      showSuccessToast('烦心事已清空, 心情不好就点我吧:)');
      return;
  }

  var param = {};
  param["op"] = 7;
  $.post('/myFriend', param, function(data, textStatus, xhr) {
    /*optional stuff to do after success */
    //console.log(data);
    //data = $.parseJSON(data)
    if(data["type"] && data["type"] == 1)
    {
      $('.msg_count').text('0');
      $('.msg > li:not(#clearAllMsg)').empty();
      showSuccessToast('清理成功, 整个世界都安静了 O(∩_∩)O');
    }
    else{
      showErrorToast(data["error"]);
    }
  });
}
