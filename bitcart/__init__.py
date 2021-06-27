from . import sync  # noqa: F401: apply magic async/sync conversion
from .coins import BCH, BSTY, BTC, COINS, GZRO, LTC, XRG  # noqa: F401
from .errors import errors
from .manager import APIManager

__all__ = list(COINS.keys()) + ["COINS", "APIManager", "errors"]
