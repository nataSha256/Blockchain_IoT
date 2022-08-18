import socket
import json
from datetime import datetime
import pandas as pd
import time
import sys

# Connection with middleware side
# For local use, uncomment this line and comment out the following one:
HOST, PORT = 'localhost', 4000
#HOST, PORT = socket.gethostbyname('middleware'), 4000

# Set the speed of collecting data from sensors
if len(sys.argv)==2:
    speed_sec = int(sys.argv[1])
else: 
    speed_sec = 15
print('The speed of collecting data from sensors is', speed_sec,'seconds')

def soc_connect(h, p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((h, p)) 
    return s

def read_csv():
    data_f = pd.read_csv("apartment2016.csv")
    data_f = data_f.loc[:, ~data_f.columns.isin(['icon', 'summary', 'time'])]
    param_f = list(data_f.columns)
    return data_f, param_f

def date_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  

data, param = read_csv()

i=2
# Initialize the communication with the server
soc = soc_connect(HOST, PORT)
soc.send('*START*'.encode())
soc.close()    

for label, row in data.iterrows():  
    # Collect data from all sensors and send
    print(date_str(),": Collecting data from all sensors and sending to the port", PORT)

    for j in range(len(param)): 
        # connecting to the server
        soc = soc_connect(HOST, PORT)

        m ={
            "date": date_str(), 
            "param": param[j],
            "value": row[j] 
        }
        data = json.dumps(m)
        soc.sendall(bytes(data,encoding="utf-8"))
        time.sleep(0.3)

    # close the connection
    soc.close()        
    print("The connection was closed") 

    if i==9:
        break
    i+=1

    # Waiting between the next sensor poll (submission speed)
    time.sleep(speed_sec)

# Finish the communication with the server
soc = soc_connect(HOST, PORT)
soc.send('*STOP*'.encode())
soc.close() 

    