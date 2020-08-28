from .bch import BCH
from .bsty import BSTY
from .btc import BTC
from .gzro import GZRO
from .ltc import LTC

COINS = {"BTC": BTC, "BCH": BCH, "LTC": LTC, "GZRO": GZRO, "BSTY": BSTY}

__all__ = list(COINS.keys()) + ["COINS"]
