# coding: utf8
__author__ = 'bone'

import os
import jieba
import jieba.posseg
from tornado.escape import utf8


class StopWordsManager(object):
    def __init__(self):
        self._stop_words = set()
        self._read_into_dict("data/dict/en_stop_words.txt")
        self._read_into_dict("data/dict/zh_stop_words.txt")

    def _read_into_dict(self, path):
        cur_dir = os.path.dirname(__file__)
        en_file = os.path.join(cur_dir,  path)
        with open(en_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and line[:3] != "---":
                    self._stop_words.add(utf8(line))

    def is_stop_word(self, word):
        return utf8(word) in self._stop_words

    def stem(self, words):
        ret = []
        for word in words:
            strip_word = word.strip()

            if len(strip_word) > 1:
                word = utf8(strip_word)
                if not self.is_stop_word(word) and word not in ret:
                    ret.append(word)
        return ret

    def extract_words(self, text):
        ret = []
        for seg in jieba.posseg.cut(text):
            word = seg.word
            flag = seg.flag
            strip_word = word.strip()
            # print word, flag
            if len(strip_word) > 1 and (flag in ("v", "vn", "i", "j", "n", "nt", "nh", "ni", "nl", "ns", "nz")):
                word = utf8(strip_word)
                if not self.is_stop_word(word) and word not in ret:
                    # print word, flag
                    ret.append(word)
        return ret

if __name__ == "__main__":
    stop_words_man = StopWordsManager()
    assert stop_words_man.is_stop_word(",")
    assert stop_words_man.is_stop_word(".")
    assert stop_words_man.is_stop_word("#")
    assert stop_words_man.is_stop_word("you")
    assert stop_words_man.is_stop_word("year")
    assert stop_words_man.is_stop_word("一时")
    assert stop_words_man.is_stop_word(u"一时")
    assert stop_words_man.is_stop_word(u"year")
    for w in stop_words_man.extract_words(" 历史上为什么没有关于秦始皇皇后的记载？历史上为什么没有关于秦始皇皇后的记载？难道他是筒子？"):
        print w
    print "-----------------------"
    for w in stop_words_man.extract_words(""" 如何解决"早起毁一天"？
为了GPA、证书考试以及竞赛折腾终日，感觉时间非常不够用。
有一段时间（大概一个月）里，我早上六点钟起床洗漱，七点半叫醒舍友起床出门，八点钟上课。晚上自习到十点钟回宿舍，十一点半睡觉。
满以为这是一种能保证睡眠质量但是也可以高效利用时间的安排，但是一个月后发现身体完全跟不上了，常常七点半以后失去意志，上课硬撑着（高数），或者上课（思修）倒头就睡。
感觉每天都是“特困生”，这个问题大家有遇到过吗，你们是如何解决的呢？
"""):
        print w

    print "pass test"
