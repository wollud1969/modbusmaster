import datetime
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException
import MqttProcessor
import logging
import json


class DatapointException(Exception): pass

class AbstractModbusDatapoint(object):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None):
        self.argList = ['label', 'unit', 'address', 'count', 'scanRate']
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        if type(scanRate) == float:
            self.scanRate = datetime.timedelta(seconds=scanRate)
        else:
            self.scanRate = scanRate
        self.type = 'abstract data point'
        self.enqueued = False
        self.lastContact = None
        self.errorCount = 0
        self.processCount = 0
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __str__(self):
        return ("{0}, {1}: unit: {2},  address: {3}, count: {4}, scanRate: {5}, "
                "enqueued: {6}, lastContact: {7}, errorCount: {8}, processCount: {9}"
                .format(self.type, self.label, self.unit, self.address, self.count,
                        self.scanRate, self.enqueued, self.lastContact,
                        self.errorCount, self.processCount))

    def jsonify(self):
        return {'type':self.__class__.__name__, 
                'args': { k: getattr(self, k) for k in self.argList }
               }

    def process(self, client):
        raise NotImplementedError



class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, 
                 publishTopic=None, subscribeTopic=None, feedbackTopic=None):
        super().__init__(label, unit, address, count, scanRate)
        self.argList = self.argList + ['publishTopic', 'subscribeTopic', 'feedbackTopic']
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
        logger = logging.getLogger('HoldingRegisterDatapoint')
        if self.writeRequestValue:
            # perform write operation
            logger.debug("Holding register, perform write operation")
            self.writeRequestValue = None
        else:
            # perform read operation
            logger.debug("Holding register, perform read operation")
            self.processCount += 1
            result = client.read_holding_registers(address=self.address, 
                                                   count=self.count, 
                                                   unit=self.unit)
            if type(result) in [ExceptionResponse, ModbusIOException]:
                self.errorCount += 1
                raise DatapointException(result)
            logger.debug("{0}: {1!s}".format(self.label, result.registers))
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.registers)))
            self.lastContact = datetime.datetime.now()
    
    def onMessage(self, value):
        self.writeRequestValue = value


class ReadOnlyDatapoint(AbstractModbusDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, publishTopic=None):
        super().__init__(label, unit, address, count, scanRate)
        self.argList = self.argList + ['updateOnly', 'publishTopic']
        self.updateOnly = updateOnly
        self.lastValue = None
        self.publishTopic = publishTopic

    def __str__(self):
        return ("[{0!s}, updateOnly: {1}, publishTopic: {2}, lastValue: {3!s}"
                .format(super().__str__(), self.updateOnly, self.publishTopic,
                        self.lastValue))



class InputRegisterDatapoint(ReadOnlyDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, publishTopic=None):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic)
        self.type = 'input register'

    def process(self, client, pubQueue):
        logger = logging.getLogger('InputRegisterDatapoint')
        # perform read operation
        logger.debug("Input register, perform read operation")
        self.processCount += 1
        result = client.read_input_registers(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            self.errorCount += 1
            raise DatapointException(result)
        if not self.updateOnly or (result.registers != self.lastValue):
            self.lastValue = result.registers
            logger.debug("{0}: {1!s}".format(self.label, result.registers))        
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.registers)))
        self.lastContact = datetime.datetime.now()


class DiscreteInputDatapoint(ReadOnlyDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, publishTopic=None):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic)
        self.type = 'discrete input'

    def process(self, client, pubQueue):
        logger = logging.getLogger('DiscreteInputDatapoint')
        # perform read operation
        logger.debug("Discrete input, perform read operation")
        self.processCount += 1
        result = client.read_discrete_inputs(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            self.errorCount += 1
            raise DatapointException(result)
        if not self.updateOnly or (result.bits != self.lastValue):
            self.lastValue = result.bits
            logger.debug("{0}: {1!s}".format(self.label, result.bits))        
            pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(result.bits)))
        self.lastContact = datetime.datetime.now()




class JsonifyEncoder(json.JSONEncoder):
    def default(self, o):
        res = None
        try:
            res = o.jsonify()
        except (TypeError, AttributeError):
            if type(o) == datetime.timedelta:
                res = o.total_seconds()
            else:
                res = super().default(o)
        return res

def datapointObjectHook(j):
    if type(j) == dict and 'type' in j and 'args' in j:
        klass = eval(j['type'])
        o = klass(**j['args'])
        return o
    else:
        return j

def saveRegisterList(registerList, registerListFile):
    js = json.dumps(registerList, cls=JsonifyEncoder, sort_keys=True, indent=4)
    with open(registerListFile, 'w') as f:
        f.write(js)
    
def loadRegisterList(registerListFile):
    with open(registerListFile, 'r') as f:
        js = f.read()
        registerList = json.loads(js, object_hook=datapointObjectHook)
        return registerList

