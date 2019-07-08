import threading
import datetime

class CommunicationProcessor(threading.Thread):
    def __init__(self, config, queue):
        super().__init__()
        self.config = config
        self.queue = queue

    def run(self):
        while True:
            r = self.queue.get()
            # r.process()
            r.lastContact = datetime.datetime.now()
            print("Dequeued: {0!s}".format(r))
            r.enqueued = False
