import CmdServer
import MqttProcessor
import CommunicationProcessor
import MyPriorityQueue
from queue import Queue
import NotificationForwarder
import Config
import ScanRateConsideringQueueFeeder
import datetime
import RegisterDatapoint
import pickle
import logging
import Pins
import Heartbeat


if __name__ == "__main__":
    config = Config.Config()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(config.logFile)
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    Pins.pinsInit()

    queue = MyPriorityQueue.MyPriorityQueue()
    pubQueue = Queue()
    nf = NotificationForwarder.NotificationForwarder()
    logger.debug('infrastructure prepared')

    datapoints = RegisterDatapoint.loadRegisterList(config.registerFile)
    logger.debug('datapoints read')

    cp = CommunicationProcessor.CommunicationProcessor(config, queue, pubQueue)
    cp.start()
    logger.debug('CommunicationProcessor started')

    mp = MqttProcessor.MqttProcessor(config, datapoints, queue, pubQueue)
    nf.register(mp)
    mp.start()
    logger.debug('MqttProcessor started')

    cs = CmdServer.CmdServer(config, nf, datapoints)
    cs.start()
    logger.debug('CmdServer started')

    hb = Heartbeat.Heartbeat(config, pubQueue)
    hb.start()
    logger.debug('Heartbeat started')

    qf = ScanRateConsideringQueueFeeder.ScanRateConsideringQueueFeeder(config, datapoints, queue)
    nf.register(qf)
    qf.start()
    logger.debug('ScanRateConsideringQueueFeeder started')
