import threading
import datetime
from NotificationForwarder import AbstractNotificationReceiver
import logging

class ScanRateConsideringQueueFeeder(threading.Thread, AbstractNotificationReceiver):
    def __init__(self, config, registers, queue):
        super().__init__()
        self.config = config
        self.registers = registers
        self.queue = queue
        self.delayEvent = threading.Event()
        # self.daemon = True
        self.logger = logging.getLogger('ScanRateConsideringQueueFeeder')

    def getMinimalScanrate(self):
            return min([r.scanRate.total_seconds() for r in self.registers if r.scanRate])

    def receiveNotification(self, arg):
        self.logger.info("ScanRateConsideringQueueFeeder:registersChanged")
        self.delay = self.getMinimalScanrate()

    def run(self):
        self.delay = self.getMinimalScanrate()
        while True:
            registersToBeHandled = [
                r for r in self.registers if ((not r.enqueued) and
                                              (r.scanRate) and
                                              ((not r.lastContact) or 
                                               (r.lastContact + r.scanRate < datetime.datetime.now())))
            ]
            registersToBeHandled.sort(key=lambda x : x.scanRate)
            for r in registersToBeHandled:
                self.queue.put(r)
                r.enqueued = True
            self.delayEvent.wait(self.delay)
