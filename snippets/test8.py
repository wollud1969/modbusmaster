import queue
import datetime
import threading
import socketserver
import cmd
import io
import paho.mqtt.client as mqtt
import re


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

    def __str__(self):
        return "{0}, {1}: {2} {3} {4} {5} {6}".format(self.type, self.label, self.unit, self.address, self.count, self.command, self.value)
    
    def setCommand(self, cmd):
        self.command = cmd
    
    def setValue(self, value):
        self.value = value


class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.lastContact = None
        self.type = 'read holding register'

    def __str__(self):
        return "[{0!s}, {1} {2} {3}".format(super().__str__(), self.publishTopic, self.subscribeTopic, self.feedbackTopic)

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
        super().__init__()
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
        super().__init__()
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
        super().__init__()
        self.queue = queue

    def run(self):
        while True:
            r = self.queue.get()
            # r.process()
            r.lastContact = datetime.datetime.now()
            print("Dequeued: {0!s}".format(r))
            r.enqueued = False


class MyPriorityQueueItem(object):
    def __init__(self, itemWithPriority):
        self.itemWithPriority = itemWithPriority

    def __lt__(self, other): return self.itemWithPriority.priority < other.itemWithPriority.priority
    def __le__(self, other): return self.itemWithPriority.priority <= other.itemWithPriority.priority
    def __eq__(self, other): return self.itemWithPriority.priority == other.itemWithPriority.priority
    def __ne__(self, other): return self.itemWithPriority.priority != other.itemWithPriority.priority
    def __gt__(self, other): return self.itemWithPriority.priority > other.itemWithPriority.priority
    def __ge__(self, other): return self.itemWithPriority.priority >= other.itemWithPriority.priority

class MyPriorityQueue(queue.PriorityQueue):
    def _put(self, itemWithPriority):
        i = MyPriorityQueueItem(itemWithPriority)
        super()._put(i)

    def _get(self):
        i = super()._get()
        return i.itemWithPriority

class CmdInterpreterException(ValueError): pass

def parseIntArbitraryBase(s):
    i = 0
    if s.startswith('0x'):
        i = int(s, 16)
    elif s.startswith('0b'):
        i = int(s, 2)
    else:
        i = int(s, 10)
    return i

class CmdInterpreter(cmd.Cmd):
    def __init__(self, infile, outfile, notifier, registers):
        super().__init__(stdin=infile, stdout=outfile)
        self.use_rawinput = False
        self.notifier = notifier
        self.registers = registers
        self.prompt = "test8> "
        self.intro = "test8 admin interface"
        self.splitterRe = re.compile('\s+')

    def __print(self, text):
        self.stdout.write(text)

    def __println(self, text):
        self.stdout.write(text)
        self.stdout.write("\n\r")

    def do_notify(self, arg):
        self.notifier.notify()

    def help_notify(self):
        self.__println("Notifies threads using the list of datapoints about changes in this list.")
        self.__println("Call after modifications on the list.")

    def do_quit(self, arg):
        self.__println("Bye!")
        return True
    
    def do_add(self, arg):
        try:
            (registerType, label, unit, address, count, scanrate, readTopic, writeTopic, feedbackTopic) = self.splitterRe.split(arg)
            self.__println("RegisterType:  {0}".format(registerType))
            self.__println("Label:         {0}".format(label))
            self.__println("Unit:          {0}".format(unit))
            self.__println("Address:       {0}".format(address))
            self.__println("Count:         {0}".format(count))
            self.__println("ScanRate:      {0}".format(scanrate))
            self.__println("ReadTopic:     {0}".format(readTopic))
            self.__println("WriteTopic:    {0}".format(writeTopic))
            self.__println("FeedbackTopic: {0}".format(feedbackTopic))

            if readTopic == 'None':
                readTopic = None
            if writeTopic == 'None':
                writeTopic = None
            if feedbackTopic == 'None':
                feedbackTopic = None
            unit = parseIntArbitraryBase(unit)
            address = parseIntArbitraryBase(address)
            count = parseIntArbitraryBase(count)
            scanrate = float(scanrate)
            if scanrate == 0:
                if readTopic:
                    raise CmdInterpreterException('readTopic must not be set when scanRate is zero')
                if not writeTopic:
                    raise CmdInterpreterException('writeTopic must be set when scanRate is zero')
                if not feedbackTopic:
                    raise CmdInterpreterException('feedbackTopic must be set when scanRate is zero')
            else:
                if not readTopic:
                    raise CmdInterpreterException('readTopic must be set when scanRate is zero')
                if writeTopic:
                    raise CmdInterpreterException('writeTopic must not be set when scanRate is zero')
                if feedbackTopic:
                    raise CmdInterpreterException('feedbackTopic must not be set when scanRate is zero')
            allowedRegisterTypes = ['HoldingRegister']
            if registerType not in allowedRegisterTypes:
                raise CmdInterpreterException('Unknown register type {0}, allowed are {1!s}'.format(registerType, allowedRegisterTypes))


        except ValueError as e:
            self.__println("ERROR: {0!s}, {1!s}".format(e.__class__.__name__, e))

    def help_add(self):
        # HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
        self.__println("Usage: add <RegisterType> <Label> <Unit> <Address> <Count> <ScanRate>")
        self.__println("           <ReadTopic> <WriteTopic> <FeedbackTopic>")
        self.__println("---------------------------------------------------------------------")
        self.__println("<RegisterType>               One of HoldingRegister, ...")
        self.__println("<Label>                      Descriptive label")
        self.__println("<Unit>                       Modbus address of the device")
        self.__println("<Address>                    Register address within the device")
        self.__println("<Count>                      Count of registers to be read or write in words")
        self.__println("<ScanRate>                   Scanrate in seconds (float), for write datapoints")
        self.__println("                             set to zero (0)")
        self.__println("<ReadTopic>                  Topic to publish read data")
        self.__println("<WriteTopic>                 Topic to be subscribe to receive data to be")
        self.__println("                             written")
        self.__println("<FeedbackTopic>              Topic to publish feedback after a write process")
        self.__println("")
        self.__println("For read items the <ScanRate> must be non-zero, a <ReadTopic> must be set and")
        self.__println("<WriteTopic> and <FeedbackTopic> must be <None>.")
        self.__println("For write items the <ScanRate> must be zero, <ReadTopic> must be <None> and ")
        self.__println("<WriteTopic> and <FeedbackTopic> must be set.")

    def do_list(self, arg):
        for i, r in enumerate(self.registers):
            self.__println("#{0}: {1!s}".format(i, r))
    
    def help_list(self):
        self.__println("Usage: list")
        self.__println("-----------")
        self.__println("List the configured datapoints")

    def do_del(self, arg):
        try:
            i = int(arg)
            r = self.registers[i]
            self.registers.remove(r)
            self.__println("{0!s} removed".format(r))
        except ValueError as e:
            self.__println("ERROR: {0!s}".format(e))

    def help_del(self):
        self.__println("Usage: del <idx>")
        self.__println("Removes an item from the list of datapoints by its index, see list command.")
        self.__println("Be aware: indexes have been changed, rerun list before removing the next item.")


class CmdHandle(socketserver.StreamRequestHandler):
    def handle(self):
        cmd = CmdInterpreter(io.TextIOWrapper(self.rfile), io.TextIOWrapper(self.wfile), self.server.userData.notifier, self.server.userData.registers)
        try:
            cmd.cmdloop()
            print("Cmd handle terminated")
        except ConnectionAbortedError as e:
            print("Cmd handle externally interrupted")

class MyThreadingTCPServer(socketserver.ThreadingTCPServer):
    def __init__(self, host, handler, userData):
        super().__init__(host, handler)
        self.userData = userData

class MyCmdUserData(object):
    def __init__(self, notifier, registers):
        self.notifier = notifier
        self.registers = registers

class CmdServer(threading.Thread):
    def __init__(self, address, port, notifier, registers):
        super().__init__()
        self.server = MyThreadingTCPServer((address, port), CmdHandle, MyCmdUserData(notifier, registers))

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

queue = MyPriorityQueue()
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

    cs = CmdServer('127.0.0.1',9999, nf, datapoints)
    cs.start()