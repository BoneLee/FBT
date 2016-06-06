# -*- coding: utf-8 -*-
import pymongo

def main():
	conn = pymongo.Connection('localhost',27017)
	print "begin"
	db = conn.fbt
	# db.test.remove()
	# new_msg = { "title" : "ABC",  "comments" : [ { "by" : "joe", "votes" : 3 }, { "by" : "jane", "votes" : 7 } ,{ "by" : "joe", "votes" : 3 }] }
	# db.test.insert(new_msg)
	#result =  db.test.find_one({'user': "1"})
	#print result
	# re = db.test.find_one({'comments.by':'joe'})
	# db.test.update( {'comments.by':'joe'}, {'$unset':{"comments.$":0}}, False, True )
	# db.test.update({},{'$pull':{'comments':None}})
	result = db.users.find_one({'nick_name': u'唯真'})
	print result
	#for item in db.user_msg.find():
	# 	print item

if __name__ == "__main__":
	main()