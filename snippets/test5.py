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

class ModbusException(Exception):
  def __init__(self, resp):
    self.msg = str(result)

  def __str__(self):
    return self.msg



ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200, stopbits=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

delay = 0.05

try:
  # BG-Tech, Voltage
  result = client.read_holding_registers(address=0x2000, count=2, unit=1)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Voltage: {:.2f}".format(registersToIeeeFloat(result.registers)))

  time.sleep(delay)

  # BG-Tech, Frequency
  result = client.read_holding_registers(address=0x2020, count=2, unit=1)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Frequency: {:.2f}".format(registersToIeeeFloat(result.registers)))

  time.sleep(delay)

  # BG-Tech, Current
  result = client.read_holding_registers(address=0x2060, count=2, unit=1)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Current: {:.2f}".format(registersToIeeeFloat(result.registers)))

  time.sleep(delay)

  # Hottis Thermometer, Resistance Channel 1
  result = client.read_holding_registers(address=0x0004, count=2, unit=3)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Resistance Channel 1: {:.2f}".format(registersToIeeeFloatReverse(result.registers)))

  time.sleep(delay)

  # Hottis Thermometer, Temperature Channel 1
  result = client.read_holding_registers(address=0x000c, count=2, unit=3)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Temperature Channel 1: {:.2f}".format(registersToIeeeFloatReverse(result.registers)))

  time.sleep(delay)

  # Hottis Thermometer, Resistance Channel 2
  result = client.read_holding_registers(address=0x0014, count=2, unit=3)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Resistance Channel 2: {:.2f}".format(registersToIeeeFloatReverse(result.registers)))

  time.sleep(delay)

  # Hottis Thermometer, Temperature Channel 2
  result = client.read_holding_registers(address=0x001c, count=2, unit=3)
  if type(result) == ExceptionResponse:
    raise ModbusException(result)
  print("Temperature Channel 2: {:.2f}".format(registersToIeeeFloatReverse(result.registers)))
except ModbusException as e:
  print("ERROR: %s" % e)
finally:
  client.close()
