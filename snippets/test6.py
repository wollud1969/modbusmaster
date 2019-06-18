from pymodbus.client.sync import ModbusSerialClient
import RS485Ext
import time

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200, stopbits=2)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()

while True:
    try:
        result = client.read_holding_registers(address=0x2000, count=2, unit=1)
        print(result)
        print(result.registers)
    except Exception as e:
        print("ERROR: %s" % str(e))
    time.sleep(2)

client.close()

