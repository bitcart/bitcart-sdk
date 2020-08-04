#!/usr/bin/env python3
# A command line utility to send to some address from your wallet
from bitcart import BTC
import sys
import requests

if len(sys.argv) != 4:
    print("Usage: ./donateto xpub address amount")
    sys.exit(1)
xpub = sys.argv[1]
address = sys.argv[2]
try:
    amount = float(sys.argv[3])
except ValueError:
    print("Invalid amount passed")
    sys.exit(1)
# bitcartcc-related code
btc = BTC(xpub=xpub)
try:
    tx_hash = btc.pay_to(address, amount)
    print(f"Success!\nTx hash: {tx_hash}")
except ValueError as e:
    if "Error loading wallet" in str(e):  # TODO: better exceptions
        print("Bad wallet provided")
    else:
        print(e)
except requests.exceptions.ConnectionError:  # TODO: add specific exception for it to be the same in bitcart and bitcart-async
    print("Daemon not running")
