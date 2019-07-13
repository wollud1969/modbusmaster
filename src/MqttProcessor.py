import threading
import paho.mqtt.client as mqtt
from NotificationForwarder import AbstractNotificationReceiver
import logging


class PublishItem(object):
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload

def mqttOnConnectCallback(client, userdata, flags, rc):
    userdata.onConnect()

def mqttOnMessageCallback(client, userdata, message):
    userdata.onMessage(message.topic, message.payload)

def mqttOnDisconnectCallback(client, userdata, rc):
    userdata.onDisconnect(rc)

class MqttProcessor(threading.Thread, AbstractNotificationReceiver):
    def __init__(self, config, registers, queue, pubQueue):
        super().__init__()
        self.config = config
        self.registers = registers
        self.queue = queue
        self.pubQueue = pubQueue
        self.client = mqtt.Client(userdata=self)
        self.subscriptions = []
        self.topicRegisterMap ={}
        self.daemon = True
        self.logger = logging.getLogger('MqttProcessor')

    def __processUpdatedRegisters(self, force=False):
        self.logger.debug("MqttProcessor.__updateSubscriptions")

        subscribeTopics = [ r.subscribeTopic for r in self.registers if r.subscribeTopic]
        self.logger.debug("Topics: {0!s}".format(subscribeTopics))

        for subscribeTopic in subscribeTopics:
            if (subscribeTopic not in self.subscriptions) or force:
                self.logger.debug("Subscribe to {0}".format(subscribeTopic))
                self.client.subscribe(subscribeTopic)
                self.subscriptions.append(subscribeTopic)

        for subscription in self.subscriptions:
            if (subscription not in subscribeTopics) and not force:
                self.logger.debug("Unsubscribe from {0}".format(subscription))
                self.client.unsubscribe(subscription)
                self.subscriptions.remove(subscription)

        self.topicRegisterMap = { r.subscribeTopic: r for r in self.registers if r.subscribeTopic }

    def receiveNotification(self, arg):
        self.logger.info("MqttProcessor:registersChanged")
        self.__processUpdatedRegisters()

    def run(self):
        self.client.on_message = mqttOnMessageCallback
        self.client.on_connect = mqttOnConnectCallback
        self.client.on_disconnect = mqttOnDisconnectCallback
        if self.config.mqttLogin and self.config.mqttPassword:
            self.client.username_pw_set(self.config.mqttLogin, self.config.mqttPassword)
        self.client.connect(self.config.mqttBrokerHost, self.config.mqttBrokerPort)
        self.client.loop_start()

        while True:
            pubItem = self.pubQueue.get()
            if isinstance(pubItem, PublishItem):
                self.client.publish(pubItem.topic, pubItem.payload)
            else:
                self.logger.error("Invalid object in publish queue")


    def onConnect(self):
        # print("MqttProcessor.onConnect")
        self.__processUpdatedRegisters(force=True)

    def onDisconnect(self, rc):
        self.logger.error("Disconnected from MQTT broker: {0}".format(rc))

    def onMessage(self, topic, payload):
        # print("MqttProcessor.onMessage")
        r = self.topicRegisterMap[topic]
        self.logger.debug("{0}: {1!s} -> {2!s}".format(topic, payload, r))
        r.onMessage(payload)
        self.queue.put(r)

