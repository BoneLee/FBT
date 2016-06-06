/**
 * Created by bone on 15-5-12.
 */

function getCookie(name) {
    var c = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return c ? c[1] : undefined;
}

/**********************************************************************/
// POST JSON with csrf cookie
$(function(){
    $.ajaxSetup({"headers":{"X-CSRFToken": getCookie("_xsrf")}});
});

jQuery.postJSON = function (url, data, callback) {
    jQuery.ajax({
        url: url,
        data: JSON.stringify(data),
        dataType: "json",
        type: "POST",
        success: callback
    });
};

/*
jQuery.postJSON = function (url, data, callback) {
    data._xsrf = getCookie("_xsrf");
    jQuery.ajax({
        url: url,
        data: jQuery.param(data),
        dataType: "json",
        type: "POST",
        success: callback
    });
};
*/
/**********************************************************************/

function validateEmail(email) {
    var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
    return re.test(email);
}

function validateRegisterForm() {
    var name = $("#fbt_user").val();
    if (!validateEmail(name)) {
        $("#err_tips").html("您输入的邮箱无效，请重新输入！");
        return false;
    }
    $("#encrypted_passwd").val($.md5($("#fbt_passwd").val()));
    return true;
}

function validateLoginForm() {
    var name = $("#fbt_user").val();
    if (!validateEmail(name)) {
        $("#err_tips").html("您输入的邮箱无效，请重新输入！");
        return false;
    }
    $("#encrypted_passwd").val($.md5($("#fbt_passwd").val()));
    return true;
}