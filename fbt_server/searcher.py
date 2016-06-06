# coding: utf-8
__author__ = 'bone'
# Thanks to https://github.com/tj/reds

import jieba
import redis


class RedisFullTextSearcher(object):
    def __init__(self, key, redis_db=None):
        self.key = key
        if redis_db:
            self.db = redis_db
        else:
            self.db = redis.StrictRedis()
        self.unwanted = {".", ",", " ", "。", "，", ":", "、", "？", "?"}  # TODO add more

    def stem(self, words):
        return [word for word in words if word not in self.unwanted]

    def get_weights(self, words):
        ret = {}
        for word in words:
            ret[word] = len(word) # maybe for English words it should be frequency
        return ret

    def index(self, text, id):
        text = text.lower()
        words = self.stem(jieba.cut_for_search(text))  # 搜索引擎模式
        words2 = self.stem(jieba.cut(text, cut_all=True))  # 精确模式
        for word in words2:
            if word not in words:
                words.append(word)
        # words = self.stem(jieba.cut(text, cut_all=True))
        # print " index, ".join(words)
        if not words:
            return
        words_weight = self.get_weights(words)
        # print "weight:" + str(words_weight)

        pipe = self.db.pipeline()
        for word, weight in words_weight.iteritems():
            # print "word, weight: %s %d" % (word,weight)
            pipe.zadd(self.key + ':word:' + word, weight, id)
            pipe.zadd(self.key + ':object:' + str(id), weight, word)
        pipe.execute()

    def remove(self, id):
        delete_keys = self.db.zrevrangebyscore(self.key + ":object:" + str(id), "+inf", 0)
        pipe = self.db.pipeline()
        for k in delete_keys:
            pipe.zrem(self.key + ":word:" + k, id)
        pipe.execute()

    def search(self, text):
        text = text.lower()
        words = self.stem(jieba.cut(text, cut_all=False))  # 精确模式
        if not words:
            return []
        # print " search, ".join(words)
        tmp_key = self.key + "tmpkey"

        pipe = self.db.pipeline()
        pipe.zinterstore(tmp_key, [self.key + ":word:"+word for word in words if word])
        pipe.zrevrange(tmp_key, 0, -1)
        pipe.zremrangebyrank(tmp_key, 0, -1)
        out = pipe.execute()
        # print "out:" + str(out)
        found_ids = out[1]
        return found_ids


if __name__ == "__main__":
    r = RedisFullTextSearcher("test")
    text_array = []
    text_array.append('Tobi wants four dollars')
    text_array.append('Tobi only wants $4')
    text_array.append('Loki is really fat')
    text_array.append('Loki, Jane, and Tobi are ferrets')
    text_array.append('Manny is a cat')
    text_array.append('Luna is a cat')
    text_array.append('Mustachio is a cat')
    text_array.append("Tom    is also a cat. Isn't  True?")
    text_array.append("小明硕士毕业于北京,中国科学院计算所chinese academy of science")
    text_array.append("good test just have a look, E.T.，xixi。")
    text_array.append("也许只有失去以后才会珍惜；你觉得呢；；；；～～～！@！#@￥@#￥#@……%……＆%＊%￥")
    text_array.append("北京是一个好地方，那里有清华，还有好多大学")
    text_array.append("清华，是什么大学？")
    text_array.append("我来到北京清华大学")
    text_array.append("不知道清华，是什么大学，大学，大学？")
    text_array.append(u"安徽大学的一个课程资源，希望可以搜索简称？")
    text_array.append(u"李智华老师的一个课程资源，希望可以搜索简称？")
    text_array.append(u"中国人民大学，希望可以搜索到这个东西？")
    for i in range(0,len(text_array)):
        r.remove(i)

    for i, s in enumerate(text_array):
        r.index(s, i)

    for keyword in ["cat a", "Jane", "北京", "清华大学","才会珍惜","也许只有失去以后才会珍惜","我来到北京清华大学","搜不到才对","李智华", "中国人民大学", "人民大学", "tom"]:
        result = r.search(keyword)
        print "found search for cat:"+str(keyword)
        for i in result:
            print text_array[int(i)]
        print "*******************************"

    print "search 安大:"
    result = r.search("安大")
    for i in result:
        print text_array[int(i)]
    # print " ".join(jieba.cut("安徽大学的一个课程资源，希望可以搜索简称安大,还有国科大这样的？", cut_all=False))
    # print " ".join(jieba.cut_for_search("安徽大学的一个课程资源，希望可以搜索简称安大,还有国科大这样的？"))

    r.index("测下重复建立同一个索引会如何？", 100)
    r.index("测下重复建立同一个索引会如何？", 100)
    r.index("测下重复建立同一个索引会如何？", 100)
    r.index("测下重复建立同一个索引会如何？", 100)
    r.index("测下重复建立同一个索引会如何？", 100)
    print "search 索引:"
    result = r.search("索引")
    print result

    # space is key point
    r.index("李智华 中科大", 0)
    '''
    李智华 index, 中科 index, 科大 index, 中科大
    '''
    r.index("李智华中科大", 0)
    '''
    李智 index, 华中 index, 中科 index, 科大 index, 华中科 index, 中科大 index, 华中科大
    '''
