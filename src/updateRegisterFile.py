import datetime
import RegisterDatapoint
import pickle



with open('registers.pkl', 'rb') as f:
    datapoints = pickle.load(f)

RegisterDatapoint.checkRegisterList(datapoints, reset=True)

newDatapoints = []
for dp in datapoints:
    ndp = type(dp)()
    for k,v in dp.__dict__.items():
        ndp.__dict__[k] = v
    newDatapoints.append(ndp)

RegisterDatapoint.checkRegisterList(newDatapoints, reset=True)

with open('registers.pkl', 'wb') as f:
    pickle.dump(newDatapoints, f)

    
