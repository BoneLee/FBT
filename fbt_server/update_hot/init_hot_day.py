from resource_hot_update import HotUpdate

def init_update():
	update = HotUpdate()
	update.run(update.init_hot_day)

if __name__ == "__main__":
	init_update()
