import datetime
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException
import MqttProcessor


class DatapointException(Exception): pass

class AbstractModbusDatapoint(object):
    def __init__(self, label, unit, address, count, scanRate):
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.scanRate = scanRate
        self.type = 'abstract data point'
        self.enqueued = False
        self.lastContact = None
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __str__(self):
        return ("{0}, {1}: unit: {2},  address: {3}, count: {4}, scanRate: {5}, "
                "enqueued: {6}, lastContact: {7}"
                .format(self.type, self.label, self.unit, self.address, self.count,
                        self.scanRate, self.enqueued, self.lastContact))

    def process(self, client):
        raise NotImplementedError


class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.type = 'holding register'

    def __str__(self):
        return ("[{0!s}, publishTopic: {1}, subscribeTopic: {2}, feedbackTopic: {3}, "
                "writeRequestValue: {4!s}"
                .format(super().__str__(), self.publishTopic, self.subscribeTopic, self.feedbackTopic,
                        self.writeRequestValue))

    def process(self, client, pubQueue):
        successFull = True
        giveUp = False
        if self.writeRequestValue:
            # perform write operation
            print("Holding register, perform write operation")
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
            print("Holding register, perform read operation")
            result = client.read_holding_registers(address=self.address, 
                                                   count=self.count, 
                                                   unit=self.unit)
            if type(result) in [ExceptionResponse, ModbusIOException]:
                raise DatapointException(result)
            print("{0}: {1!s}".format(self.label, result.registers))
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.registers)))
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


class ReadOnlyDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, updateOnly, publishTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.updateOnly = updateOnly
        self.lastValue = None
        self.publishTopic = publishTopic

    def __str__(self):
        return ("[{0!s}, updateOnly: {1}, publishTopic: {2}, lastValue: {3!s}"
                .format(super().__str__(), self.updateOnly, self.publishTopic,
                        self.lastValue))



class InputRegisterDatapoint(ReadOnlyDatapoint):
    def __init__(self, label, unit, address, count, scanRate, updateOnly, publishTopic):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic)
        self.type = 'input register'

    def process(self, client, pubQueue):
        successFull = True
        giveUp = False
        # perform read operation
        print("Input register, perform read operation")
        result = client.read_input_registers(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            raise DatapointException(result)
        if not self.updateOnly or (result.registers != self.lastValue):
            self.lastValue = result.registers
            print("{0}: {1!s}".format(self.label, result.registers))        
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.registers)))

        if successFull:
            self.lastContact = datetime.datetime.now()
            # publish value
        else:
            # retries handling
            if giveUp:
                # backoff and availability handling
                # give negative feedback
                pass


class DiscreteInputDatapoint(ReadOnlyDatapoint):
    def __init__(self, label, unit, address, count, scanRate, updateOnly, publishTopic):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic)
        self.type = 'discrete input'

    def process(self, client, pubQueue):
        successFull = True
        giveUp = False
        # perform read operation
        print("Discrete input, perform read operation")
        result = client.read_discrete_inputs(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            raise DatapointException(result)
        if not self.updateOnly or (result.bits != self.lastValue):
            self.lastValue = result.bits
            print("{0}: {1!s}".format(self.label, result.bits))        
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.bits)))

        if successFull:
            self.lastContact = datetime.datetime.now()
            # publish value
        else:
            # retries handling
            if giveUp:
                # backoff and availability handling
                # give negative feedback
                pass



def checkRegisterList(registers):
    for r in registers:
        if not isinstance(r, AbstractModbusDatapoint):
            raise ValueError('Entry in register list {0!s} is not derived from class AbstractModbusDatapoint'.format(r))        


