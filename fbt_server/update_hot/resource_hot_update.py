#-*- coding: utf-8 -*- 
from tornado.ioloop import IOLoop
from tornado import gen
from datetime import date 
import cPickle as pickle
from random import randint
import os
import pprint
import logging
from copy import deepcopy
import motorclient

class HotUpdate(object):
	
	'''
	hot of resources in all_resources DB is like
		hot[{hot_day:hot, download_num_day:download of last period}]
	'''
	hotRankLists = [[] for i in range(10)]
	def __init__(self):
		self._main_type = {0: "电影", 1: "剧集", 2:"学习",3: "音乐", 4: "动漫", 5: "游戏", 6: "综艺", 7: "体育", 8:"软件", 9:"其他"}
		self._main_type_sum = len(self._main_type) #the amount of main types
		self._db = motorclient.fbt
		self._coll = self._db.all_resources
		self._DESCENDING  = -1
		self._hot_day_coefficent = 0.5
		self._max_records = 200
		self._dump_max_records = 20
		self.hotRankLists = [[] for i in range(10)]

	@gen.coroutine	
	def init_hot_day(self):
		yield self._coll.update({}, {"$set": {"hot":[{"hot_day": 0, "download_num_day": 0}]}}, multi=True)
		cursor = self._coll.find({"public": 1, "hidden": {"$ne": 1}})
		try:
			while (yield cursor.fetch_next):
				res = cursor.next_object()
				if "download_num" in res:
					if res["download_num"] != '':
						res["hot"][0]["hot_day"] = int(res["download_num"])
				self._coll.save(res)
		except Exception, e:
			logging.warning(e)
			print res
	
	@gen.coroutine
	def update_hot_day(self):
		cursor = self._coll.find({"public": 1, "hidden": {"$ne": 1}})
		try:
			while (yield cursor.fetch_next):
				res = cursor.next_object()
				if "hot" not in res:
					res["hot"] = [{"hot_day": 0, "download_num_day": 0}]
				else:
					if res["hot"][0]["hot_day"] == '':
						res["hot"][0]["hot_day"] = 0
					res["hot"][0]["hot_day"] = int(self._hot_day_coefficent * res["hot"][0]["hot_day"]) + res["hot"][0]["download_num_day"]
					res["hot"][0]["download_num_day"] = 0
				self._coll.save(res)
		except Exception, e:
			today = date.today().strftime("%Y-%m-%d")
			print today
			logging.warning(e)
			print res
	
	@gen.coroutine
	def test(self):
		try:
			one_res = yield self._coll.find_one({"public": 1, "hot.0.hot_day": {"$gt": 10},"hidden": {"$ne": 1}})
			#one_res = HotUpdate.hotRankLists[9][200]
			print one_res
		except Exception, e:
			logging.warning(e)

	@gen.coroutine
	def get_hottest_resource(self):
		try:
			hot_db = motorclient.fbt.hot_resources
			hot_db.remove({})	
			for res_type in range(self._main_type_sum):
				#self.hotRankLists[res_type] = []
				cursor = self._coll.find({"hidden": {"$ne": 1}, "public": 1, "main_type": res_type}).sort([('hot.0.hot_day', self._DESCENDING), ('download_num', self._DESCENDING)]).limit(self._max_records)
				while (yield cursor.fetch_next):
					res = cursor.next_object()
					#one_resource = self.extract_resource_from_db(res)
					#self.hotRankLists[res_type].append(res)
					hot_db.save(res)
			for res_type in range(self._main_type_sum):
				cursor = hot_db.find({"main_type": res_type}).sort([('hot.0.hot_day', self._DESCENDING)])
		except Exception, e:
			logging.warning(e)
		
	
	def backup_hot_resource(self):
		#make the dirs for backup files
		assert self._dump_max_records <= self._max_records
		path = "dump_hot_resource"
		if not os.path.exists(path):
			os.makedirs(path)
		for res_type in range(self._main_type_sum):
			new_path = os.path.join(path, self._main_type[res_type])
			if not os.path.exists(new_path):
				os.makedirs(new_path)

		for res_type in range(self._main_type_sum):
			today = date.today().strftime("%Y-%m-%d")
			file_name = os.path.join(path, self._main_type[res_type], today+ ".pkl")
			with open(file_name, "wb") as infile:
				pickle.dump(HotUpdate.hotRankLists[res_type][0:self._dump_max_records], infile)
			infile.close()

	def get_hot_resource_from_backup(self):
		path = "dump_hot_resource"			
		for res_type in range(self._main_type_sum):
			today = date.today().strftime("%Y-%m-%d")
			file_name = os.path.join(path, self._main_type[res_type], today+ ".pkl")
			with open(file_name, "rb") as outfile:
				pickle.load(outfile)
			outfile.close()
	
	def extract_resource_from_db(self, res):
		one_resource = dict()
		one_resource['file_hash'] = res['file_hash']
		one_resource['file_name'] = res['file_name']
		one_resource['main_type'] = res['main_type']
		one_resource['sub_type'] = res['sub_type']
		one_resource['file_size'] = res['file_size']
		one_resource['mtime'] = res['mtime']
		one_resource['tags'] = " ".join(tag for tag in res['tags'])
		one_resource['grades'] = dict()
		map(lambda score1: operator.setitem(one_resource['grades'], score1['uid'], score1["score"]), res['scores'])
		total_score = reduce(lambda score1, score2: {"score": score1['score'] + score2['score'], "uid": 0}, res['scores'])["score"]
		one_resource['avg_grade'] = (total_score + 0.0) / len(res['scores'])
		one_resource['comments'] = res['comments']  
		if "download_num" not in res:
			res["download_num"] = 0
		one_resource['download_num'] = res['download_num']
		if need_private_owner:
			owners = [owner['uid'] for owner in res['owners']]  # yield self.get_resource_owners(k)
		else:
			owners = [owner['uid'] for owner in res['owners'] if owner['is_public']]  # yield self.get_resource_owners(k)
		one_resource['owners'] = owners
		one_resource['total_owners_num'] = len(owners)
		return one_resource

	@gen.coroutine
	def run(self, func):
		IOLoop.current().run_sync(func)

	

	


	
