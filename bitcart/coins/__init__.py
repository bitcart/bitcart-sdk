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
from .xmr import XMR
from .xrg import XRG

COINS = {
    "BTC": BTC,
    "BCH": BCH,
    "XMR": XMR,
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
