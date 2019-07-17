# in:  from Modbus to MQTT, input is a list of 16bit integers, output shall be the desired format 
#      to be sent in the MQTT message
# out: from MQTT to Modbus, input is the format received from MQTT, output shall be a list of 
#      16bit integers to be written to the Modbus slave

import struct


Converters = {
    "dht20TOFloat": {
        "in": lambda x : float(x[0]) / 10.0,
        "out": None
    },
    "uint32": {
        "in": lambda x : struct.unpack('I', x)[0],
        "out": lambda x : struct.pack('I', x)
    }
}