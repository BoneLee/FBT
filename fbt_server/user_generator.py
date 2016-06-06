# -*- coding: utf-8 -*-
__author__ = 'GuoHuan'

import os
import random
import pypinyin

from users_manager import UserManager

boy_img_path = 'static/images/user_icon2/boy_head_img'
girl_img_path = 'static/images/user_icon2/girl_head_img'

psw = '96e79218965eb72c92a549dd5a330112'  # 111111 -> md5

university_211 = [  # 112
                    "清华大学",
                    "北京大学",
                    "中国人民大学",
                    "北京交通大学",
                    "北京工业大学",
                    "北京航空航天大学",
                    "北京理工大学",
                    "北京科技大学",
                    "北京化工大学",
                    "北京邮电大学",
                    "中国农业大学",
                    "北京林业大学",
                    "中国传媒大学",
                    "中央民族大学",
                    "北京师范大学",
                    "中央音乐学院",
                    "对外经济贸易大学",
                    "北京中医药大学",
                    "北京外国语大学",
                    "中国地质大学（北京）",
                    "中国政法大学",
                    "中央财经大学",
                    "华北电力大学",
                    "北京体育大学",
                    "上海外国语大学",
                    "复旦大学",
                    "华东师范大学",
                    "上海大学",
                    "东华大学",
                    "上海财经大学",
                    "华东理工大学",
                    "同济大学",
                    "上海交通大学",
                    "南开大学",
                    "天津大学",
                    "天津医科大学",
                    "重庆大学",
                    "西南大学",
                    "河北工业大学",
                    "太原理工大学",
                    "内蒙古大学",
                    "大连理工大学",
                    "东北大学",
                    "辽宁大学",
                    "大连海事大学",
                    "吉林大学",
                    "东北师范大学",
                    "延边大学",
                    "哈尔滨工业大学",
                    "哈尔滨工程大学",
                    "东北农业大学",
                    "东北林业大学",
                    "南京大学",
                    "东南大学",
                    "苏州大学",
                    "南京师范大学",
                    "中国矿业大学",
                    "中国药科大学",
                    "河海大学",
                    "南京理工大学",
                    "江南大学",
                    "南京农业大学",
                    "南京航空航天大学",
                    "浙江大学",
                    "中国科学技术大学",
                    "安徽大学",
                    "合肥工业大学",
                    "厦门大学",
                    "福州大学",
                    "南昌大学",
                    "山东大学",
                    "中国海洋大学",
                    "中国石油大学（华东）",
                    "中国石油大学（北京）",
                    "郑州大学",
                    "武汉大学",
                    "华中科技大学",
                    "武汉理工大学",
                    "中南财经政法大学",
                    "华中师范大学",
                    "华中农业大学",
                    "中国地质大学（武汉）",
                    "湖南大学",
                    "中南大学",
                    "湖南师范大学",
                    "中山大学",
                    "暨南大学",
                    "华南理工大学",
                    "华南师范大学",
                    "广西大学",
                    "四川大学",
                    "西南交通大学",
                    "电子科技大学",
                    "四川农业大学",
                    "西南财经大学",
                    "云南大学",
                    "贵州大学",
                    "西北大学",
                    "西安交通大学",
                    "西北工业大学",
                    "长安大学",
                    "西北农林科技大学",
                    "陕西师范大学",
                    "西安电子科技大学",
                    "兰州大学",
                    "海南大学",
                    "宁夏大学",
                    "青海大学",
                    "西藏大学",
                    "新疆大学",
                    "石河子大学",
                    "第二军医大学",
                    "第四军医大学",
                    "国防科学技术大学"]


class UserGenerator(object):
    def __init__(self):
        self.um = UserManager()
        self.mail_postfix = ['163', '126', 'qq', 'gmail', 'sina']
        self.family_names = self.filein('familyname.txt')
        self.boy_names = self.filein('boyname.txt')
        self.girl_names = self.filein('girlname.txt')
        self.boy_imgs = self.get_img_files(boy_img_path)
        self.girl_imgs = self.get_img_files(girl_img_path)

    def generate_user(self, university=None, gender="女"):
        if gender == "女":
            name = self.family_names[int(random.uniform(0, len(self.family_names)))] + self.girl_names[
                int(random.uniform(0, len(self.girl_names)))]
            pic = self.girl_imgs[int(random.uniform(0, len(self.girl_imgs)))]
        else:
            name = self.family_names[int(random.uniform(0, len(self.family_names)))] + self.boy_names[
                int(random.uniform(0, len(self.boy_names)))]
            pic = self.boy_imgs[int(random.uniform(0, len(self.boy_imgs)))]
        pinyin = pypinyin.slug(name.decode('utf-8'), separator='')
        mail = '%s%d@%s.com' % (pinyin, random.uniform(1000000000, 9999999999),
                                self.mail_postfix[int(random.uniform(0, len(self.mail_postfix)))])
        if not university:
            school = university_211[int(random.uniform(0, len(university_211)))]
        else:
            school = university
        # print(mail, psw, pic, name, school, '', name, gender)
        # uid = 1234
        uid = self.um.register_user_sync(mail, psw, pic, name, school, '', name, gender)
        return {
            'user': mail,
            'icon': pic,
            'real_name': name,
            'university': school,
            'uid': uid
        }

    def filein(self, file_name):
        lst = []
        with file(file_name) as fin:
            for line in fin.readlines():
                lst.append(line.strip())
        return lst

    def get_img_files(self, path):
        lst = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith('.jpg'):
                    fname = os.path.join(root, f)
                    lst.append(fname)
                    # lst.append(f)
        return lst
