import datetime
import RegisterDatapoint
import pickle



with open('registers.pkl', 'rb') as f:
    datapoints = pickle.load(f)

