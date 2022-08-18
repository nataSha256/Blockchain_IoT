from web3 import Web3
from solcx import compile_source
import json

def sc_deploy(_addr):
    # Solidity source code
    with open('IoT.sol', "r") as f:
        contract_source_code = f.read()

    compiled_sol = compile_source(contract_source_code, output_values=['abi', 'bin'])
    print('The contract IoT.sol has been successfully compiled')

    # retrieve the contract interface
    contract_id, contract_interface = compiled_sol.popitem()

    # get bytecode / bin
    bytecode = contract_interface['bin']

    # get abi
    abi = contract_interface['abi']
    with open('IoT_abi.json', 'w') as f:
        json.dump(abi, f)

    # web3.py instance
    w3 = Web3(Web3.HTTPProvider(_addr))

    # set pre-funded account as sender
    #w3.eth.default_account = w3.eth.accounts[0]      ######
    wallet_private_key = "83defd12853a684923f944d2e237b019695f9f3e02064816060a1fadb4ffc26c"
    wallet_address = "0x653E9815Fe30328782f87599efa7917BF082D467"    

    # wallet_private_key = "3e1280d5df946dda80ae27f58e221ed6f76687120851a148339ba384dcb3d05e"
    # wallet_address = "0x67bb4829EdB3D860890ba0DA28793c7326c608e8" 

    nonce = w3.eth.getTransactionCount(wallet_address)
    acct = w3.eth.account.privateKeyToAccount(wallet_private_key)

    IoT_contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Submit the transaction that deploys the contract
    #tx_hash = IoT_contract.constructor().transact()     ######
    construct_tx = IoT_contract.constructor().buildTransaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': 633499,
        'maxFeePerGas': w3.toWei(3.500000012, 'gwei'), 
        'maxPriorityFeePerGas': w3.toWei(3.5, 'gwei'),
        'chainId': 3
        })
    signed = acct.signTransaction(construct_tx)
    tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)

    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print('The contract IoT.sol has been successfully deployed\nReceipt:')
    print(tx_receipt)

    with open('IoT_address.txt', 'w') as f:
        f.write(tx_receipt.contractAddress)
