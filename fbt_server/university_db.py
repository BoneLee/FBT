# -*- coding: utf-8 -*-

from singleton import singleton
from constant import CDN_URL

import simplejson as json
from random import sample
from tornado.escape import utf8, to_unicode
from pypinyin import pinyin, TONE2, lazy_pinyin
import os
import jieba


class MemSearcher(object):
    # https://github.com/fengli/autocomplete-redis/blob/master/autocomplete/index.py
    _all_words_dict = dict()
    _all_words_array = list()

    def __init__(self):
        self._index_key = dict()

    def gen_uid_for(self, word):
        word = word.lower()
        if word not in self._all_words_dict:
            self._all_words_array.append(word)
            uid = len(self._all_words_array) - 1
            self._all_words_dict[word] = uid
        return self._all_words_dict[word]

    def index(self, text):
        text = text.lower()
        text_id = self.gen_uid_for(text)
        for prefix in self.prefixs_for_term(text):
            if prefix not in self._index_key:
                self._index_key[prefix] = set()
            self._index_key[prefix].add(text_id)
    
    def prefixs_for_term (self, text):
        """
        Get prefixs for TERM.
        """
        text = text.lower()
        text = to_unicode(text)
        return text
        '''
        words = list(jieba.cut_for_search(text))  # 搜索引擎模式
        for word in jieba.cut(text, cut_all=True): # 精确模式
            if word not in words:
                words.append(word)
        prefixs = []
        for word in words:
            for i in xrange (1,len(word)+1):
                prefixs.append(word[:i])
        return prefixs
        '''

    def remove(self, item):
        text = text.lower()
        for prefix in self.prefixs_for_term(text):
            if prefix in self._index_key:
                self._index_key[prefix].remove(text)

    def search(self, text):
        text = text.lower()
        words = self.prefixs_for_term(text)
        #words = list(jieba.cut(text, cut_all=True))  # 精确模式
        if not words:
            return []
        ret = set()
        for word in words:
            #print word
            if word not in self._index_key:
                return []
            if not ret:
                ret = self._index_key[word]
            else:
                ret = ret.intersection(self._index_key[word])
        return [self._all_words_array[i] for i in ret]


@singleton
class UniversityDB(object):
    def __init__(self):
        self._universities = set()
        self._college_of_university = {}
        self._university_of_province = {}
        self._short_universities_dict = {}
        self._mem_searcher = MemSearcher()
        self._985_university = { # 39
            "北京大学",
            "北京航空航天大学",
            "北京理工大学",
            "北京师范大学",
            "大连理工大学",
            "电子科技大学",
            "东北大学",
            "东南大学",
            "复旦大学",
            "国防科学技术大学",
            "哈尔滨工业大学",
            "湖南大学",
            "华东师范大学",
            "华南理工大学",
            "华中科技大学",
            "吉林大学",
            "兰州大学",
            "南京大学",
            "南开大学",
            "清华大学",
            "厦门大学",
            "山东大学",
            "上海交通大学",
            "四川大学",
            "天津大学",
            "同济大学",
            "武汉大学",
            "西安交通大学",
            "西北工业大学",
            "西北农林科技大学",
            "浙江大学",
            "中国海洋大学",
            "中国科学技术大学",
            "中国农业大学",
            "中国人民大学",
            "中南大学",
            "中山大学",
            "中央民族大学",
            "重庆大学",
            "星环大学"}
        self._211_university = { #112
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
            "国防科学技术大学"}
        self._university_short = { 
            "清华大学":[u"清华"],
            "北京大学":[u"北大"],
            "中国人民大学":[u"人大"],
            "北京交通大学":[u"北交"],
            "北京工业大学":[u"北工大"],
            "北京航空航天大学":[u"北航"],
            "北京理工大学":[u"北理"],
            "北京科技大学":[u"北科大"],
            "北京化工大学":[u"北化",u"化大"],
            "北京邮电大学":[u"北邮"],
            "中国农业大学":[u"中国农大"],
            "北京林业大学":[u"北林"],
            "中国传媒大学":[u"北广",u"中传",u"广院"],
            "中央民族大学":[u"民大"],
            "北京师范大学":[u"北师大"],
            "中央音乐学院":[u"中音"],
            "对外经济贸易大学":[u"对外经贸",u"外经贸",u"贸大"],
            "北京中医药大学":[u"中医药大学",u"北中医"],
            "北京外国语大学":[u"北外"],
            "中国地质大学（北京）":[u"地大",u"中国地大"],
            "中国政法大学":[u"法大"],
            "中央财经大学":[u"中央财大",u"中财大",u"中财"],
            "华北电力大学":[u"华电",u"华北电大"],
            "北京体育大学":[u"北体"],
            "上海外国语大学":[u"上外",u"西索"],
            "复旦大学":[u"复旦"],
            "华东师范大学":[u"华师",u"华师大"],
            "上海大学":[u"上大"],
            "东华大学":[u"东华大学"],
            "上海财经大学":[u"上财"],
            "华东理工大学":[u"华东理工",u"华理"],
            "同济大学":[u"同济"],
            "上海交通大学":[u"上交"],
            "南开大学":[u"南开"],
            "天津大学":[u"天大"],
            "天津医科大学":[u"天津医大"],
            "重庆大学":[u"重大"],
            "西南大学":[u"西大",u"西南大"],
            "河北工业大学":[u"河工大"],
            "太原理工大学":[u"太原理工"],
            "内蒙古大学":[u"内大"],
            "大连理工大学":[u"大连理工",u"大工"],
            "东北大学":[u"东大"],
            "辽宁大学":[u"辽大"],
            "大连海事大学":[u"大连海大"],
            "吉林大学":[u"吉大"],
            "东北师范大学":[u"东北师大"],
            "延边大学":[u"延大"],
            "哈尔滨工业大学":[u"哈工大"],
            "哈尔滨工程大学":[u"哈工程"],
            "东北农业大学":[u"东农"],
            "东北林业大学":[u"林大",u"东林",u"林业大学",u"东北林大"],
            "南京大学":[u"南大"],
            "东南大学":[u"东大"],
            "苏州大学":[u"苏大"],
            "南京师范大学":[u"南师大"],
            "中国矿业大学":[u"中国矿大",u"矿大"],
            "中国药科大学":[u"药大"],
            "河海大学":[u"河海"],
            "南京理工大学":[u"南理工",u"南炮工"],
            "江南大学":[u"江大"],
            "南京农业大学":[u"南农",u"南农大"],
            "南京航空航天大学":[u"南航"],
            "浙江大学":[u"浙大"],
            "中国科学技术大学":[u"中科大"],
            "安徽大学":[u"安大"],
            "合肥工业大学":[u"合工大"],
            "厦门大学":[u"厦大"],
            "福州大学":[u"福大"],
            "南昌大学":[u"昌大"],
            "山东大学":[u"山大"],
            "中国海洋大学":[u"中海大"],
            "中国石油大学（华东）":[u"石大"],
            "中国石油大学（北京）":[u"石大"],
            "郑州大学":[u"郑大"],
            "武汉大学":[u"武大"],
            "华中科技大学":[u"华科",u"华中大"],
            "武汉理工大学":[u"武理工"],
            "中南财经政法大学":[u"中南大",u"中南财大"],
            "华中师范大学":[u"华师"],
            "华中农业大学":[u"华中农大",u"华农"],
            "中国地质大学（武汉）":[u"地大"],
            "湖南大学":[u"湖大"],
            "中南大学":[u"中南"],
            "湖南师范大学":[u"湖南师大"],
            "中山大学":[u"中大"],
            "暨南大学":[u"暨大",u"国立暨南"],
            "华南理工大学":[u"华南理工",u"华工大"],
            "华南师范大学":[u"华师",u"华南师大"],
            "广西大学":[u"西大"],
            "四川大学":[u"川大"],
            "西南交通大学":[u"西南交大"],
            "电子科技大学":[u"电子科大"],
            "四川农业大学":[u"川农"],
            "西南财经大学":[u"西财",u"苏菲",u"西南财大"],
            "云南大学":[u"云大"],
            "贵州大学":[u"贵大"],
            "西北大学":[u"西北大学"],
            "西安交通大学":[u"西交"],
            "西北工业大学":[u"西工大"],
            "长安大学":[u"长大"],
            "西北农林科技大学":[u"西北农大"],
            "陕西师范大学":[u"陕师大"],
            "西安电子科技大学":[u"西电"],
            "兰州大学":[u"兰大"],
            "海南大学":[u"海大"],
            "宁夏大学":[u"宁大"],
            "青海大学":[u"青大"],
            "西藏大学":[u"藏大"],
            "新疆大学":[u"新大"],
            "石河子大学":[u"石河子大学"],
            "第二军医大学":[u"第二军医大学",u"二医大"],
            "第四军医大学":[u"四医大"],
            "国防科学技术大学":[u"国防科大",u"国防科技大"],
            }
        self._load_university_data()
        for u in self._985_university:
            assert u in self._universities
        for u in self._211_university:
            assert u in self._universities

        path = "static/images/university/"
        self._img_of_university = {}
        for k,university_id in self._university_id.iteritems():
            file_path = path+str(university_id)+".jpg"
            if os.path.isfile(file_path):
                self._img_of_university[k] = CDN_URL + file_path
            else:
                default_icon = "0.jpg"
                self._img_of_university[k] = CDN_URL + path+default_icon
        for u in self._university_short:
            for short_name in self._university_short[u]:
                if short_name not in self._short_universities_dict:
                    self._short_universities_dict[short_name] = []
                self._short_universities_dict[short_name].append(u)

    def _load_university_data(self):
        dir = os.path.dirname(__file__)
        json_file = os.path.join(dir,  "static/json/university.json")
        with open(json_file,'r') as f:
            data = json.load(f)

        json_of_university_id = os.path.join(dir, "static/json/university_id.json")
        with open(json_of_university_id,'r') as f:
            self._university_id=json.load(f)

        json_of_college_id = os.path.join(dir, "static/json/college_id.json")
        with open(json_of_college_id,'r') as f:
            self.college_id=json.load(f)

        college_of_university = data["college_of_university"]
        for university in college_of_university:
            self._universities.add(utf8(university))
            self._mem_searcher.index(university)
            if utf8(university) not in self._college_of_university:
                self._college_of_university[utf8(university)]=set()
            for college in college_of_university[university]:
                self._college_of_university[utf8(university)].add(utf8(college))

        university_of_province = data["university_of_province"]
        for province in university_of_province:
            university_of_province[province] = sorted(university_of_province[province], key=lambda x: pinyin(to_unicode(x), style=TONE2))
            self._university_of_province[utf8(province)] = [utf8(university) for university in university_of_province[province]]

    def random_choose_college_of_university(self, university=None):
        if university is None:
            university = sample(self._universities, 1)[0]
        college = sample(self._college_of_university[university], 1)[0]
        assert self.is_valid_university_and_college(university, college)
        return university, college

    def is_valid_university(self, university):
        university = utf8(university)
        return university in self._universities

    def is_valid_university_and_college(self, university, college):
        university = utf8(university)
        college = utf8(college)
        if university in self._universities:
            if self._college_of_university[university]:
                return college in self._college_of_university[university]
            else:
                return True
        else:
            return False

    def get_university_by_province(self, province, need_pinyin=True):
        if province in self._university_of_province:
            if need_pinyin:
                return [{"university": u, "pinyin": self.to_pinyin(u)}
                        for u in self._university_of_province[province]]
            else:
                return sorted(self._university_of_province[province], key=lambda x: pinyin(to_unicode(x), style=TONE2))
        else:
            return []

    def get_college_by_university(self, university, need_pinyin=True):
        university=utf8(university)
        if university in self._universities:
            if need_pinyin:
                colleges = []
                for c in (self._college_of_university[university]):
                    c = to_unicode(c)
                    colleges.append({"college": c, "pinyin":  self.to_pinyin(c)})
                return sorted(colleges, key=lambda x: pinyin(x["college"], style=TONE2))
            else:
                return sorted(list(self._college_of_university[university]), key=lambda x: pinyin(to_unicode(x), style=TONE2))
        else:
            return []

    def get_university(self, keyword=None):
        if keyword:
            # keyword = utf8(keyword)
            universities = []
            for university in self._mem_searcher.search(keyword):
                if self.is_985(university):
                    universities.insert(0, university)
                elif self.is_211(university):
                    universities.insert(0, university)
                else:
                    universities.append(university)
            return universities
        else:
            return self._universities

    def get_211university(self, keyword=None):
        if keyword:
            universities = [university for university in self._211_university if self.university_has_keyword(keyword, university)]
            return universities
        else:
            return self._211_university

    def get_985university(self, keyword=None):
        if keyword:
            universities = [university for university in self._985_university if self.university_has_keyword(keyword, university)]
            return universities
        else:
            return self._985_university

    def to_pinyin(self, word):
        ret = ""
        for py in (lazy_pinyin(to_unicode(word))):
            ret += py[0]
        return ret
        # return u" ".join(lazy_pinyin(to_unicode(word)))

    def university_has_keyword(self, keyword, university):
        keyword = to_unicode(keyword)
        university = to_unicode(university)
        university_by_pinyin = self.to_pinyin(university)
        return self.is_continuous_substr(keyword, university) or \
            self.is_continuous_substr(keyword, university_by_pinyin)

    def is_continuous_substr(self, keyword, string):
        i = j = 0
        while i < len(keyword):
            try:
                index = string.index(keyword[i], j)
                j = index + 1
                i += 1
            except ValueError as e:
                return False
        return True

    def is_211(self, university):
        university = utf8(university)
        return university in self._211_university or ("中国科学院" in university)

    def is_985(self, university):
        university = utf8(university)
        return university in self._985_university

    def get_college(self, university):
        university = utf8(university)
        return self._college_of_university[university]

    def get_university_icon(self, university):
        university = to_unicode(university)
        # print university
        return self._img_of_university[university]

    def get_university_id(self, university):
        university = to_unicode(university)
        return self._university_id.get(university,-1)

    def get_college_id(self, university, college):
        university_id=str(self.get_university_id(university))
        if university_id=='-1' or university_id not in self.college_id:
            return -1
        return self.college_id[university_id].get(to_unicode(college), -1)

    def get_short_name(self, university):
        university = utf8(university)
        if university in self._university_short:
            return self._university_short[university]
        elif university == "中国科学院":
            return [u"中科院"]
        else:
            return []
        # giv me unicde
        # return [u"中科大",u"科大"]

    def get_complete_name(self, short_name):
        short_name = to_unicode(short_name)
        if short_name in self._short_universities_dict:
            return self._short_universities_dict[short_name]
        else:
            return []

if __name__ == "__main__":
    udb = UniversityDB()
    print udb.is_valid_university_and_college("北京大学", "法律自考部")
    print udb.get_university_id("中国传媒大学")
    print udb.get_university_id("河北大学")
    print udb.get_college_id("中国传媒大学", "通信工程系")
    print udb.get_college_id("河北大学", "电子信息工程学院")
    m_search = MemSearcher()
    m_search.index("中国科学院大学")
    m_search.index("中国科学院")
    m_search.index("中国科学院大学")
    m_search.index("北京大学")
    m_search.index("清华大学")
    m_search.index("电子科技大学")
    m_search.index("长江师范学苑")
    m_search.index("北京林业大学")
    m_search.index("东北林业大学")
    for w in m_search.search("国科大"):
        print w
    print "**************************"
    for w in m_search.search("中科院"):
        print w
    print "**************************"
    for w in m_search.search("北大"):
        print w
    print "**************************"
    for w in m_search.search("清华大学"):
        print w
    print "**************************"
    for w in m_search.search("清华"):
        print w
    print "**************************"
    for w in m_search.search("电子科大"):
        print w
    print "**************************"
    for w in m_search.search("长江师苑"):
        print w
    print "**************************"
    for w in m_search.search("林业大学"):
        print w
    print "**************************"
    for w in m_search.search("大学林业"):
        print w
    print "**************************"
