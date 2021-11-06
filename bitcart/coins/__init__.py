from .bch import BCH
from .bsty import BSTY
from .btc import BTC
from .ltc import LTC
from .xrg import XRG

COINS = {"BTC": BTC, "BCH": BCH, "LTC": LTC, "BSTY": BSTY, "XRG": XRG}

__all__ = list(COINS.keys()) + ["COINS"]
