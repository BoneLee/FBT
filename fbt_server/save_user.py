if __name__ == "__main__":	
	import json
	import cPickle as pickle
	f = open("user.json")
	lines = f.readlines()
	users = {}
	for item in lines:
		item = item.split("==")
		users[long(item[0].strip())] = item[1].strip()
	f.close()
	for port in ["8001","8002","8003","8005"]:
		f = open("users"+str(port)+".pkl", "w")
		f.write(pickle.dumps(users))
		f.close()
	f = open("server_info.json")
	lines = f.readlines()
	server_info = {}
	for item in lines:
		item = item.split("==")
		#print item[1]
		index_0 = item[1].find(":")
		index_2 = item[1].find(":", index_0+1)
		index_1 = item[1].find(",")
		#print item[1][index_2+2:]
		if item[1][index_0+2:index_1].strip() == "None":
			item[1] = "'"+item[1][0:index_0].strip()+"':'None','"+item[1][index_1+2:index_2]+"':"+item[1][index_2+6:len(item[1])-1]
		elif item[1][index_2+2:].strip() == "None":
			#print "come in"
			item[1] = "'"+item[1][0:index_0].strip()+"':'"+item[1][index_0+2:index_1]+"','"+item[1][index_1+2:index_2]+"':'None'"
		else:
			item[1] = "'"+item[1][0:index_0].strip()+"':'"+item[1][index_0+2:index_1]+"','"+item[1][index_1+2:index_2]+"':"+item[1][index_2+6:len(item[1])-1]
		item[1] = item[1].replace("u'", "\"")
		item[1] = item[1].replace("'", "\"")
		item[1] = item[1].replace(" ", "") 
		item[1] = item[1].replace("\n", "")
		item[1] = item[1].replace(")", "")
		#print "{"+item[1]+"}"
		item[1] = json.loads("{"+item[1]+"}")
		if item[1]["ipv4"] == "None":
			item[1]["ipv4"] = None
		if item[1]["ipv6"] == "None":
			item[1]["ipv6"] = None
		if item[1]["ipv6"]:
			item[1]["ipv6"] = set(item[1]["ipv6"])
			#print (isinstance(item[1]["ipv6"], set))
		server_info[long(item[0].strip())] = item[1]
	f.close()
	for port in ["8001","8002","8003","8005"]:
		f = open("http_server_info_"+str(port)+".pkl", "w")
		f.write(pickle.dumps(server_info))
		f.close()
	# f = open("8001server_info.json")
	# print pickle.load(f)
	# f.close()