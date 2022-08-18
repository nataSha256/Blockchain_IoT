from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://ropsten.infura.io/v3/d962a61c87ef416fa4bed926d810d2d3"))

tx = w3.eth.get_transaction('0x4a66fe31f3fcc4b1bf0e59053b0aadca8aa11e5e8fdfe7611aa75ac284bc7fab')

with open('IoT_abi.json', "r") as f:
    abi = json.load(f)
IoT_contract = w3.eth.contract(address=tx["to"], abi=abi)

func_obj, func_params = IoT_contract.decode_function_input(tx["input"])

print(func_obj)
print(func_params)