import threading
import datetime
# import RS485Ext
import RegisterDatapoint
from pymodbus.client.sync import ModbusSerialClient
import wiringpi
import MyRS485
import time


ERROR_PIN = 29

class CommunicationProcessor(threading.Thread):
    def __init__(self, config, queue, pubQueue):
        super().__init__()
        self.config = config
        self.queue = queue
        self.pubQueue = pubQueue
        wiringpi.wiringPiSetup()
        wiringpi.pinMode(ERROR_PIN, wiringpi.OUTPUT)
        self.daemon = True

    def __getSerial(self):
        # return RS485Ext.RS485Ext(port=self.config.serialPort, baudrate=self.config.serialBaudRate, stopbits=1,
        #                         timeout=1)
        return MyRS485.MyRS485(port=self.config.serialPort, baudrate=self.config.serialBaudRate, stopbits=1,
                               timeout=1)


    def run(self):
        client = ModbusSerialClient(method='rtu')
        client.socket = self.__getSerial()
        client.connect()

        while True:
            r = self.queue.get()
            try:
                wiringpi.digitalWrite(ERROR_PIN, wiringpi.LOW)
                print("Dequeued: {0!s}".format(r))
                r.enqueued = False
                r.process(client, self.pubQueue)
            except RegisterDatapoint.DatapointException as e:
                wiringpi.digitalWrite(ERROR_PIN, wiringpi.HIGH)
                print("ERROR when processing '{0}': {1!s}".format(r.label, e))
                if client.socket is None:
                    print("renew socket")
                    client.socket = self.__getSerial()
            finally:
                time.sleep(self.config.interCommDelay)




