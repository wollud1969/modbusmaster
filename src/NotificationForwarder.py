
class AbstractNotificationReceiver(object):
    def receiveNotification(self, arg):
        raise NotImplementedError


class NotificationForwarder(object):
    def __init__(self):
        self.receivers = []

    def register(self, receiver):
        self.receivers.append(receiver)

    def notify(self, arg=None):
        for r in self.receivers:
            r.receiveNotification(arg)
