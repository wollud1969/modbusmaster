import CmdServer
import MqttProcessor
import CommunicationProcessor
import MyPriorityQueue
import NotificationForwarder
import Config
import ScanRateConsideringQueueFeeder
import datetime
import HoldingRegisterDatapoint

datapoints = [
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Frequency', 1, 0x2020, 2, datetime.timedelta(seconds=10), 'Pub/Frequency', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Current', 1, 0x2060, 2, datetime.timedelta(seconds=10), 'Pub/Current', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Resistance Channel 1', 2, 0x0004, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel1', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Temperature Channel 1', 2, 0x000c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel1', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Resistance Channel 2', 2, 0x0014, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel2', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Temperature Channel 2', 2, 0x001c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel2', None, None),
    HoldingRegisterDatapoint.HoldingRegisterDatapoint('Relay1', 5, 0x0001, 1, None, None, 'Sub/Relay1', 'Feedback/Relay1')
]

queue = MyPriorityQueue.MyPriorityQueue()
nf = NotificationForwarder.NotificationForwarder()
config = Config.Config()

if __name__ == "__main__":
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