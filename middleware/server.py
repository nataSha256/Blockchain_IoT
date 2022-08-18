import socket
import sys
import json
from math import isnan
import sc_setget as sc
import threading
from sc_deploy import sc_deploy
from pathlib import Path

# Connection with iot side
# For local use, uncomment this line and comment out the following one:
HOST, PORT = 'localhost', 4000
#HOST, PORT = socket.gethostbyname('middleware'), 4000

# Connect with ethereum side
# For local use, uncomment this line and comment out the following one:
#HOST_for_ethereum, PORT_for_ethereum = 'localhost', 8545
#HOST_for_ethereum, PORT_for_ethereum = 'ethereum', 8545
#addr_ethereum = 'http://'+ HOST_for_ethereum +':'+ str(PORT_for_ethereum)
# For Ethereum Ropsten testnet comment out all previous lines and uncomment these:
addr_ethereum = "https://ropsten.infura.io/v3/d962a61c87ef416fa4bed926d810d2d3"

# Connection with user side
# For local use, uncomment this line and comment out the following one:
HOST_for_user, PORT_for_user = 'localhost', 4001
#HOST_for_user, PORT_for_user = socket.gethostbyname('middleware'), 4001

CONNECTED_iot = False
CONNECTED_user = False
THRESHOLDS = {}
nonce = 0


def send_transaction(_data, _nonce):
    # Write data to the blockchain
    IoT_contract_params = sc.sc_parameters()
    sc.sc_send_transaction(addr_ethereum, *IoT_contract_params, _nonce, _data)
    


def socket_connect(_HOST, _PORT, _listeners):
    # AF_INET refers to the address-family ipv4. The SOCK_STREAM means connection-oriented TCP protocol.
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # With the help of bind() function binding host and port
        soc.bind((_HOST, _PORT)) 
    except socket.error as message:
        # if any error occurs then with the help of sys.exit() exit from the program
        print('Bind failed. Error Code : ' + str(message[0]) + ' Message ' + message[1])
        sys.exit()

    # With the help of listening () function starts listening
    # Connection with iot has _listeners == 1, thus: 
    # 1 connection is kept waiting if the server is busy and if a 2nd socket tries to connect then the connection is refused.
    soc.listen(_listeners)

    # print if Socket binding operation completed & it started to listen  
    print("Started listening on port %s" %(_PORT))

    return soc


def interaction_with_client(_soc):    
    # Get data
    conn, addr = _soc.accept()
    data_str = conn.recv(1024).decode()

    # Close the connection with the client
    conn.close()   

    return data_str, addr


def user_connect(_HOST_for_user, _PORT_for_user):
    global CONNECTED_user

    soc = socket_connect(_HOST_for_user, _PORT_for_user, 10)    
    while True:
        conn, addr = soc.accept()
        data_str = conn.recv(1024).decode()

        # Initialize the communication with the user if it sended *START*
        if not CONNECTED_user:
            if data_str=='*START*': 
                CONNECTED_user = True
                print('The communication with the user has been initiazed (Port '+ str(_PORT_for_user)+')')  
        # Communication with the user:
        else:    
            if data_str=='*SETTINGS*':
                with open('IoT_abi.json', "r") as f:
                    abi = json.load(f)    
                with open('IoT_address.txt', "r") as f:
                    address = f.read()
                data = json.dumps(abi)
                conn.sendall(bytes(data,encoding="utf-8")) 
                conn.send(address.encode())
                print("Smart contract's abi and address were successfully sent to the user")  
                conn.close()
                continue  
            
            if data_str=='*STOP*':
                CONNECTED_user = False
                print('The communication with the user has been finished (Port '+ str(_PORT_for_user)+')')  
                conn.close()
                continue        
            
            # New thresholds
            
            print(str(_PORT_for_user) + ': Received new thresholds from ' + str(addr), end=": " )          
            data = json.loads(data_str)
            print(data)
            THRESHOLDS[data["param"]] = [data["valueLow"], data["valueHigh"]]
            with open('IoT_thresholds.json', 'w') as f:
                json.dump(THRESHOLDS, f)
            print('Thresholds for iot have been successfully changed per user request')

        conn.close()


# Deploy the smart contract if it hasn't already been done
file_abi, file_address = Path("IoT_abi.json"), Path("IoT_address.txt")
if file_abi.exists() and file_address.exists():
    print('The contract IoT.sol has already been deployed')
else:
    sc_deploy(addr_ethereum)

# Read thresholds:
with open('IoT_thresholds.json', "r") as f:
    THRESHOLDS = json.load(f) 
print('Current thresholds: ', THRESHOLDS)

# Start interaction with user: 
thread = threading.Thread(target=user_connect, args=(HOST_for_user, PORT_for_user,))
thread.start()  


# Start interaction with iot:
soc = socket_connect(HOST, PORT, 1)
while True:
    data_str, addr = interaction_with_client(soc)

    # Initialize the communication with the iot if it sended *START*
    if not CONNECTED_iot:
        if data_str=='*START*': 
            CONNECTED_iot = True
            print('The communication with the iot has been initiazed (Port '+ str(PORT)+')')  
    # Communication with the iot:
    else:    
        if data_str=='*STOP*':
            CONNECTED_iot = False
            print('The communication with the iot has been finished (Port '+ str(PORT)+')')  
            continue        
        
        print(str(PORT) + ': Received data from ' + str(addr), end=": " )          
        data = json.loads(data_str)
        print(data)

        if isnan(data['value']):
            data['value']=0    
        
        # if both filter values are 0, then the filter is disabled
        if THRESHOLDS[data['param']][0]==0 and THRESHOLDS[data['param']][1]==0:
            nonce = sc.nonce_count(addr_ethereum, nonce)
            thread = threading.Thread(target=send_transaction, args=(data,nonce,))
            thread.start()
        else:
             # otherwise compare with filter values
            if data['value']< THRESHOLDS[data['param']][0] or data['value']> THRESHOLDS[data['param']][1]:
                nonce = sc.nonce_count(addr_ethereum, nonce)
                thread = threading.Thread(target=send_transaction, args=(data,nonce,))
                thread.start()

    
        

 
    

    