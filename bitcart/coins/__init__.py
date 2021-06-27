from .bch import BCH
from .bsty import BSTY
from .btc import BTC
from .gzro import GZRO
from .ltc import LTC
from .xrg import XRG

COINS = {"BTC": BTC, "BCH": BCH, "LTC": LTC, "GZRO": GZRO, "BSTY": BSTY, "XRG": XRG}

__all__ = list(COINS.keys()) + ["COINS"]
