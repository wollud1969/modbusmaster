import datetime
import RegisterDatapoint
import pickle
import json


with open('registers.pkl', 'rb') as f:
    datapoints = pickle.load(f)

newDatapoints = []
for dp in datapoints:
    ndp = type(dp)()
    for k, v in dp.__dict__.items():
        if k != 'logger':
            ndp.__dict__[k] = v
    newDatapoints.append(ndp)

js = json.dumps(newDatapoints, cls=RegisterDatapoint.JsonifyEncoder, sort_keys=True, indent=4)
print(js)

RegisterDatapoint.saveRegisterList(newDatapoints, 'registers.json')
