import datetime
import RegisterDatapoint
import pickle


datapoints = [
    RegisterDatapoint.HoldingRegisterDatapoint('Voltage', 1, 0x2000, 2, datetime.timedelta(seconds=10), 'Pub/Voltage', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Frequency', 1, 0x2020, 2, datetime.timedelta(seconds=10), 'Pub/Frequency', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Current', 1, 0x2060, 2, datetime.timedelta(seconds=10), 'Pub/Current', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Resistance Channel 1', 2, 0x0004, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel1', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Temperature Channel 1', 2, 0x000c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel1', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Resistance Channel 2', 2, 0x0014, 2, datetime.timedelta(seconds=1), 'Pub/ResistanceChannel2', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Temperature Channel 2', 2, 0x001c, 2, datetime.timedelta(seconds=1), 'Pub/TemperatureChannel2', None, None),
    RegisterDatapoint.HoldingRegisterDatapoint('Relay1', 5, 0x0001, 1, None, None, 'Sub/Relay1', 'Feedback/Relay1'),
    RegisterDatapoint.InputRegisterDatapoint('Humidity 1', 6, 0x0001, 1, datetime.timedelta(seconds=1), 'Pub/Humidity1'),
]


with open('registers.pkl', 'wb') as f:
    pickle.dump(datapoints, f)

