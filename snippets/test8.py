import queue
import datetime
import threading
import socketserver
import cmd
import io

class AbstractModbusDatapoint(object):
    def __init__(self, label, unit, address, count, scanRate):
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.scanRate = scanRate
        self.type = 'abstract data point'
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
        return "{0}, {1}: {2} {3} {4}".format(self.type, self.label, self.unit, self.address, self.count)

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


class MqttProcessor(threading.Thread):
    def __init__(self, registers, queue):
        super(MqttProcessor, self).__init__()
        self.registers = registers
        self.queue = queue

    def registersChanged(self):
        pass
        # subscribe and/or unsubscribe according to register changes

    def run(self):
        pass
        # set mqtt callbacks
        # mqtt connect
        # mqtt loop forever

    def onConnect(self):
        pass
        # subscribe to all subscribe topics from registers

    def onMessage(self, topic, payload):
        pass
        # call onMessage method of register with related subscribe topic
        # put register yourself in high prio queue
        # self.put(r)


class ScanRateConsideringQueueFeeder(threading.Thread):
    def __init__(self, registers, queue):
        super(ScanRateConsideringQueueFeeder, self).__init__()
        self.registers = registers
        self.queue = queue
        self.delayEvent = threading.Event()

    def getMinimalScanrate(self):
            return min([r.scanRate.total_seconds() for r in self.registers if r.scanRate])

    def registersChanged(self):
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
        self.stdout.write("This is the test response")

    def do_bye(self, arg):
        self.stdout.write("Bye!")
        return True


class CmdHandle(socketserver.StreamRequestHandler):
    def handle(self):
        print("About to handle cmd session")
        cmd = CmdInterpreter(io.TextIOWrapper(self.rfile), io.TextIOWrapper(self.wfile))
        cmd.cmdloop()

    def finish(self):
        super(CmdHandle, self).finish()
        print("END")

class CmdServer(object):
    def __init__(self, address, port):
        self.server = socketserver.ThreadingTCPServer((address, port), CmdHandle)
        self.serverThread = threading.Thread(target=self.server.serve_forever())

    def start(self):
        self.serverThread.start()






#  ModbusRequestDefinition(4, 0x2000, 2, 'F', '(ERR) Unavailable device'),
#  ModbusRequestDefinition(1, 0x2000, 4, 'F', '(ERR) Wrong register size'),
#  ModbusRequestDefinition(1, 0x2000, 2, 'F', 'Voltage'),
#  ModbusRequestDefinition(1, 0x2020, 2, 'F', 'Frequency'),
#  ModbusRequestDefinition(1, 0x2060, 2, 'F', 'Current'),
#  ModbusRequestDefinition(3, 0x0004, 2, 'RF', 'Resistance Channel 1'),
#  ModbusRequestDefinition(3, 0x000C, 2, 'RF', 'Temperature Channel 1'),
#  ModbusRequestDefinition(3, 0x0014, 2, 'RF', 'Resistance Channel 2'),
#  ModbusRequestDefinition(3, 0x001C, 2, 'RF', 'Temperature Channel 2'),


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



if __name__ == "__main__":
    #cp = CommunicationProcessor(queue)
    #cp.start()

    #qf = ScanRateConsideringQueueFeeder(datapoints, queue)
    #qf.start()

    cs = CmdServer('0.0.0.0',9999)
    cs.start()