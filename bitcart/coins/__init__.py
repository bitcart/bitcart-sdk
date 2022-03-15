from .bch import BCH
from .bsty import BSTY
from .btc import BTC
from .eth import ETH
from .ltc import LTC
from .xrg import XRG

COINS = {"BTC": BTC, "BCH": BCH, "ETH": ETH, "LTC": LTC, "BSTY": BSTY, "XRG": XRG}

__all__ = list(COINS.keys()) + ["COINS"]
