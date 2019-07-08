from pymodbus.client.sync import ModbusSerialClient
from pymodbus.pdu import ExceptionResponse
from pymodbus.exceptions import ModbusIOException
import RS485Ext
import struct
import time

def registersToIeeeFloat(i):
  return struct.unpack('f', bytes(
                                   [((x & 0xff00) >> 8) if y else (x & 0x00ff) 
                                     for x in i[::-1] 
                                     for y in [False, True]
                                   ]
                                 )
                      )[0]

def registersToIeeeFloatReverse(i):
  return struct.unpack('f', bytes(
                                   [((x & 0xff00) >> 8) if y else (x & 0x00ff) 
                                     for x in i 
                                     for y in [False, True]
                                   ]
                                 )
                      )[0]

def dataConverter(t, d):
  if t == 'F':
    return registersToIeeeFloat(d)
  elif t == 'RF':
    return registersToIeeeFloatReverse(d)
  else:
    raise Exception("Converter '{0}' is not supported".format(t))


class ModbusException(Exception):
  def __init__(self, resp):
    self.msg = str(result)

  def __str__(self):
    return self.msg

class ModbusRequestDefinition(object):
  def __init__(self, kind, unit, address, count, converter, label):
    self.kind = kind
    self.unit = unit
    self.address = address
    self.count = count
    self.converter = converter
    self.label = label
  
reqs = [
#  ModbusRequestDefinition(4, 0x2000, 2, 'F', '(ERR) Unavailable device'),
#  ModbusRequestDefinition(1, 0x2000, 4, 'F', '(ERR) Wrong register size'),
#  ModbusRequestDefinition(1, 0x2000, 2, 'F', 'Voltage'),
#  ModbusRequestDefinition(1, 0x2020, 2, 'F', 'Frequency'),
#  ModbusRequestDefinition(1, 0x2060, 2, 'F', 'Current'),
#  ModbusRequestDefinition('H', 3, 0x0004, 2, 'RF', 'Resistance Channel 1'),
#  ModbusRequestDefinition('H', 3, 0x000C, 2, 'RF', 'Temperature Channel 1'),
#  ModbusRequestDefinition('H', 3, 0x0014, 2, 'RF', 'Resistance Channel 2'),
#  ModbusRequestDefinition('H', 3, 0x001C, 2, 'RF', 'Temperature Channel 2'),
  ModbusRequestDefinition('D', 4, 0x0000, 1, '', 'Discrete Input'),
  ModbusRequestDefinition('I', 5, 0x0001, 1, '', 'Temperature'),
  ModbusRequestDefinition('I', 5, 0x0002, 1, '', 'Humidity'),
]


def getSerial():
  return RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=9600, stopbits=1,
                           timeout=1)

client = ModbusSerialClient(method='rtu')
client.socket = getSerial()
client.connect()

delay = 0.05
period = 0.5

while True:
  for req in reqs:
    try:
      time.sleep(delay)
      if req.kind == 'H':
        # print("Trying to read: {0} {1} {2}".format(req.address, req.count, req.unit))
        result = client.read_holding_registers(address=req.address, 
                                               count=req.count, 
                                               unit=req.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
          raise ModbusException(result)
        print("{0}: {1:.2f}".format(req.label, 
                                    dataConverter(req.converter, 
                                                  result.registers)))
      elif req.kind == 'D':
        result = client.read_discrete_inputs(address=req.address,
                                             count=req.count,
                                             unit=req.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
          raise ModbusException(result)
        print("{0}: {1!s}".format(req.label, result.bits))        
      elif req.kind == 'I':
        result = client.read_input_registers(address=req.address,
                                             count=req.count,
                                             unit=req.unit)
        if type(result) in [ExceptionResponse, ModbusIOException]:
          raise ModbusException(result)
        print("{0}: {1}".format(req.label, result.registers))        
    except ModbusException as e:
      print("ERROR when querying '{0}': {1!s}".format(req.label, e))
      if client.socket is None:
        print("renew socket")
        client.socket = getSerial()

  print("-------------")
  time.sleep(period)


client.close()

