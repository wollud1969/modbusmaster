import threading
import paho.mqtt.client as mqtt
from NotificationForwarder import AbstractNotificationReceiver



def mqttOnConnectCallback(client, userdata, flags, rc):
    userdata.onConnect()

def mqttOnMessageCallback(client, userdata, message):
    userdata.onMessage(message.topic, message.payload)

def mqttOnDisconnectCallback(client, userdata, rc):
    userdata.onDisconnect(rc)

class MqttProcessor(threading.Thread, AbstractNotificationReceiver):
    def __init__(self, config, registers, queue):
        super().__init__()
        self.config = config
        self.registers = registers
        self.queue = queue
        self.client = mqtt.Client(userdata=self)
        self.subscriptions = []
        self.topicRegisterMap ={}

    def __processUpdatedRegisters(self, force=False):
        # print("MqttProcessor.__updateSubscriptions")

        subscribeTopics = [ r.subscribeTopic for r in self.registers if r.subscribeTopic]
        # print("Topics: {0!s}".format(subscribeTopics))

        for subscribeTopic in subscribeTopics:
            if (subscribeTopic not in self.subscriptions) or force:
                print("Subscribe to {0}".format(subscribeTopic))
                self.client.subscribe(subscribeTopic)
                self.subscriptions.append(subscribeTopic)

        for subscription in self.subscriptions:
            if (subscription not in subscribeTopics) and not force:
                print("Unsubscribe from {0}".format(subscription))
                self.client.unsubscribe(subscription)
                self.subscriptions.remove(subscription)

        self.topicRegisterMap = { r.subscribeTopic: r for r in self.registers if r.subscribeTopic }

    def receiveNotification(self, arg):
        print("MqttProcessor:registersChanged")
        self.__processUpdatedRegisters()

    def run(self):
        # print("MqttProcessor.run")
        self.client.on_message = mqttOnMessageCallback
        self.client.on_connect = mqttOnConnectCallback
        self.client.on_disconnect = mqttOnDisconnectCallback
        if self.config.mqttLogin and self.config.mqttPassword:
            self.client.username_pw_set(self.config.mqttLogin, self.config.mqttPassword)
        self.client.connect(self.config.mqttBrokerHost, self.config.mqttBrokerPort)
        self.client.loop_forever()

    def onConnect(self):
        # print("MqttProcessor.onConnect")
        self.__processUpdatedRegisters(force=True)

    def onDisconnect(self, rc):
        print("Disconnected from MQTT broker: {0}".format(rc))

    def onMessage(self, topic, payload):
        # print("MqttProcessor.onMessage")
        r = self.topicRegisterMap[topic]
        # print("{0}: {1!s} -> {2!s}".format(topic, payload, r))
        r.setCommand('w')
        r.setValue(payload)
        self.queue.put(r)



