from flask import Flask, request, render_template, flash, redirect
import threading
from web3 import Web3
import json
import time
import socket
from pathlib import Path
from datetime import datetime
import sys

# Connection with middleware side
# For local use, uncomment this line and comment out the following one:
HOST_middleware, PORT_middleware = 'localhost', 4001
#HOST_middleware, PORT_middleware = socket.gethostbyname('middleware'), 4001

# Connect with ethereum side
# For local use, uncomment this line and comment out the following one:
#HOST_ethereum, PORT_ethereum = 'localhost', 8545
# HOST_ethereum, PORT_ethereum = 'ethereum', 8545
#addr_ethereum = 'http://'+ HOST_ethereum +':'+ str(PORT_ethereum)
# For Ethereum Ropsten testnet comment out all previous lines and uncomment these:
addr_ethereum = "https://ropsten.infura.io/v3/d962a61c87ef416fa4bed926d810d2d3"


# Set the number of recent blocks that will be checked for the presence of the required data 
if len(sys.argv)==2:
    blocks_count = int(sys.argv[1])
else: 
    blocks_count = 100  
print('The number of last blocks read from the blockchain is', blocks_count)


newdata = False
newdata_time = []
newdata_values = []


app = Flask(__name__)   

@app.route('/', methods=['GET','POST'])                      
def index():
    if request.method == 'POST':
        sensoList = request.form.get("sensoList")
        inputLow = request.form.get("inputLow")
        inputHigh = request.form.get("inputHigh")

        if len(inputLow)==0 or len(inputHigh)==0:
            flash('Please enter both thresholds','warning')
            return redirect(request.url)
        
        if float(inputLow) > float(inputHigh):
            flash('The lower threshold must not be greater than the upper threshold!','warning')
            return redirect(request.url)

        middleware_thresholds_send(sensoList, float(inputLow), float(inputHigh))

        flash('Threshold values have been applied!','success')
        return redirect(request.url)

    return render_template('index.html')

@app.route('/data')
def data(): 
    return get_data()

@app.route('/newdata')
def new_data(): 
    global newdata
    if newdata:
        v = {'time': newdata_time[-1], 'amount': len(newdata_values[-1]), 'page': len(newdata_time)-1}
        newdata = False
    else:
        v = {}
    return v

@app.route('/notification/<int:notif>')
def profile(notif):
    return render_template('notifications.html', time = newdata_time[notif], data = newdata_values[notif])



# Interaction with the middleware:

def soc_connect(_HOST, _PORT):
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect((_HOST, _PORT)) 
    return soc

def soc_close(_soc):
    # Finish communication with the server
    #soc = soc_connect(_HOST, _PORT)
    _soc.send('*STOP*'.encode())
    _soc.close() 

def middleware_first_connect():
    global HOST_middleware, PORT_middleware

    # Initialize communication with the server    
    soc = soc_connect(HOST_middleware, PORT_middleware)
    soc.send('*START*'.encode())

    soc = soc_connect(HOST_middleware, PORT_middleware)
    soc.send('*SETTINGS*'.encode())

    for i in range(2):
        # Get data
        #soc = soc_connect(HOST_middleware, PORT_middleware)
        data_str = soc.recv(2048).decode()
        print(str(PORT_middleware) + ': Received a file from the middleware')          

        if i == 0:
            data = json.loads(data_str)
            with open('IoT_abi.json', 'w') as f:
                json.dump(data, f)
        else:
            with open('IoT_address.txt', 'w') as f:
                f.write(data_str)

    print("Abi and address of the smart contract are obtained from the middleware")
    
    # Close communication with the server
    soc = soc_connect(HOST_middleware, PORT_middleware)
    soc_close(soc)  
    new_data()


def middleware_thresholds_send(_sensoList, _inputLow, _inputHigh):
    global HOST_middleware, PORT_middleware
    
    soc = soc_connect(HOST_middleware, PORT_middleware)
    soc.send('*START*'.encode())    

    soc = soc_connect(HOST_middleware, PORT_middleware)
    m ={
            "param": _sensoList, 
            "valueLow": _inputLow,
            "valueHigh": _inputHigh 
        }
    data = json.dumps(m)
    soc.sendall(bytes(data,encoding="utf-8"))

    print("New thresholds have been successfully sent to middleware")
    
    # Close communication with the server
    soc = soc_connect(HOST_middleware, PORT_middleware)
    soc_close(soc)  



# Interaction with the ethereum:

def ethereum_connect():
    global addr_ethereum
    file_abi, file_address = Path("IoT_abi.json"), Path("IoT_address.txt")
    while True:
        if (not file_abi.exists()) or (not file_address.exists()):
            # wait, files have not been copied from the middleware yet
            print("Waiting for abi and address of the smart contract from the middleware...")
            time.sleep(15)
        else:
            break

    with open('IoT_abi.json', "r") as f:
        abi = json.load(f)        
    with open('IoT_address.txt', "r") as f:
        address = f.read()
    
    w3 = Web3(Web3.HTTPProvider(addr_ethereum))
    # w3.eth.default_account = w3.eth.accounts[0]
    IoT_contract = w3.eth.contract(address=address, abi=abi)

    return w3, IoT_contract, address

def handle_data(_w3, _IoT_contract, _data):
    tx_receipt = _w3.eth.get_transaction_receipt(_data['transactionHash'])
    logs = _IoT_contract.events.IotData().processReceipt(tx_receipt)
    data_dict = logs[0]['args']
    #print("Block: ", logs[0]['blockNumber'])
    return [data_dict['d'], data_dict['p'], data_dict['v']]


def get_data():
    global blocks_count

    # data from blockchain
    bl_data = {"data": []}
    
    w3, IoT_contract, address = ethereum_connect()    

    # Reading data: checking latest blocks
    block_latest = w3.eth.get_block('latest')['number']
    if (block_latest - blocks_count + 1) <= 1:
        block_from = 1
    else:
        block_from = block_latest - blocks_count + 1

    block_filter_old = w3.eth.filter({'fromBlock': block_from, 
                                      'address':address})
    print("Reading old data (" + str(blocks_count) + " latest blocks)...")

    for event in block_filter_old.get_all_entries():
        bl_data['data'].append(handle_data(w3, IoT_contract, event))

    return bl_data


def date_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def new_data():
    global newdata, newdata_time, newdata_values

    w3, IoT_contract, address = ethereum_connect()
    block_filter_new = w3.eth.filter({'fromBlock':'latest', 'address':address})

    while True:
        bl_data = []
        new_entries = block_filter_new.get_new_entries()
        if len(new_entries)>0:
            for entry in new_entries:
                bl_data.append(handle_data(w3, IoT_contract, entry))
            
            newdata_time.append(date_str())
            newdata_values.append(bl_data)
            newdata = True
            print('New data items ('+ str(len(new_entries)) +') in the blockchain') 
        time.sleep(20)

# Receive (if necessary) abi and smart contract address from the middleware - and then listen - new_data()
file_abi, file_address = Path("IoT_abi.json"), Path("IoT_address.txt")
if file_abi.exists() and file_address.exists():
    thread = threading.Thread(target = new_data, args=())
else: 
    thread = threading.Thread(target = middleware_first_connect, args=())
thread.start()


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    # app.run(debug = False, host="0.0.0.0")
    app.run(debug = False)
   