# -*- coding: utf-8 -*-
__author__ = 'spark'

from tornado import gen
from tornado.escape import json_encode, json_decode
from tornado.concurrent import return_future
from urllib import urlencode
from tornado.httpclient import HTTPRequest
from tornadoes import ESConnection
from tornado import ioloop
from elasticsearch import Elasticsearch
import logging
from bisect import bisect_right


class ESConnectionWithUpdate(ESConnection):

    def __init__(self, *args, **kwargs):
        super(ESConnectionWithUpdate, self).__init__(*args, **kwargs)

    @return_future
    def update(self, callback, **kwargs):
        doc_type = '{}/{}'.format(kwargs.pop('type'), kwargs.pop('id'))
        kwargs['type'] = doc_type
        path = self.create_path("update", **kwargs)
        source = kwargs.get('source', None)
        if source:
            source = json_encode(source)
            self.post_by_path(path, callback, source)

    @return_future
    def delete_index(self, index, parameters=None, callback=None):
        self.request_index(
                index, "DELETE",
                parameters=parameters, callback=callback)

    @return_future
    def put_index(self, index, contents, parameters=None, callback=None):
        self.request_index(
                index, "PUT", body=json_encode(contents),
                parameters=parameters, callback=callback)

    @return_future
    def get_index(self, index, callback=None):
        self.request_index(
            index, callback=callback)

    def request_index(self, index, method="GET", body=None, parameters=None, callback=None):
        path = '/{index}'.format(**locals())
        url = '%(url)s%(path)s?%(querystring)s' % {
            "url": self.url,
            "path": path,
            "querystring": urlencode(parameters or {})
        }
        request_arguments = dict(self.httprequest_kwargs)
        request_arguments['method'] = method

        if body is not None:
            request_arguments['body'] = body

        request = HTTPRequest(url, **request_arguments)
        self.client.fetch(request, callback)

    @return_future
    def exists_index(self, index, callback=None):
        self.request_index(index, "HEAD", callback=callback)


class ESSearch(object):
    def __init__(self, host="localhost", port=9200,
                 analyze_fields=None,
                 none_analyze_fields=None,
                 index_mapping="",
                 index_name="",
                 type_name="",
                 io_loop=None):
        assert index_mapping and index_name and type_name
        self.index_mapping = index_mapping
        self.index_name = index_name
        self.type_name = type_name
        self.analyze_fields = analyze_fields
        self.none_analyze_fields = none_analyze_fields
        self.all_fields = self.analyze_fields + self.none_analyze_fields
        self._es_connection = ESConnectionWithUpdate(host, port,
            io_loop or ioloop.IOLoop.current())

        es = Elasticsearch("{}:{}".format(host, port))
        if not es.indices.exists(self.index_name):
            es.indices.create(index=self.index_name, body=self.index_mapping)

    def _return_response(self, response):
        response = json_decode(response.body)
        return response

    # just for test
    @gen.coroutine
    def clean_all(self):
        yield self._es_connection.delete_index(self.index_name, parameters={'refresh': True})
        yield self._es_connection.put_index(self.index_name, self.index_mapping, parameters={'refresh': True})

    def check_index(self):
        def cb(result):
            if 200 != result.code:
                # logging.info("index %s not exist, will create new one." % self.index_name)
                self._es_connection.put_index(self.index_name, self.index_mapping, parameters={'refresh': True})
            # else:
            #     logging.info("index %s exist, check OK." % self.index_name)
        # logging.info("begin check index %s" % self.index_name)
        self._es_connection.exists_index(self.index_name, cb)

    @gen.coroutine
    def insert(self, uid, info_dict):
        response = None
        if info_dict:
            insert_dict = dict()
            for k in self.all_fields:
                v = info_dict.get(k, None)
                if v:
                    insert_dict[k] = v
            if insert_dict:
                response = yield self._es_connection.put(self.index_name, self.type_name, uid, insert_dict, parameters={'refresh': True})
        raise gen.Return(response)

    @gen.coroutine
    def get(self, uid):
        response = yield self._es_connection.get(self.index_name, self.type_name, uid)
        raise gen.Return(response)

    @gen.coroutine
    def delete(self, uid):
        response = yield self._es_connection.delete(self.index_name, self.type_name, uid, parameters={'refresh': True})
        raise gen.Return(response)

    @gen.coroutine
    def update_field(self, uid, field_name, val):
        response = None
        if field_name in self.all_fields:
            query = {"doc": {field_name: val}}
            response = yield self._es_connection.update(index=self.index_name,
                                                                  type=self.type_name,
                                                                  id=uid,
                                                                  source=query)
        raise gen.Return(response)

    @gen.coroutine
    def update_multi_fields(self, uid, fields_dict):
        response = None
        if fields_dict:
            update_dict = dict()
            for k in self.all_fields:
                v = fields_dict.get(k, None)
                if v:
                    update_dict[k] = v
            if update_dict:
                query = {"doc": update_dict}
                response = yield self._es_connection.update(index=self.index_name,
                                                            type=self.type_name,
                                                            id=uid,
                                                            source=query)
        raise gen.Return(response)

    @gen.coroutine
    def push(self, uid, field_name, val):
        if not isinstance(val, list) and not isinstance(val, tuple):
            val = [val]
        res = yield self.get(uid)
        res = res['_source']
        org = res.get(field_name, [])
        if not isinstance(org, list):
            org = [org]
        org.extend(val)
        result = yield self.update_field(uid, field_name, org)
        raise gen.Return(result)

    @gen.coroutine
    def add_to_set(self, uid, field_name, val):
        if not isinstance(val, list) and not isinstance(val, tuple):
            val = [val]
        res = yield self.get(uid)
        res = res['_source']
        org = res.get(field_name, [])
        if not isinstance(org, list):
            org = [org]
        org = set(org)
        new = list(org.union(val))
        result = yield self.update_field(uid, field_name, new)
        raise gen.Return(result)

    # TODO: figure out why match     _all can not work 
    @gen.coroutine
    def query(self, query_str, size=200, sort=None):
        #query = {"query": {"match": {"_all": query_str}}}
        query = {
                        "query": {
                            "multi_match":{
                                "type": "best_fields",
                                "query": query_str,
                                "fields": list(self.analyze_fields),
                                "analyzer": "query_ansj"
                            }
                        },
                        "size": size
                    }
        if sort:
            query["sort"] = sort
        response = yield self._es_connection.search(index=self.index_name,
                                                    type=self.type_name,
                                                    source=query)
        #res = self._return_response(response)
        raise gen.Return(response)

    @gen.coroutine
    def search(self, keyword):
        response = yield self.query(keyword)
        if response.code in [200, 201]:
            res = self._return_response(response)
            if "hits" in res["hits"]:
                # scores = [- float(_.get('_score', 0)) for _ in res["hits"]["hits"]]
                # idx = bisect_right(scores, -0.8)
                results = [hit["_source"] for hit in res["hits"]["hits"]]
                # print res["hits"]["hits"]
                raise gen.Return(results)
                # raise gen.Return(results[:idx])
            else:
                raise gen.Return([])
        else:
            logging.info("search error: %d %s" % (response.code, response.body))
            raise gen.Return([])