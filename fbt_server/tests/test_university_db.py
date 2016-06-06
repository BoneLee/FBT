# coding: utf-8
__author__ = 'bone'

import sys
import os.path

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(fbt_path)

from university_db import UniversityDB
import tornado.testing

class UniversityDBTestCase(tornado.testing.AsyncTestCase):
    @tornado.testing.gen_test(timeout=1)
    def test_get_university_id(self):
        u = UniversityDB()
        self.assertEqual(u.get_university_id("北京大学"), 1002)
        self.assertEqual(u.get_university_id("星环大学"), 34042)
        self.assertEqual(u.get_college_id("北京大学","软件与微电子学院"), 160)
        self.assertEqual(u.get_college_id("星环大学","考研学院"), 30145)
        self.assertEqual(u.get_college_id("中南林业科技大学","林学院"), 30155)
        self.assertEqual(u.get_college_id("清华大学","考研学院"), 30156)
        self.assertEqual(u.get_college_id("北京大学","考研学院"), 30157)
        self.assertEqual(u.get_college_id("哈尔滨工程大学","考研学院"), 30269)
        self.assertListEqual(u.get_short_name("北京大学"), [u"北大"])
        self.assertListEqual(u.get_short_name("中国科学院"), [u"中科院"])

    @tornado.testing.gen_test(timeout=1)
    def test_university_short_name(self):
        u = UniversityDB()
        self.assertListEqual(u.get_complete_name("北林"),["北京林业大学"])
        self.assertListEqual(u.get_complete_name("北广"),["中国传媒大学"])
        self.assertListEqual(u.get_complete_name("中传"),["中国传媒大学"])
        self.assertListEqual(u.get_complete_name("广院"),["中国传媒大学"])
        self.assertListEqual(u.get_complete_name("地大"),["中国地质大学（武汉）","中国地质大学（北京）"])
        self.assertListEqual(u.get_complete_name("不存在"), [])

    @tornado.testing.gen_test(timeout=1)
    def test_is_valid_college(self):
        u = UniversityDB()
        self.assertTrue(u.is_valid_university_and_college("北京大学", "物理学院"))
        self.assertTrue(u.is_valid_university_and_college("北京科技大学", "马克思主义学院"))

    @tornado.testing.gen_test(timeout=1)
    def test_has_university_keyword(self):
        u = UniversityDB()
        self.assertTrue(u.is_continuous_substr("北林","北京林业大学"))
        self.assertTrue(u.is_continuous_substr("中传","中国传媒大学"))
        self.assertTrue(u.is_continuous_substr("地大","中国地质大学（武汉）"))
        self.assertTrue(u.is_continuous_substr("地大", "中国地质大学（北京）"))
        self.assertTrue(u.is_continuous_substr("中地大", "中国地质大学（北京）"))
        self.assertTrue(u.university_has_keyword("北林","北京林业大学"))
        self.assertTrue(u.university_has_keyword("zky", "中国科学院大学"))
        self.assertTrue(u.university_has_keyword("中科院", "中国科学院大学"))
        self.assertTrue(u.university_has_keyword("国科大", "中国科学院大学"))
        self.assertFalse(u.university_has_keyword("zky2", "中国科学院大学"))



if __name__ == '__main__':
    import unittest
    unittest.main()
