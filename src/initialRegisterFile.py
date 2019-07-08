import datetime
import RegisterDatapoint
import pickle


datapoints = [
    RegisterDatapoint.InputRegisterDatapoint('Temperature', 5, 0x0001, 1, datetime.timedelta(seconds=0.2), 'Pub/Temperature'),
    RegisterDatapoint.InputRegisterDatapoint('Humidity', 5, 0x0002, 1, datetime.timedelta(seconds=0.2), 'Pub/Humidity'),
]


with open('registers.pkl', 'wb') as f:
    pickle.dump(datapoints, f)

