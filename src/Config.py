
class Config(object):
    def __init__(self):
        self.mqttBrokerHost = '127.0.0.1'
        self.mqttBrokerPort = 1883
        self.mqttLogin = ''
        self.mqttPassword = ''
        self.cmdAddress = '127.0.0.1'
        self.cmdPort = 9999
        self.registerFile = 'registers.pkl'
        self.serialPort = '/dev/ttyAMA0'
        self.serialBaudRate = 9600

