from web3 import Web3
import json

def sc_parameters():
    with open('IoT_abi.json', "r") as f:
        abi = json.load(f)
    
    with open('IoT_address.txt', "r") as f:
        address = f.read()
    return abi, address


def nonce_count(_addr_ethereum, _nonce): 
    if _nonce==0:
        wallet_address = "0x653E9815Fe30328782f87599efa7917BF082D467"   

        #wallet_address = "0x67bb4829EdB3D860890ba0DA28793c7326c608e8" 

        w3 = Web3(Web3.HTTPProvider(_addr_ethereum)) 
        _nonce = w3.eth.get_transaction_count(wallet_address)
    else:
        _nonce +=1
    return _nonce


def sc_send_transaction(_addr_ethereum, _abi, _cs_address, _nonce, _data):  
    w3 = Web3(Web3.HTTPProvider(_addr_ethereum))      
    IoT_contract = w3.eth.contract(address=_cs_address, abi=_abi)

    wallet_private_key = "83defd12853a684923f944d2e237b019695f9f3e02064816060a1fadb4ffc26c"    

    #wallet_private_key = "3e1280d5df946dda80ae27f58e221ed6f76687120851a148339ba384dcb3d05e" 

    acct = w3.eth.account.privateKeyToAccount(wallet_private_key)
    tx_dict = {
        'gas': 200500,
        'maxFeePerGas': w3.toWei(4.500000012, 'gwei'), 
        'maxPriorityFeePerGas': w3.toWei(4.5, 'gwei'),
        'nonce': _nonce,
        'chainId': 3,
    }
    
    build_tx = IoT_contract.functions.setData(_data['date'], _data['param'], int(_data['value'] * 10000)).build_transaction(tx_dict) 
    signed = acct.sign_transaction(build_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=600) 
    print('Successfully written to the blockchain:', _data)
    



# params = sc_parameters()
# sc_set("https://ropsten.infura.io/v3/32b00f836fea430fa98d37199b71ebeb", params[0], params[1], {'date':'2022-07-22 23:41:41', 'param':'temperature', 'value':2960})