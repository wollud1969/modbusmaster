import datetime
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException


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
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __str__(self):
        return "{0}, {1}: Unit: {2},  Address: {3}, Count: {4}".format(self.type, self.label, self.unit, self.address, self.count)

    def process(self, client):
        raise NotImplementedError


class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.lastContact = None
        self.type = 'holding register'

    def __str__(self):
        return "[{0!s}, Read: {1}, Write: {2}, Feedback: {3}".format(super().__str__(), self.publishTopic, self.subscribeTopic, self.feedbackTopic)

    def process(self, client):
        successFull = False
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




class InputRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.lastContact = None
        self.type = 'input register'

    def __str__(self):
        return "[{0!s}, {1}".format(super().__str__(), self.publishTopic)

    def process(self, client):
        successFull = False
        giveUp = False
        # perform read operation
        result = client.read_input_registers(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            raise DatapointException(result)
        print("{0}: {1!s}".format(self.label, result.registers))        

        print("Input register, perform read operation")
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


