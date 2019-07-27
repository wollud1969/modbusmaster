import serial
# import wiringpi
import Pins
import array
import fcntl
import termios

DE_PIN = 0

class MyRS485(serial.Serial):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # wiringpi.wiringPiSetup()
        # wiringpi.pinMode(DE_PIN, wiringpi.OUTPUT)
        self.buf = array.array('h', [0])

    def write(self, b):
        # wiringpi.digitalWrite(DE_PIN, wiringpi.HIGH)
        Pins.pinsWrite('DE', True)
        super().write(b)
        while True:
            fcntl.ioctl(self.fileno(), termios.TIOCSERGETLSR, self.buf, 1)
            if self.buf[0] & termios.TIOCSER_TEMT:
                break
        # wiringpi.digitalWrite(DE_PIN, wiringpi.LOW)
        Pins.pinsWrite('DE', False)

