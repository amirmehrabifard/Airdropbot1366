import os
from web3 import Web3
import json

BSC_RPC = "https://bsc-dataseed.binance.org/"

w3 = Web3(Web3.HTTPProvider(BSC_RPC))

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
OWNER_WALLET = os.getenv("OWNER_WALLET")

with open("BJF_abi.json", "r") as f:
    BJF_ABI = json.load(f)

contract_address = Web3.to_checksum_address("0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181")
contract = w3.eth.contract(address=contract_address, abi=BJF_ABI)

def send_tokens(from_address: str, to_address: str, amount: float) -> str:
    amount_wei = int(amount * 10**18)

    nonce = w3.eth.get_transaction_count(OWNER_WALLET)

    txn = contract.functions.transfer(
        Web3.to_checksum_address(to_address),
        amount_wei
    ).build_transaction({
        'chainId': 56,
        'gas': 200000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return w3.to_hex(tx_hash)
