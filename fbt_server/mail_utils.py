#coding:utf-8
#! /usr/bin/env python
#################################################################################
#     File Name           :     mail_utils.py
#     Created By          :     DQ - D.Q.Zhang.chn@gmail.com
#     Creation Date       :     [2015-08-18 20:47]
#     Last Modified       :     [2015-08-19 19:52]
#     Description         :     所有发信都使用模板发信,发信前请创建好模板，触发发信使用template_send()函数，群发全用group_send()函数
#################################################################################

'''
webapi返回内容
# 请求成功
{
"message": "success",
...
}

# 请求失败
{
"message": "error",
"errors": {},
}
'''
import requests,json                                                             

API_KEY = 'AAV36hVJiwO8A7Fx'#所有的API—USER共用一个API-KEY 
TRIGER_API_USER = 'friendsbt'#触发发信
BATCH_API_USER = 'fbt_service'#批量发信

def common_send(mail_from, from_name, subject, html, to):
    url = "http://sendcloud.sohu.com/webapi/mail.send.json"
    params = {
        "api_user": TRIGER_API_USER, # 使用api_user和api_key进行验证                       
        "api_key" : API_KEY,                                             
        "from" : mail_from,
        "fromname" : from_name,
        "subject": subject,
        "html": html,
        "to": to,
        "resp_email_id": "true",
        "use_maillist":"false",
    }
    return requests.post(url, data=params)

#触发发信使用,返回response对象
def template_send(mail_from,from_name,template_name,sub_vars):
#sub_vars = {
#    'to': ['to1@domain.com', 'to2@domain.com'],
#    'sub': {
#        '%name%': ['user1', 'user2'],
#        '%money%': ['1000', '2000'],
#    }
#}
#如果模板中有参数需要替换，使用sub字段，如果模板无内容替换，不需要sub字段
#to字段请不要超过100个地址
    url = "http://sendcloud.sohu.com/webapi/mail.send_template.json"
    params = {
        "api_user": TRIGER_API_USER, # 使用api_user和api_key进行验证                       
        "api_key" : API_KEY,                                             
        "template_invoke_name" : template_name,
        "substitution_vars" : json.dumps(sub_vars),
        "from" : mail_from,
        "fromname" : from_name,
        "resp_email_id": "true",
        "use_maillist":"false",
    }
    #filename = "..."
    #display_filename = "..."
    #files = { "file1" : (display_filename, open(filename,"rb"))}
    #r = requests.post(url, files=files, data=params)

    return requests.post(url, data=params)

#群发,返回response对象
def group_send(mail_from,from_name,template_name,group_name):
    url = "http://sendcloud.sohu.com/webapi/mail.send_template.json"
    params = {
        "api_user":BATCH_API_USER,
        "api_key":API_KEY,
        "to":group_name,
        "from":mail_from,
        "fromname":from_name,
        "template_invoke_name":template_name,
        "use_maillist":"true",
        "resp_email_id":"true",
    }
    r = requests.post(url,data = params)
    return r

def test_template_send():
    mail_from = "fbt@mail.friendsbt.com"
    from_name = "fbt"
    template_name = "welcome_to_fbt"

    sub_vars = {

        "to" : ["459545754@qq.com"], # 收件人地址
        #邮件内容无需替换请注释掉sub字段
        #'sub': {
        #    '%name%': ['user1', 'user2'],
        #    '%money%': ['1000', '2000'],
        #}
    }
    r =  template_send(mail_from,from_name,template_name,sub_vars)
    print r.text

def test_group_send():
    mail_from = "fbt@mail.friendsbt.com"
    from_name = "fbt"
    template_name = "test_template_greet"
    group_name = "fbt_users@maillist.sendcloud.org"
    print group_send(mail_from,from_name,template_name,group_name).text

def test_common_send():
    url = "http://sendcloud.sohu.com/webapi/mail.send.json"                         
    params = {                                                                      
        "api_user": TRIGER_API_USER, # 使用api_user和api_key进行验证                       
        "api_key" : API_KEY,                                             
        "to" : "459545754@qq.com", # 收件人地址, 用正确邮件地址替代, 多个地址用';'分隔  
        "from" : "fbt@mail.friendsbt.com", # 发信人, 用正确邮件地址替代     
        "fromname" : "SendCloud",                                                    
        "subject" : "SendCloud python common",                              
        "html": "欢迎使用SendCloud",
        "resp_email_id": "true",
    }                                                                               

    r = requests.post(url, data=params)

    print r.text

if __name__ == '__main__':
    test_template_send()
