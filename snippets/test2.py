import serial.rs485
ser=serial.rs485.RS485(port='/dev/ttyAMA0',baudrate=2400)
ser.rs485_mode = serial.rs485.RS485Settings(False,True)
ser.write('a test'.encode('utf-8'))

while True:
	c = ser.read(1)
	ser.write(c)
	print(c, end='')

