
class Config(object):
    def __init__(self):
        self.mqttBrokerHost = '172.16.2.16'
        self.mqttBrokerPort = 1883
        self.mqttLogin = ''
        self.mqttPassword = ''
        self.cmdAddress = '127.0.0.1'
        self.cmdPort = 9999
        self.registerFile = 'registers.pkl'
        self.serialPort = '/dev/ttyAMA0'
        self.serialBaudRate = 9600
        self.interCommDelay = 0.025
