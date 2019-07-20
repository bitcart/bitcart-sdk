# pylint: disable=import-error, invalid-sequence-index
import sys
import time
import logging
from typing import Optional, Iterable, Union, Dict, SupportsInt, SupportsFloat, Callable
from types import ModuleType
from .btc import BTC


class LN(BTC):
    coin_name = "LN"
    friendly_name = "Bitcoin(Lightning)"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = [
        "jsonrpcrequests"]
    RPC_URL = "http://localhost:5001"