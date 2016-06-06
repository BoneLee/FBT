import pyinotify
from tornado.ioloop import IOLoop


class EventHandler(pyinotify.ProcessEvent):

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

    def process_IN_MODIFY(self, event):
        print "Modifying:", event.pathname


def handle_read_callback(notifier):
    """
    Just stop receiving IO read events after the first
    iteration (unrealistic example).
    """
    print('handle_read callback')
    # notifier.io_loop.stop()
    # notifier.stop()


wm = pyinotify.WatchManager()
ioloop = IOLoop.instance()
notifier = pyinotify.TornadoAsyncNotifier(wm, ioloop, handle_read_callback,
                                          EventHandler())

wm.add_watch('watch_this', pyinotify.ALL_EVENTS)
ioloop.start()
# ioloop.close()
# notifier.stop()
