#!/usr/bin/env python3
# A command line utility returning tx info by tx hash
import sys
import warnings

from bitcart import BTC
from bitcart.errors import ConnectionFailedError, RequestError

if len(sys.argv) != 2:
    print("Usage: ./gettx txhash")
    sys.exit(1)
tx = sys.argv[1]
# bitcartcc-related code
with warnings.catch_warnings():  # to ignore no xpub passed warning
    warnings.simplefilter("ignore")
    btc = BTC()
try:
    print(btc.get_tx(tx))
except (RequestError, ConnectionFailedError):
    print("Bad tx hash provided, or daemon not running.")
