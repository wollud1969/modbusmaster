import threading
import MqttProcessor
import logging
import time


class Heartbeat(threading.Thread):
    def __init__(self, config, pubQueue):
        super().__init__()
        self.config = config
        self.pubQueue = pubQueue
        # self.daemon = True
        self.logger = logging.getLogger('Heartbeat')

    def run(self):
        cnt = 0
        while True:
            cnt += 1
            pubItem = MqttProcessor.PublishItem(self.config.heartbeatTopic, str(cnt))
            self.pubQueue.put(pubItem)
            time.sleep(self.config.heartbeatPeriod)
