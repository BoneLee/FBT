function executeScript(html)
{
    var reg = /<script[^>]*>([^\x00]+)$/i;
    //对整段HTML片段按<\/script>拆分
    var htmlBlock = html.split("<\/script>");
    for (var i in htmlBlock)
    {
        var blocks;//匹配正则表达式的内容数组，blocks[1]就是真正的一段脚本内容，因为前面reg定义我们用了括号进行了捕获分组
        if( (blocks = htmlBlock[i].match(reg)) )
        {
            //清除可能存在的注释标记，对于注释结尾-->可以忽略处理，eval一样能正常工作
            var code = blocks[1].replace(/<!--/, '');
            try
            {
                eval(code); //执行脚本
            }
            catch (e)
            {
            }
        }
    }
}
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}
jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
        if (callback) callback(response);
    }, error: function(response) {
        console.log("ERROR:", response);
    }});
};
jQuery.post = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), type: "POST",
            success: function(response) {
        if (callback) callback(response);
    }, error: function(response) {
        console.log("ERROR:", response);
    }});
};
jQuery.get = function(url, callback) {
    url = url + "?_xsrf=" + getCookie("_xsrf");
    $.ajax({url: url, type: "GET", success: function(response) {
        if(callback) callback(response);
        $("a").click(function(e){
            if($(this).attr("href") && $(this).attr("href").charAt(0) == '/'){
                e.preventDefault();
                $.get($(this).attr("href"), function(data) {
                    /*optional stuff to do after success */
                    //$(".wrap_hide").html(data);
                    $(".wrap_hide").get(0).innerHTML = data;
                    var d = $("body > div.wrap_hide").find(".wrap_all").html();
                    $("body > div.wrap_all").html(d);
                    $(".wrap_hide").html("");
                });
                return false;
            }
            else{
                $(this).click();
            }
        });
    }, error: function(response) {
        console.log("ERROR:", response);
    }});
};

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {};
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

jQuery.fn.disable = function() {
    this.enable(false);
    return this;
};

jQuery.fn.enable = function(opt_enable) {
    if (arguments.length && !opt_enable) {
        this.attr("disabled", "disabled");
    } else {
        this.removeAttr("disabled");
    }
    return this;
};
$(function(){
    $("a").click(function(e){
        if($(this).attr("href") && $(this).attr("href").charAt(0) == '/'){
            e.preventDefault();
            $.get($(this).attr("href"), function(data) {
                /*optional stuff to do after success */
                //$(".wrap_hide").html(data);
                $(".wrap_hide").get(0).innerHTML = data;
                var d = $("body > div.wrap_hide").find(".wrap_all").html();
                $("body > div.wrap_all").html(d);
                $(".wrap_hide").html("");
            });
            return false;
        }
        else{
            $(this).click();
        }
    });
});
function quit(){
    $.get('/logout?_xsrf = '+getCookie("_xsrf"), function(data) {
        /*optional stuff to do after success */
        console.log(data);
        data = JSON.parse(data);
        if(data["type"] && data["type"] == 1){
            location.href = "/login";
        }
    });
}
function getJsonLength(jsonData){

var jsonLength = 0;

for(var item in jsonData){

jsonLength++;

}

return jsonLength;

}
function createSock(){
    if(!window.ws){
      window.ws = new ReconnectingWebSocket('ws://friendsbt.com/socket');
      ws.onopen = function(){
          ws.send( "0"+$("b.user").html());
      };
      ws.onmessage = function(event) {
          console.log(event.data);
          var data = JSON.parse(event.data);
          if(data["id"]){
            var li = '<li><b class="unRead" onclick="handle('+data["id"]+', '+data["sender"]+')">'+data["content"]+'&nbsp;'+data["time"]+'</b></li>';
            $(".msg").prepend(li);
            var count = parseInt($(".msg_count").html()) + 1;
            $(".msg_count").html(count);
          }
          else{
            alert(data["msg"]);
          }
      };
      ws.onclose = function(event){
        console.log(event);
        delete window.ws;
      };
    }
}
