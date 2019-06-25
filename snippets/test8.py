import queue
import datetime
import threading
import socketserver
import cmd
import io
import paho.mqtt.client as mqtt


class Config(object):
    def __init__(self):
        self.mqttBrokerHost = '127.0.0.1'
        self.mqttBrokerPort = 1883
        self.mqttLogin = ''
        self.mqttPassword = ''



class AbstractNotificationReceiver(object):
    def receiveNotification(self, arg):
        raise NotImplementedError

class NotificationForwarder(object):
    def __init__(self):
        self.receivers = []

    def register(self, receiver):
        self.receivers.append(receiver)

    def notify(self, arg=None):
        for r in self.receivers:
            r.receiveNotification(arg)


class AbstractModbusDatapoint(object):
    def __init__(self, label, unit, address, count, scanRate):
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.scanRate = scanRate
        self.type = 'abstract data point'
        self.command = None
        self.value = None
        self.enqueued = False
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __lt__(self, other): return self.priority < other.priority
    def __le__(self, other): return self.priority <= other.priority
    def __eq__(self, other): return self.priority == other.priority
    def __ne__(self, other): return self.priority != other.priority
    def __gt__(self, other): return self.priority > other.priority
    def __ge__(self, other): return self.priority >= other.priority

    def __str__(self):
        return "{0}, {1}: {2} {3} {4} {5} {6}".format(self.type, self.label, self.unit, self.address, self.count, self.command, self.value)
    
    def setCommand(self, cmd):
        self.command = cmd
    
    def setValue(self, value):
        self.value = value


class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super(HoldingRegisterDatapoint, self).__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.lastContact = None
        self.type = 'read holding register'

    def process(self):
        successFull = False
        giveUp = False
        if self.writeRequestValue:
            # perform write operation
            if successFull:
                # give feedback
                self.writeRequestValue = None
            else:
                # retries handling
                if giveUp:
                    # give negative feedback
                    self.writeRequestValue = None
        else:
            # perform read operation
            if successFull:
                self.lastContact = datetime.datetime.now()
                # publish value
            else:
                # retries handling
                if giveUp:
                    # backoff and availability handling
                    # give negative feedback
                    pass
    
    def onMessage(self, value):
        self.writeRequestValue = value


def mqttOnConnectCallback(client, userdata, flags, rc):
    userdata.onConnect()

def mqttOnMessageCallback(client, userdata, message):
    userdata.onMessage(message.topic, message.payload)

def mqttOnDisconnectCallback(client, userdata, rc):
    userdata.onDisconnect(rc)

class MqttProcessor(threading.Thread, AbstractNotificationReceiver):
    def __init__(self, registers, queue):
        super(MqttProcessor, self).__init__()
        self.registers = registers
        self.queue = queue
        self.client = mqtt.Client(userdata=self)
        self.subscriptions = []
        self.topicRegisterMap ={}

    def __processUpdatedRegisters(self, force=False):
        # print("MqttProcessor.__updateSubscriptions")

        subscribeTopics = [ r.subscribeTopic for r in self.registers if r.subscribeTopic]
        # print("Topics: {0!s}".format(subscribeTopics))

        for subscribeTopic in subscribeTopics:
            if (subscribeTopic not in self.subscriptions) or force:
                print("Subscribe to {0}".format(subscribeTopic))
                self.client.subscribe(subscribeTopic)
                self.subscriptions.append(subscribeTopic)

        for subscription in self.subscriptions:
            if (subscription not in subscribeTopics) and not force:
                print("Unsubscribe from {0}".format(subscription))
                self.client.unsubscribe(subscription)
                self.subscriptions.remove(subscription)

        self.topicRegisterMap = { r.subscribeTopic: r for r in self.registers if r.subscribeTopic }

    def receiveNotification(self, arg):
        print("MqttProcessor:registersChanged")
        self.__processUpdatedRegisters()

    def run(self):
        # print("MqttProcessor.run")
        self.client.on_message = mqttOnMessageCallback
        self.client.on_connect = mqttOnConnectCallback
        self.client.on_disconnect = mqttOnDisconnectCallback
        if config.mqttLogin and config.mqttPassword:
            self.client.username_pw_set(config.mqttLogin, config.mqttPassword)
        self.client.connect(config.mqttBrokerHost, config.mqttBrokerPort)
        self.client.loop_forever()

    def onConnect(self):
        # print("MqttProcessor.onConnect")
        self.__processUpdatedRegisters(force=True)

    def onDisconnect(self, rc):
        print("Disconnected from MQTT broker: {0}".format(rc))

    def onMessage(self, topic, payload):
        # print("MqttProcessor.onMessage")
        r = self.topicRegisterMap[topic]
        # print("{0}: {1!s} -> {2!s}".format(topic, payload, r))
        r.setCommand('w')
        r.setValue(payload)
        self.queue.put(r)


class ScanRateConsideringQueueFeeder(threading.Thread, AbstractNotificationReceiver):
    def __init__(self, registers, queue):
        super(ScanRateConsideringQueueFeeder, self).__init__()
        self.registers = registers
        self.queue = queue
        self.delayEvent = threading.Event()

    def getMinimalScanrate(self):
            return min([r.scanRate.total_seconds() for r in self.registers if r.scanRate])

    def receiveNotification(self, arg):
        print("ScanRateConsideringQueueFeeder:registersChanged")
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
                r.setCommand('r')
                self.queue.put(r)
                r.enqueued = True
            self.delayEvent.wait(self.delay)


class CommunicationProcessor(threading.Thread):
    def __init__(self, queue):
        super(CommunicationProcessor, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            r = self.queue.get()
            # r.process()
            r.lastContact = datetime.datetime.now()
            print("Dequeued: {0!s}".format(r))
            r.enqueued = False


class CmdInterpreter(cmd.Cmd):
    def __init__(self, infile, outfile):
        super(CmdInterpreter, self).__init__(stdin=infile, stdout=outfile)
        self.use_rawinput = False

    def do_test(self, arg):
        self.stdout.write("This is the test response\n\r")

    def do_notify(self, arg):
        nf.notify()

    def do_bye(self, arg):
        self.stdout.write("Bye!\n\r")
        return True


class CmdHandle(socketserver.StreamRequestHandler):
    def handle(self):
        cmd = CmdInterpreter(io.TextIOWrapper(self.rfile), io.TextIOWrapper(self.wfile))
        try:
            cmd.cmdloop()
            print("Cmd handle terminated")
        except ConnectionAbortedError as e:
            print("Cmd handle externally interrupted")


class CmdServer(threading.Thread):
    def __init__(self, address, port):
        super(CmdServer, self).__init__()
        self.server = socketserver.ThreadingTCPServer((address, port), CmdHandle)

    def start(self):
        self.server.serve_forever()





datapoints = [
    HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
    HoldingRegisterDatapoint('Frequency', 1, 0x2020, 2, datetime.timedelta(seconds=10), 'Pub/Frequency', None, None),
    HoldingRegisterDatapoint('Current', 1, 0x2060, 2, datetime.timedelta(seconds=10), 'Pub/Current', None, None),
    HoldingRegisterDatapoint('Resistance Channel 1', 2, 0x0004, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel1', None, None),
    HoldingRegisterDatapoint('Temperature Channel 1', 2, 0x000c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel1', None, None),
    HoldingRegisterDatapoint('Resistance Channel 2', 2, 0x0014, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel2', None, None),
    HoldingRegisterDatapoint('Temperature Channel 2', 2, 0x001c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel2', None, None),
    HoldingRegisterDatapoint('Relay1', 5, 0x0001, 1, None, None, 'Sub/Relay1', 'Feedback/Relay1')
]

queue = queue.PriorityQueue()
nf = NotificationForwarder()
config = Config()

if __name__ == "__main__":
    cp = CommunicationProcessor(queue)
    cp.start()

    mp = MqttProcessor(datapoints, queue)
    nf.register(mp)
    mp.start()

    qf = ScanRateConsideringQueueFeeder(datapoints, queue)
    nf.register(qf)
    qf.start()

    cs = CmdServer('127.0.0.1',9999)
    cs.start()