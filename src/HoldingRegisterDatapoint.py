from AbstractModbusDatapoint import AbstractModbusDatapoint


class HoldingRegisterDatapoint(AbstractModbusDatapoint):
    def __init__(self, label, unit, address, count, scanRate, publishTopic, subscribeTopic, feedbackTopic):
        super().__init__(label, unit, address, count, scanRate)
        self.publishTopic = publishTopic
        self.subscribeTopic = subscribeTopic
        self.feedbackTopic = feedbackTopic
        self.writeRequestValue = None
        self.lastContact = None
        self.type = 'read holding register'

    def __str__(self):
        return "[{0!s}, {1} {2} {3}".format(super().__str__(), self.publishTopic, self.subscribeTopic, self.feedbackTopic)

    def process(self):
        successFull = False
        giveUp = False
        if self.writeRequestValue:
            # perform write operation
            if successFull:
                # give feedback
                self.writeRequestValue = None
            else:
                # retries handling
                if giveUp:
                    # give negative feedback
                    self.writeRequestValue = None
        else:
            # perform read operation
            if successFull:
                self.lastContact = datetime.datetime.now()
                # publish value
            else:
                # retries handling
                if giveUp:
                    # backoff and availability handling
                    # give negative feedback
                    pass
    
    def onMessage(self, value):
        self.writeRequestValue = value
