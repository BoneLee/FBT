# -*- coding: utf-8 -*-
__author__ = 'spark'


ZH_CN_STRING = {"type": "string",
                "term_vector": "yes",
                "analyzer": "index_ansj",
                "search_analyzer": "query_ansj"}

SETTING = {"refresh_interval": "5s",
           "number_of_shards": 2,
           "number_of_replicas": 1}

user_none_analyze_fields = ("user", "uid",  "icon", "tags", "thumb_num",
                                               "followers_num", "state", "state_desc",
                                               "desc", "gender", "answers_num", "nick_name")
user_analyze_fields = ('tags_list', 'honor', 'university', "university_short_name", 'college', 'real_name')
user_index_mapping = {
    "settings": SETTING,
    "mappings": {
        "_default_": {
            "_all": {"enabled": False}
        },
        "user": {
            "properties": {
                "tags_list": ZH_CN_STRING,
                "honor": ZH_CN_STRING,
                "university": ZH_CN_STRING,
                "university_short_name": ZH_CN_STRING,
                "college": ZH_CN_STRING,
                "real_name": ZH_CN_STRING,
                "thumb_num": {
                    "type": "integer",
                    "index": "not_analyzed"
                }
            }
        }
    }
}


question_analyze_fields = ('title', 'content', 'class2', "publisher_real_name", 'tags')
question_none_analyze_fields = ("university", "college", "publisher","answer_users", "publisher_img",
                                "user_description","publisher_nick", "publisher_real_name","publisher_star_info",
                                "publisher_uid", "reply_num", "comment_num", "comment_list", "best_answer",
                                "thumb_up_num", "tags_with_class", "thumb_up_users", "thanked_users",
                                "thanks_coin", "index_ctime", "ctime", "id", "views", "collected_num")

question_index_mapping = {
    "settings": SETTING,
    "mappings": {
        "_default_": {
            "_all": {"enabled": False}
        },
        "question": {
            "properties": {
                "tags": ZH_CN_STRING,
                "publisher_real_name": ZH_CN_STRING,
                "class2": ZH_CN_STRING,
                "content": ZH_CN_STRING,
                "title": ZH_CN_STRING,
            }
        }
    }
}

course_analyze_fields = ('university', 'college', 'course', "university_short_names", 'teacher')
course_none_analyze_fields = ("ctime", "real_uploader", "course_id", "resource_num")

course_index_mapping = {
    "settings": SETTING,
    "mappings": {
        "_default_": {
            "_all": {"enabled": False}
        },
        "course": {
            "properties": {
                "university": ZH_CN_STRING,
                "college": ZH_CN_STRING,
                "course": ZH_CN_STRING,
                "university_short_names": ZH_CN_STRING,
                "teacher": ZH_CN_STRING,
            }
        }
    }
}


resource_analyze_fields = ('university', 'college', 'course', "university_short_names", 'teacher', "filename", "resource_name")
resource_none_analyze_fields = ("file_size", "resource_name", "university", "college", "img", "uid", "real_uploader",
                                "file_key", "filename", "preview_key", "download_link", "file_id")

resource_index_mapping = {
    "settings": SETTING,
    "mappings": {
        "_default_": {
            "_all": {"enabled": False}
        },
        "resource": {
            "properties": {
                "university": ZH_CN_STRING,
                "college": ZH_CN_STRING,
                "course": ZH_CN_STRING,
                "university_short_names": ZH_CN_STRING,
                "teacher": ZH_CN_STRING,
                "filename": ZH_CN_STRING,
                "resource_name": ZH_CN_STRING,
            }
        }
    }
}
