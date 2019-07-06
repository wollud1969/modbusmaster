from pymodbus.client.sync import ModbusSerialClient
import RS485Ext
import time

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200, stopbits=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

v = 0
while True:
    if v == 0:
        v = 1
    else:
        v = 0
    try:
        result = client.write_coil(address=0x0000, unit=4, value=v)
        print(result)
    except Exception as e:
        print("ERROR: %s" % str(e))
    time.sleep(0.5)

client.close()

