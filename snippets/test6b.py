from pymodbus.client.sync import ModbusSerialClient
import RS485Ext
import time

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=9600, stopbits=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

try:
   result = client.read_holding_registers(address=0x9c43, count=1, unit=4)
   # result = client.read_holding_registers(address=0x0102, count=1, unit=5)
   # result = client.read_input_registers(address=0x0002, count=1, unit=5)
   # result = client.read_discrete_inputs(address=0x0000, count=1, unit=4)
   print(result)
   print(result.registers)
   # print(result.bits)
except Exception as e:
   print("ERROR: %s" % str(e))

client.close()

