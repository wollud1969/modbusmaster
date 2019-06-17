import serial.rs485
import serial.serialutil
import ctypes


class RS485Ext(serial.rs485.RS485):
    def __init__(self, *args, **kwargs):
        super(RS485Ext, self).__init__(*args, **kwargs)
        self.writec = ctypes.cdll.LoadLibrary('writec.so')
        r = self.writec.init()

    def write(self, b):
        d = serial.serialutil.to_bytes(b)
        r = self.writec.writec(self.fileno(), d, len(d))
        return r

