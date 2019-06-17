from pymodbus.client.sync import ModbusSerialClient
import serial.rs485
import RS485Ext

#ser=serial.rs485.RS485(port='/dev/ttyAMA0',baudrate=1200)
#ser.rs485_mode = serial.rs485.RS485Settings(rts_level_for_tx=False, 
#                                            rts_level_for_rx=True,
#                                            delay_before_tx=0.005,
#                                            delay_before_rx=-0.0)
ser=RS485Ext.RS485Ext(port='/dev/ttyAMA0', baudrate=1200)

client = ModbusSerialClient(method='rtu')
client.socket = ser
client.connect()
result = client.read_holding_registers(address=0x2000, count=2, unit=1)
print(result)
print(result.registers)
client.close()
