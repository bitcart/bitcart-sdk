#!/usr/bin/env python3
# A command line utility to send to some address from your wallet
import sys
from decimal import Decimal, InvalidOperation

from bitcart import BTC, errors
from bitcart.errors import ConnectionFailedError

if len(sys.argv) != 4:
    print("Usage: ./donateto xpub address amount")
    sys.exit(1)
xpub = sys.argv[1]
address = sys.argv[2]
try:
    amount = Decimal(sys.argv[3])
except InvalidOperation:
    print("Invalid amount passed")
    sys.exit(1)
# bitcart-related code
btc = BTC(xpub=xpub)
try:
    tx_hash = btc.pay_to(address, amount)
    print(f"Success!\nTx hash: {tx_hash}")
except errors.LoadingWalletError:
    print("Bad wallet provided")
except ConnectionFailedError:
    print("Daemon not running")
except Exception as e:
    print(e)
