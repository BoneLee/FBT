from resource_hot_update import HotUpdate
from copy import deepcopy

def update():
	update = HotUpdate()
	update.run(update.get_hottest_resource)
	#update.run(update.test)
	#HotUpdate.set_hottest_resource(update.hotRankLists)
	#HotUpdate.hotRankLists = deepcopy(update.hotRankLists)

if __name__ == "__main__":
	update()
	#print HotUpdate.hotRankLists[1][1]
	#test = HotUpdate()
	#print test.__class__.hotRankLists[1][1]
	
	
	  
