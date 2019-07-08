import CmdServer
import MqttProcessor
import CommunicationProcessor
import MyPriorityQueue
import NotificationForwarder
import Config
import ScanRateConsideringQueueFeeder
import datetime
import RegisterDatapoint
import pickle



if __name__ == "__main__":
    queue = MyPriorityQueue.MyPriorityQueue()
    nf = NotificationForwarder.NotificationForwarder()
    config = Config.Config()

    datapoints = None
    with open(config.registerFile, 'rb') as f:
        datapoints = pickle.load(f)
    RegisterDatapoint.checkRegisterList(datapoints)

    cp = CommunicationProcessor.CommunicationProcessor(config, queue)
    cp.start()

    mp = MqttProcessor.MqttProcessor(config, datapoints, queue)
    nf.register(mp)
    mp.start()

    qf = ScanRateConsideringQueueFeeder.ScanRateConsideringQueueFeeder(config, datapoints, queue)
    nf.register(qf)
    qf.start()

    cs = CmdServer.CmdServer(config, nf, datapoints)
    cs.start()