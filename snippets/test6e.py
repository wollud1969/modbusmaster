from pymodbus.client.sync import ModbusSerialClient
import RS485Ext
import time

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200, stopbits=1)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

while True:
    try:
        result = client.read_discrete_inputs(address=0x0000, count=1, unit=4)
        print(result)
        print(result.bits)
    except Exception as e:
        print("ERROR: %s" % str(e))
    time.sleep(0.5)

client.close()

