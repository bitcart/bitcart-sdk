from .btc import BTC


class LTC(BTC):
    coin_name = "LTC"
    friendly_name = "Litecoin"
    RPC_URL = "http://localhost:5001"
