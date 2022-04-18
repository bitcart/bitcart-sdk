from .bch import BCH
from .bnb import BNB
from .bsty import BSTY
from .btc import BTC
from .eth import ETH
from .ltc import LTC
from .sbch import SBCH
from .xrg import XRG

COINS = {"BTC": BTC, "BCH": BCH, "ETH": ETH, "BNB": BNB, "SBCH": SBCH, "LTC": LTC, "BSTY": BSTY, "XRG": XRG}

__all__ = list(COINS.keys()) + ["COINS"]
