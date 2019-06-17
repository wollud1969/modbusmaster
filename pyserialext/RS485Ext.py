import serial.rs485
import serial.serialutil
import ctypes


class RS485Ext(serial.rs485.RS485):
    def __init__(self, *args, **kwargs):
        super(RS485Ext, self).__init__(*args, **kwargs)
        self.writec = ctypes.cdll.LoadLibrary('writec.so')
        fd = self.fileno()
        r = self.writec.set_rs485_mode(fd)

    def write(self, b):
        d = serial.serialutil.to_bytes(b)
        l = len(d)
        fd = self.fileno()
        r = self.writec.writec(fd, d, l)
        return r

