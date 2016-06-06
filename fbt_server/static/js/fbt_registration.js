/*$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $("#submit").on("click",function(){
        if (validate()) {
            registration();
        }
    });
    $("#confirmPassword").blur(function(event) {
        if ($("#password").val() != $(this).val()) {
            $("#checkmarkConfirm").html("密码不一致，请检查");
        }
        else
        {
            $("#checkmarkConfirm").html("");
        }
    });
    function validate(){
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        var value = $("#email").val();
        if($("#email").val() == "" || $("#password").val() == "" || $("#confirmPassword").val() == "")
        {
            $("#hint").html("用户名或者密码未填写.");
            $(".alert").removeClass('hide').addClass('show');
            return false;
        }
        else if (!emailReg.test(value)) {
            $("#hint").html("非法的邮箱格式.");
            $(".alert").removeClass('hide').addClass('show');
            return false;
        }
        return true;
    }
    $(".alert").alert()
});*/
if (!window.console) window.console = {};
if (!window.console.log) window.console.log = function() {};

$("#submit").on("click",function(){
    if (validate()) {
        registration();
    }
});
$("#confirmPassword").bind('blur',function(event) {
    /* Act on the event */
    if ($("#password").val() != $(this).val()) {
        $("#checkmarkConfirm").html("密码不一致，请检查");
    }
    else
    {
        $("#checkmarkConfirm").html("");
    }
});
function validate(){
    var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
    var value = $("#email").val();
    if($("#email").val() == "" || $("#password").val() == "" || $("#confirmPassword").val() == "")
    {
        $("#hint").html("用户名或者密码未填写.");
        $(".alert").removeClass('hide').addClass('show');
        return false;
    }
    else if (!emailReg.test(value)) {
        $("#hint").html("非法的邮箱格式.");
        $(".alert").removeClass('hide').addClass('show');
        return false;
    }
    return true;
}
$(".alert").alert()
function registration() {
    var message = {}
    message["user"] = $("#email").val();
    message["pwd"] = $("#password").val();
    message["nick"] = $("#nickName").val()
    message["next"] = "/login"
    var disabled = $("#submit");
    disabled.disable();
    $.postJSON("/registration", message, function(response) {
        if(response != "0" && response != "2")
        {
            location.href = "/login";
        }
        else if (response == "2") {
            $("#checkmarkEmail").html("用户名已存在");
        }
        else{
            $("#hint").html("用户名或者密码未填写.");
            $(".alert").removeClass('hide').addClass('show');
        }
        disabled.enable();
    });
}