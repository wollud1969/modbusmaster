import datetime
import RegisterDatapoint
import pickle


datapoints = [
    RegisterDatapoint.InputRegisterDatapoint('Temperature', 5, 0x0001, 1, datetime.timedelta(seconds=1.0), 'Pub/Temperature'),
    RegisterDatapoint.InputRegisterDatapoint('Humidity', 5, 0x0002, 1, datetime.timedelta(seconds=1.0), 'Pub/Humidity'),
    RegisterDatapoint.DiscreteInputDatapoint('Switches', 4, 0x0000, 1, datetime.timedelta(seconds=1.0), 'Pub/Switches'),
]


with open('registers.pkl', 'wb') as f:
    pickle.dump(datapoints, f)

