from resource_hot_update import HotUpdate

def update():
	update = HotUpdate()
	update.run(update.update_hot_day)
	#update.run(update.test)
	#update.run(update.get_hottest_resource)
	#update.backup_hot_resource()
	#update.get_hot_resource_from_backup()

if __name__ == "__main__":
	update()  
