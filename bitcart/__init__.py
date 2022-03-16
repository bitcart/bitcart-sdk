from universalasync import wrap

from .coins import BCH, BSTY, BTC, COINS, ETH, LTC, XRG  # noqa: F401
from .errors import errors
from .manager import APIManager
from .providers.jsonrpcrequests import RPCProxy

# Make all types accessible via both sync and async contexts
for coin in COINS.values():
    wrap(coin)
wrap(APIManager)
wrap(RPCProxy)

__all__ = list(COINS.keys()) + ["APIManager", "COINS", "RPCProxy", "errors"]
