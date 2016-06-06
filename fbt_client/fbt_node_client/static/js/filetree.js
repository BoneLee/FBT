var selectedFiles;
function downloadFolderExplorer(folderExplorer, treeData, dirName, dirHash, dirSize, isPrivate, flag) {
folderExplorer.fancytree({
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
      source: treeData,
      renderColumns: function(event, data) {
        var node = data.node,
        $tdList = $(node.tr).find(">td");
        // (index #0 is rendered by fancytree by adding the checkbox)
        //$tdList.eq(1).text(node.getIndexHier()).addClass("alignRight");
        // (index #2 is rendered by fancytree)
        /*
        $tdList.eq(1).find('span:last-child')
        .css({//'cursor': 'pointer',
                 'display': 'inline-block',
                 'width': '260px',
                 'white-space': 'nowrap',
                 'overflow-x': 'hidden',
                 'text-overflow': 'ellipsis',
                 'position': 'relative'
               })
        .attr({'title': node.data['title']});
        */

        $tdList.eq(2).text(node.data['file_size']).css("text-align", "center");
        $tdList.eq(3).text(node.data['download_num']).css("text-align", "center");
        var online_owners_num =  node.data['online_owners_num'];
        var all_owner_num =  node.data['all_owner_num'];
        if (all_owner_num || online_owners_num)
          $tdList.eq(4).text([online_owners_num, all_owner_num].join('/')).css("text-align", "center");
      },
      select: function(event, data) {
        var filesCount = 0;
        data.tree.visit(function(node){
          if(!node.folder) filesCount += 1;
        });
        selectedFiles = $.map(data.tree.getSelectedNodes(), function(node){
          if(node.folder) return null;
          return node.key;
        });
        // Download callback
        $('#btn-download-selected-files').text('下载(' + selectedFiles.length + '/' + filesCount + ')');
      }
    });
  // select all(default)
  /*$('#folder-explorer').fancytree('getTree').visit(function(node){
    node.setSelected(true);
  });*/
  /*$('#btn-select-all').click(function() {
    $('#folder-explorer').fancytree('getTree').visit(function(node){
      node.setSelected(true);
    });
    return false;
  });
  $('#btn-deselect-all').click(function() {
      $('#folder-explorer').fancytree('getTree').visit(function(node){
        node.setSelected(false);
      });
      return false;
  });*/
  var cancel = $('#btn-cancel-download');
  cancel.unbind(".folder_c");
  cancel.bind("click.folder_c",function() {
    $('#folderModal').modal('hide');
  });
  var confirm = $("#btn-download-selected-files");
  confirm.unbind(".folder_o");
  confirm.bind("click.folder_o",function(){
    $('#folderModal').modal('hide');
    var fileHashs = [], fileSizes=[];
    for(var i in selectedFiles){
      var item = selectedFiles[i];
      //var dirId = gen_file_id(dirHash, dirSize);
      /*if(dirId in window.downloadFolder && item in window.downloadFolder[dirId])
        continue;*/
      item = item.split("_");
      fileHashs.push(item[0]);
      fileSizes.push(item[1]);
    }
    if(fileHashs.length == 0){
      showWarningToast("oops~请选择至少一个文件");
      return;
    }
    fileHashs = fileHashs.join(",");
    fileSizes = fileSizes.join(",");
    downloadFile(true,dirName,fileHashs,fileSizes,dirSize,flag,
      dirHash,isPrivate);
  });
}

function createFileItem(){
  
}

function showDir(my_uid, dirName, dirHash, dirSize, isPrivate, flag, forceShowDir){
  var whichHtmlElement = dirHash+flag.trim()+dirSize;
  if(!forceShowDir){
    var obj = $("#download_file_hash"+whichHtmlElement);
    if(parseInt(obj.attr("data")) == 1 && (!obj[0].hasAttribute('error') || parseInt(obj.attr('error')) != 1) && $("#collapseMyDownload"+whichHtmlElement).is(':hidden'))
      handleComment(dirHash,3,flag,dirSize);
    var isDownloading = obj.attr("download");
    //console.log(isDownloading);
    if(parseInt(obj.attr("data")) == 1 && isDownloading){
      viewFolderDownload(dirName, gen_file_id(dirHash,dirSize));
      return;
    }
  }
  $('#folderModal').modal({
      backdrop: 'static'
    });
  clearHistory("#folder-explorer","folder-loading", "folder-error", 0);
  $("#folder-loading").show();
  var param = {};
  param["dirHash"] = dirHash;
  param["dirSize"] = dirSize;
  if(my_uid != 0)
    param["uid"] = my_uid;
  //console.log(param);
  $.post('/getDirDetail', param, function(data, textStatus, xhr) {
    $("#folder-loading").hide();
    var tmp;
    try{
      tmp = JSON.parse(data);
    }
    catch(e){
      tmp = data;
    }
    //console.log(tmp);
    if(tmp["type"] == 0)
    {
      if(tmp["error"])
        $("#folder-error").html(tmp["error"]);
      else
        $("#folder-error").html("获取文件夹信息失败，请重试");
    }
    else
    {
      var dirId = gen_file_id(dirHash, dirSize);
      var shouldSave = true;
      if(dirId in window.downloadFolderName)
        shouldSave = false;
      else
        window.downloadFolderName[dirId] = {};      
      var children = [];
      for(var i in tmp["result"]){
        var item = tmp["result"][i];
        var one_file = {};
        one_file['title'] = item["file_name"];
        one_file["key"] = gen_file_id(item["file_hash"], item["file_size"]);
        one_file["file_size"] = normalizeFileSize(item["file_size"]);
        one_file['download_num'] = item["download_num"];
        one_file["online_owners_num"] =  item['online_owners_num'];
        one_file['all_owner_num'] =  item['all_owner_num'];
        /*
        one_file["title"] = item["file_name"]+" 下载总数："+item["download_num"]+
        " 在线/总数："+item["online_owners_num"]+"/"+item["all_owner_num"];
        */
        children.push(one_file);
        if(shouldSave)
          window.downloadFolderName[dirId][one_file["key"]] = item["file_name"];
      }
      var folder = {
        title: dirName,
        folder: true,
        "file_size": dirSize,
        expanded: true,
        children: children
      }
      var fill = [folder];
      $("#btn-download-selected-files").text('下载(0/' + children.length + ')');
      downloadFolderExplorer($("#treetable"), fill, dirName, dirHash, dirSize, isPrivate, flag);
    }
  });
}

function viewFolderExplorer(folderExplorer, treeData) {
  folderExplorer.fancytree({
      extensions: ["table"],
      checkbox: false,
      autoCollapse: true,
      autoScroll: true,
      selectMode: 3,
      table: {
        //indentation: 20,      // indent 20px per node level
        nodeColumnIdx: 0,     // render the node title into the 1nd column
      },
      source: treeData,
      renderColumns: function(event, data) {
        var node = data.node,
        $tdList = $(node.tr).find(">td");
        // (index #0 is rendered by fancytree by adding the checkbox)
        //$tdList.eq(1).text(node.getIndexHier()).addClass("alignRight");
        // (index #2 is rendered by fancytree)
        /*
        $tdList.eq(1).find('span:last-child')
        .css({//'cursor': 'pointer',
                 'display': 'inline-block',
                 'width': '260px',
                 'white-space': 'nowrap',
                 'overflow-x': 'hidden',
                 'text-overflow': 'ellipsis',
                 'position': 'relative'
               })
        .attr({'title': node.data['title']});
        */

        $tdList.eq(1).text(node.data['size']).css("text-align", "center");
        $tdList.eq(2).text(node.data['progress']).css("text-align", "center");
      }
  });
}

function viewFolderDownload(dirName, dirId){
  /*if(!isTimeOut)
  {
    $('#folderViewModal').modal();
    $("#folder-view-loading").show();
  }
  if(!window.downloadFolderFlag[dirId]["canShow"])
  {
    setTimeout("viewFolderDownload(dirId, true)", 2000);
    return;
  }*/
  $('#folderViewModal').modal({
      backdrop: 'static'
    });
  clearHistory("#folder-view-explorer","folder-view-loading", "folder-view-error", 1);
  var fileInfo = window.downloadFolder[dirId];
  //console.log(window.downloadFolder);
  //console.log(fileInfo);
  var children = [];
  for(var i in fileInfo){
    var item = fileInfo[i];
    var one_file = {};
    one_file["key"] = i;
    one_file["title"] = item["fileName"];
    one_file["size"] = item["fileSize"];
    if(window.parseInt(item["complete"]) === 0){
      if("progress" in item)
        one_file["progress"] = item["progress"] +"%";
      else{
        one_file["progress"] = "排队中";
      }
    }
    else
      one_file["progress"] = "已下完";
    children.push(one_file);
  }
  var folder = {
    title: dirName,
    folder: true,
    expanded: true,
    children: children
  }
  var fill = [folder];
  viewFolderExplorer($("#treetable-view"), fill);
}
