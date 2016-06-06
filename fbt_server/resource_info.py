# -*- coding: utf-8 -*-

__author__ = 'bone-lee'

class ResourceInfo(object):
    '''
    enum type
    '''
    _main_type = {0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其他"}
    _sub_type = {0: "标清", 1: "高清", 2: "超高清"}
    _all_tag = {
        "电影": ["喜剧", "古装", "伦理", "恐怖", "纪录片", "爱情", "动作", "科幻", "武侠", "战争", "犯罪", "惊悚", "剧情", "玄幻", "冒险", "动画"],
        "剧集": ["喜剧", "古装", "伦理", "武侠", "纪录片", "玄幻", "冒险", "警匪", "军事", "神话", "科幻", "搞笑", "偶像", "悬疑", "历史", "儿童", "都市", "家庭", "言情"],
        "学习": ["公开课","名人名嘴","艺术","伦理社会","理工农医","文史哲法","经管","课件","计算机","职业培训","家庭教育","其他"],
        "音乐": ["流行","摇滚","舞曲","电子","HIP-HOP","乡村","民族","古典","音乐剧","轻音乐"],
        "动漫": ["热血","恋爱","搞笑","LOLI","神魔","科幻","真人","美少女","运动","亲子","励志","剧情","校园","历史"],
        "游戏": ["动作","冒险","模拟","角色扮演","休闲","其他"],
        "综艺": ["晚会","生活","访谈","音乐","游戏","旅游","真人秀","美食","益智","搞笑","纪实","汽车"],
        "体育": ["篮球","足球","台球","羽毛球","乒乓球","田径","水上项目","体操","其他"],
        "软件": ["系统","应用","管理","行业","安全防护","多媒体","游戏"],
        "其他": ["其他"],
    }
    _tags_set=set(reduce(lambda x,y:x+y, _all_tag.itervalues()))

    #reverse dict for quick find
    _reversed_main_type = dict((v,k) for k, v in _main_type.iteritems())
    _reversed_sub_type = dict((v,k) for k, v in _sub_type.iteritems())

    @classmethod
    def is_valid_year(cls,year):
        #TODO use aggregate to find all year in DB
        try:
            if int(year)>=1900: return True
            else: return False
        except:
            return False

    @classmethod
    def is_valid_country(cls,country):
        #TODO use aggregate to find all countries in DB
        return len(country.strip())>0

    @classmethod 
    def get_sum_main_type(cls):
        return len(cls._main_type)

    @classmethod
    def is_valid_main_type(cls,index):
        return index in cls._main_type

    @classmethod
    def is_valid_sub_type(cls,index):
        return index in cls._sub_type

    @classmethod
    def get_main_type_by_index(cls,index):
        assert index in cls._main_type
        return cls._main_type[index]

    @classmethod
    def get_main_index_by_type(cls,type):
        assert type in cls._reversed_main_type
        return cls._reversed_main_type[type]

    @classmethod
    def get_sub_type_by_index(cls,index):
        assert index in cls._sub_type
        return cls._sub_type[index]

    @classmethod
    def get_sub_index_by_type(cls,type):
        assert type in cls._reversed_sub_type
        return cls._reversed_sub_type[type]

    @classmethod
    def is_valid_tag(cls,tag):
        return tag in cls._tags_set or tag.encode('utf8') in cls._tags_set

    @classmethod
    def get_types_with_exp_info(cls):
        '''
        types indexed by douban api
        '''
        types_with_exp_info=[0,1,4,6]
        return types_with_exp_info

    @classmethod
    def get_sorted_main_types(cls):
        return sorted(cls._main_type.keys())

    @classmethod
    def get_tags_by_type(cls, type):
        assert type in cls._main_type
        return cls._all_tag[cls._main_type[type]]

    @classmethod
    def is_study_res_type(cls, res_type):
        return res_type == 2

