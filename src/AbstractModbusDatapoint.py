
class AbstractModbusDatapoint(object):
    def __init__(self, label, unit, address, count, scanRate):
        self.label = label
        self.unit = unit
        self.address = address
        self.count = count
        self.scanRate = scanRate
        self.type = 'abstract data point'
        self.command = None
        self.value = None
        self.enqueued = False
        if self.scanRate:
            self.priority = 1
        else:
            self.priority = 0

    def __str__(self):
        return "{0}, {1}: {2} {3} {4} {5} {6}".format(self.type, self.label, self.unit, self.address, self.count, self.command, self.value)
    
    def setCommand(self, cmd):
        self.command = cmd
    
    def setValue(self, value):
        self.value = value

