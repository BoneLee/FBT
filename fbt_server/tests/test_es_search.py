# -*- coding: utf-8 -*-
__author__ = 'spark'

import sys
import os.path
#from uuid import uuid4
from tornado import escape, gen
from tornado.testing import AsyncTestCase, gen_test
from tornadoes import ESConnection

fbt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(fbt_path)

from es_search import ESSearch
from es_mapping import user_index_mapping, user_none_analyze_fields, user_analyze_fields


test_case = [('1', {'tags_list': [u'就业:面试经验', u'校园:浏览器'],
                            'honor': [2010, u'全国', u'Google Android 应用开发中国大学生挑战赛全国优秀奖',
                                           2011, u'全国', u'中科杯全国软件设计大赛优秀作品'],
                            'university': u'中国科学院',
                            'real_name': u'王大锤'
                            }),
                    ('2', { 'university': u'电子科技大学',
                            'real_name': u'小美',
                            'tags_list': [u'校园:浏览器', u'考研:计算机']}),
                    ('3', { 'university': u'电子科技大学',
                            'real_name': u'大锤'})
                    ]


class TestUserSearch(AsyncTestCase):
    def setUp(self):
        super(TestUserSearch, self).setUp()
        self.es_connection = ESConnection("localhost", 9200, self.io_loop)
        self.us = ESSearch(index_mapping=user_index_mapping,
                           index_name="index",
                           type_name="user",
                           analyze_fields=user_analyze_fields,
                           none_analyze_fields=user_none_analyze_fields,
                           io_loop=self.io_loop)
        self.io_loop.run_sync(self.setup_coro)

    @gen.coroutine
    def setup_coro(self):
        yield self.us.clean_all()

    @gen_test
    def test_insert(self):
        uid, info_dict = test_case[0]
        response = yield self.us.insert(uid, info_dict)
        response_dict = self._verify_status_code_and_return_response(response)
        self.assertEqual(response_dict['_index'], 'index')
        self.assertEqual(response_dict['_type'], 'user')
        self.assertEqual(response_dict['_id'], uid)
        self.assertIn('refresh=True', response.request.url)

    @gen_test
    def test_get(self):
        uid, info_dict = test_case[0]
        yield self.us.insert(uid, info_dict)
        res = yield self.us.get(uid)
        self.assertEqual(info_dict, res['_source'])

    @gen_test
    def test_delete(self):
        uid, info_dict = test_case[0]
        res = yield self.us.delete(uid)
        self.assertEqual(res.code, 404)
        response = yield self.us.insert(uid, info_dict)
        res = yield self.us.delete(uid)
        self.assertEqual(res.code, 200)

    @gen_test
    def test_update_field(self):
        uid, info_dict = test_case[0]
        yield self.us.insert(uid, info_dict)
        response = yield self.us.update_field(uid, 'real_name', '小美')
        response_dict = self._verify_status_code_and_return_response(response)
        self.assertEqual(response_dict['_index'], 'index')
        self.assertEqual(response_dict['_type'], 'user')
        self.assertEqual(response_dict['_id'], uid)
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(response['real_name'], u"小美")

    @gen_test
    def test_update_multi_fields(self):
        uid, info_dict = test_case[0]
        yield self.us.insert(uid, info_dict)
        response = yield self.us.update_multi_fields(uid, {'real_name': '小美', 'tags_list': ['a', 'b']})
        response_dict = self._verify_status_code_and_return_response(response)
        self.assertEqual(response_dict['_index'], 'index')
        self.assertEqual(response_dict['_type'], 'user')
        self.assertEqual(response_dict['_id'], uid)
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(response['real_name'], u"小美")
        self.assertEqual(response['tags_list'], ['a', 'b'])

    @gen_test
    def test_push(self):
        uid, info_dict = test_case[0]
        tags_list = info_dict['tags_list']
        yield self.us.insert(uid, info_dict)
        yield self.us.push(uid, "tags_list", 'a')
        tags_list.append('a')
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(response['tags_list'], tags_list)

        yield self.us.push(uid, "tags_list", ['a', 'b'])
        tags_list.extend(['a', 'b'])
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(response['tags_list'], tags_list)

    @gen_test
    def test_add_to_set(self):
        uid, info_dict = test_case[0]
        tags_list = info_dict['tags_list']
        yield self.us.insert(uid, info_dict)
        yield self.us.add_to_set(uid, "tags_list", 'a')
        tags_list.append('a')
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(sorted(response['tags_list']), sorted(tags_list))

        yield self.us.add_to_set(uid, "tags_list", ['a', 'b'])
        tags_list = set(tags_list).union(['a', 'b'])
        tags_list = list(tags_list)
        response = yield self.es_connection.get(index="index", type="user", uid=uid)
        response = response["_source"]
        self.assertEqual(sorted(response['tags_list']), sorted(tags_list))

    @gen_test
    def test_query(self):
        for uid, info_dict in test_case[:2]:
            yield self.us.insert(uid, info_dict)
        response = yield self.us.query(u"校园")
        response = self._verify_status_code_and_return_response(response)
        self.assertEqual(response["hits"]["total"], 2)

        response = yield self.us.query(u"软件大赛")
        response = self._verify_status_code_and_return_response(response)
        self.assertEqual(response["hits"]["total"], 1)
        self.assertEqual(response["hits"]["hits"][0]["_id"], '1')

        response = yield self.us.query(u'电子科技大学')
        response = self._verify_status_code_and_return_response(response)
        self.assertEqual(response["hits"]["total"], 2)
        self.assertEqual(response["hits"]["hits"][0]["_id"], '2')

    def _verify_status_code_and_return_response(self, response):
        self.assertTrue(response.code in [200, 201], "Wrong response code: %d." % response.code)
        response = escape.json_decode(response.body)
        return response

if __name__ == '__main__':
    import unittest
    unittest.main()
