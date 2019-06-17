from pymodbus.client.sync import ModbusSerialClient
import RS485Ext

ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()
result = client.read_holding_registers(address=0x2000, count=2, unit=1)
print(result)
print(result.registers)
client.close()
