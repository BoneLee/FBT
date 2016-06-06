/*$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#login").on("click", function(event) {
    	if (validate()) {
            login();
        }
        return false;
    });
    $("#pwd").on("keypress", function(e) {
        if (e.keyCode == 13) {
            if (validate()) {
            login();
        }
            return false;
        }
    });
    $("#user").select();
    $(".alert").alert()
});*/
if (!window.console) window.console = {};
if (!window.console.log) window.console.log = function() {};

$("#login").on("click", function(event) {
    if (validate()) {
        login();
    }
    return false;
});
$("#pwd").on("keypress", function(e) {
    if (e.keyCode == 13) {
        if (validate()) {
        login();
    }
        return false;
    }
});
$("#user").select();
$(".alert").alert()
function validate(){
    if($("#user").val() == "" || $("#pwd").val() == "")
    {
        $("#hint").html("用户名或者密码未填写.");
        $(".alert").removeClass('hide').addClass('show');
        return false;
    }
    return true;
}
function login() {
    var message = {}
    message["user"] = $("#user").val();
    message["pwd"] = $("#pwd").val();
    message["next"] = "/"
    var disabled = $("#login");
    disabled.disable();
    $.postJSON("/login", message, function(response) {
        if(response != "0")
        {
        	$.get('/', function(data) {
                /*optional stuff to do after success */
                ws = new ReconnectingWebSocket('ws://localhost:8888/socket');
                ws.onopen = function(){
                    ws.send("{'type':'user','value':"+$("user").val()+"}");
                }
                ws.onmessage = function(event) {
                    alert(event.data);
                };
                $("#wrap_hide").html(data);
                $("#wrap_all").html($("#wrap_hide").find("#wrap_all").html());
            });
        }
        else{
            $("#hint").html("用户名或者密码错误.");
        	$(".alert").removeClass('hide').addClass('show');
            $("#user").val("");
            $("#pwd").val("");
        }
        disabled.enable();
    });
}
