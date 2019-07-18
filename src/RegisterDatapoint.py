import datetime
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException
import MqttProcessor
import logging
import json
import Converters

class DatapointException(Exception): pass

class AbstractModbusDatapoint(object):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, converter=None):
        self.argList = ['label', 'unit', 'address', 'count', 'scanRate', 'converter']
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.converter = converter
        if type(scanRate) == float:
            self.scanRate = datetime.timedelta(seconds=scanRate)
        else:
            self.scanRate = scanRate
        self.type = 'abstract data point'
        self.enqueued = False
        self.lastContact = None
        self.errorCount = 0
        self.readCount = 0
        self.writeCount = 0
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __str__(self):
        return ("{0}, {1}: unit: {2},  address: {3}, count: {4}, scanRate: {5}, "
                "enqueued: {6}, lastContact: {7}, errorCount: {8}, readCount: {9}, "
                "writeCount: {10}, converter: {11}"
                .format(self.type, self.label, self.unit, self.address, self.count,
                        self.scanRate, self.enqueued, self.lastContact,
                        self.errorCount, self.readCount, self.writeCount, self.converter))

    def jsonify(self):
        return {'type':self.__class__.__name__, 
                'args': { k: getattr(self, k) for k in self.argList }
               }

    def process(self, client):
        raise NotImplementedError



class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, 
                 publishTopic=None, subscribeTopic=None, feedbackTopic=None, converter=None):
        super().__init__(label, unit, address, count, scanRate, converter)
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
            self.writeCount += 1
            values = None
            logger.debug("{0}: raw: {1!s}".format(self.label, self.writeRequestValue))
            if self.converter and Converters.Converters[self.converter]['out']:
                try:
                    values = Converters.Converters[self.converter]['out'](self.writeRequestValue)
                    logger.debug("{0}: converted: {1!s}".format(self.label, values))
                except Exception as e:
                    raise DatapointException("Exception caught when trying to converter modbus data: {0!s}".format(e))
            else:
                values = [int(self.writeRequestValue)]
            result = client.write_registers(address=self.address,
                                           unit=self.unit,
                                           values=values)
            logger.debug("Write result: {0!s}".format(result))                
            self.writeRequestValue = None
        else:
            # perform read operation
            logger.debug("Holding register, perform read operation")
            self.readCount += 1
            result = client.read_holding_registers(address=self.address, 
                                                   count=self.count, 
                                                   unit=self.unit)
            if type(result) in [ExceptionResponse, ModbusIOException]:
                self.errorCount += 1
                raise DatapointException(result)
            logger.debug("{0}: {1!s}".format(self.label, result.registers))
            value = None
            if self.converter and Converters.Converters[self.converter]['in']:
                try:
                    value = Converters.Converters[self.converter]['in'](result.registers)
                    logger.debug("{0}: converted: {1!s}".format(self.label, value))
                except Exception as e:
                    raise DatapointException("Exception caught when trying to converter modbus data: {0!s}".format(e))
            else:
                value = result.registers
            if self.publishTopic:
                pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(value)))
            self.lastContact = datetime.datetime.now()
    
    def onMessage(self, value):
        self.writeRequestValue = value


class CoilDatapoint(AbstractModbusDatapoint):
    def __init__(self, label=None, unit=None, address=None, scanRate=None, publishTopic=None, subscribeTopic=None,
                 feedbackTopic=None):
        super().__init__(label, unit, address, 1, scanRate, None)
        self.argList = ['label', 'unit','address','scanRate','publishTopic', 'subscribeTopic', 'feedbackTopic']
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.type = 'coil'

    def __str__(self):
        return ("{0}, {1}: unit: {2},  address: {3}, scanRate: {4}, "
                "enqueued: {5}, lastContact: {6}, errorCount: {7}, readCount: {8}, "
                "writeCount: {9}, publishTopic: {10}, subscribeTopic: {11}, feedbackTopic: {12}"
                .format(self.type, self.label, self.unit, self.address,
                        self.scanRate, self.enqueued, self.lastContact,
                        self.errorCount, self.readCount, self.writeCount, 
                        self.publishTopic, self.subscribeTopic, self.feedbackTopic))

    def onMessage(self, value):
        self.writeRequestValue = value.decode()

    def process(self, client, pubQueue):
        logger = logging.getLogger('CoilDatapoint')
        if self.writeRequestValue:
            # perform write operation
            logger.debug("Coil, perform write operation")
            self.writeCount += 1
            logger.debug("{0}: raw: {1!s}".format(self.label, self.writeRequestValue))
            value=None
            if self.writeRequestValue in ['true', 'True', 'yes', 'Yes', 'On', 'on']:
                value = True
            elif self.writeRequestValue in ['false', 'False', 'no', 'No', 'Off', 'off']:
                value = False
            else:
                self.writeRequestValue = None
                raise DatapointException('illegal value {0!s} for coil write'.format(self.writeRequestValue))
            result = client.write_coil(address=self.address,
                                       unit=self.unit,
                                       value=value)
            logger.debug("Write result: {0!s}".format(result))                
            self.writeRequestValue = None
        else:
            # perform read operation
            logger.debug("Coil, perform read operation")
            self.readCount += 1
            result = client.read_coils(address=self.address, 
                                       unit=self.unit)
            if type(result) in [ExceptionResponse, ModbusIOException]:
                self.errorCount += 1
                raise DatapointException(result)
            logger.debug("{0}: {1!s}".format(self.label, result.getBit(0)))
            value = result.getBit(0)
            if self.publishTopic:
                pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(value)))
            self.lastContact = datetime.datetime.now()


class ReadOnlyDatapoint(AbstractModbusDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, publishTopic=None, converter=None):
        super().__init__(label, unit, address, count, scanRate, converter)
        self.argList = self.argList + ['updateOnly', 'publishTopic']
        self.updateOnly = updateOnly
        self.lastValue = None
        self.publishTopic = publishTopic

    def __str__(self):
        return ("[{0!s}, updateOnly: {1}, publishTopic: {2}, lastValue: {3!s}"
                .format(super().__str__(), self.updateOnly, self.publishTopic,
                        self.lastValue))



class InputRegisterDatapoint(ReadOnlyDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, 
                 publishTopic=None, converter=None):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic, converter)
        self.type = 'input register'

    def process(self, client, pubQueue):
        logger = logging.getLogger('InputRegisterDatapoint')
        # perform read operation
        logger.debug("Input register, perform read operation")
        self.readCount += 1
        result = client.read_input_registers(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            self.errorCount += 1
            raise DatapointException(result)
        if not self.updateOnly or (result.registers != self.lastValue):
            self.lastValue = result.registers
            logger.debug("{0}: raw: {1!s}".format(self.label, result.registers))
            value = None
            if self.converter and Converters.Converters[self.converter]['in']:
                try:
                    value = Converters.Converters[self.converter]['in'](result.registers)
                    logger.debug("{0}: converted: {1!s}".format(self.label, value))
                except Exception as e:
                    raise DatapointException("Exception caught when trying to converter modbus data: {0!s}".format(e))
            else:
                value = result.registers
            if self.publishTopic:
                pubQueue.put(MqttProcessor.PublishItem(self.publishTopic, str(value)))
        self.lastContact = datetime.datetime.now()


class DiscreteInputDatapoint(ReadOnlyDatapoint):
    def __init__(self, label=None, unit=None, address=None, count=None, scanRate=None, updateOnly=None, 
                 publishTopic=None, converter=None, bitCount=8):
        super().__init__(label, unit, address, count, scanRate, updateOnly, publishTopic, converter)
        self.argList = self.argList + ['bitCount']
        self.type = 'discrete input'
        self.bitCount = bitCount
        self.lastValues = [None] * self.bitCount

    def __str__(self):
        return ("[{0!s}, bitCount: {1}"
                .format(super().__str__(), self.bitCount))

    def process(self, client, pubQueue):
        logger = logging.getLogger('DiscreteInputDatapoint')
        # perform read operation
        logger.debug("Discrete input, perform read operation")
        self.readCount += 1
        result = client.read_discrete_inputs(address=self.address,
                                             count=self.count,
                                             unit=self.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
            self.errorCount += 1
            raise DatapointException(result)
        logger.debug("{0}: raw: {1!s}".format(self.label, result.bits))
        for i in range(self.bitCount):
            if not self.updateOnly or (result.getBit(i) != self.lastValues[i]):
                self.lastValues[i] = result.getBit(i)
                logger.debug("{0}, {1}: changed: {2!s}".format(self.label, i, result.getBit(i)))
                if self.publishTopic:
                    pubQueue.put(MqttProcessor.PublishItem("{0}/{1}".format(self.publishTopic, i), str(result.getBit(i))))
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

