from pymodbus.client.sync import ModbusSerialClient
from pymodbus.pdu import ExceptionResponse
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
  def __init__(self, unit, address, count, converter, label):
    self.unit = unit
    self.address = address
    self.count = count
    self.converter = converter
    self.label = label
  
reqs = [
  ModbusRequestDefinition(1, 0x2000, 2, 'F', 'Voltage'),
  ModbusRequestDefinition(1, 0x2020, 2, 'F', 'Frequency'),
  ModbusRequestDefinition(1, 0x2060, 2, 'F', 'Current'),
  ModbusRequestDefinition(3, 0x0004, 2, 'RF', 'Resistance Channel 1'),
  ModbusRequestDefinition(3, 0x000C, 2, 'RF', 'Temperature Channel 1'),
  ModbusRequestDefinition(3, 0x0014, 2, 'RF', 'Resistance Channel 2'),
  ModbusRequestDefinition(3, 0x001C, 2, 'RF', 'Temperature Channel 2'),
]




ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200, stopbits=1,
                      timeout=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

delay = 0.05

while True:
  for req in reqs:
    try:
      time.sleep(delay)
      result = client.read_holding_registers(req.address, req.count, req.unit)
      if type(result) in (ExceptionResponse):
        raise ModbusException(result)
      print("{0}: {1:.2f}". format(dataConverter(req.converter, result.registers)))
    except ModbusException as e:
      print("ERROR: %s" % e)
    finally:
      print("-------------")
      time.sleep(10)

client.close()

