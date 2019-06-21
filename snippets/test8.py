import queue
import datetime
import threading

class AbstractModbusDatapoint(object):
    def __init__(self, label, unit, address, count):
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.type = 'abstract data point'

    def __str__(self):
        return "{0}, {1}: {2} {3} {4}".format(self.type, self.label, self.unit, self.address, self.count)

class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super(AbstractModbusDatapoint, self).__init__(label, unit, address, count)
        self.scanRate = scanRate
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.lastContact = 0
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
        super(object, self).__init__()
        self.registers = registers
        self.queue = queue

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
        # notify using event


class ScanRateProcessingQueueFeeder(threading.Thread):
    def __init__(self, registers, queue):
        super(threading.Thread, self).__init__()
        self.registers = registers
        self.queue = queue

    def run(self):
        pass
        # search registers with expired scanRate (lastContact + scanRate * backoff < now)
        # put into low prio queue








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
    HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, 60.0, 'Pub/Voltage', None, None),
    HoldingRegisterDatapoint('Frequency', 1, 0x2020, 2, 60.0, 'Pub/Frequency', None, None),
    HoldingRegisterDatapoint('Current', 1, 0x2060, 2, 60.0, 'Pub/Current', None, None),
    HoldingRegisterDatapoint('Resistance Channel 1', 2, 0x0004, 2, 1.0, 'Pub/ResistanceChannel1', None, None),
    HoldingRegisterDatapoint('Temperature Channel 1', 2, 0x000c, 2, 1.0, 'Pub/TemperatureChannel1', None, None),
    HoldingRegisterDatapoint('Resistance Channel 2', 2, 0x0014, 2, 1.0, 'Pub/ResistanceChannel2', None, None),
    HoldingRegisterDatapoint('Temperature Channel 2', 2, 0x001c, 2, 1.0, 'Pub/TemperatureChannel2', None, None),
    HoldingRegisterDatapoint('Relay1', 5, 0x0001, 1, 0.0, None, 'Sub/Relay1', 'Feedback/Relay1')
]


