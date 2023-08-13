#!/usr/bin/env python3
# A command line utility returning balance of a wallet by it's x/y/z pub/prv or electrum seed
import sys

from bitcart import BTC
from bitcart.errors import ConnectionFailedError, RequestError

if len(sys.argv) != 2:
    print("Usage: ./getbalance xpub")
    sys.exit(1)
xpub = sys.argv[1]
# bitcart-related code
btc = BTC(xpub=xpub)
try:
    balance = btc.balance()
    print(f"Onchain balance: {balance['confirmed']}\nOffchain balance: {balance['lightning']}")
except (RequestError, ConnectionFailedError):
    print("Bad wallet provided, or daemon not running.")
