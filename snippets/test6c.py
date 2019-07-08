from pymodbus.client.sync import ModbusSerialClient
import RS485Ext
import time

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=9600, stopbits=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

try:
   result = client.write_register(address=0x9c47, unit=4, value=0x8000)
   # result = client.write_coil(address=0x0000, unit=4, value=1)
   print(result)
except Exception as e:
   print("ERROR: %s" % str(e))

client.close()

