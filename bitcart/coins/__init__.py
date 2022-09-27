from .bch import BCH
from .bnb import BNB
from .bsty import BSTY
from .btc import BTC
from .eth import ETH
from .grs import GRS
from .ltc import LTC
from .matic import MATIC
from .sbch import SBCH
from .trx import TRX
from .xrg import XRG

COINS = {
    "BTC": BTC,
    "BCH": BCH,
    "ETH": ETH,
    "BNB": BNB,
    "SBCH": SBCH,
    "LTC": LTC,
    "MATIC": MATIC,
    "BSTY": BSTY,
    "TRX": TRX,
    "XRG": XRG,
    "GRS": GRS,
}

__all__ = list(COINS.keys()) + ["COINS"]
