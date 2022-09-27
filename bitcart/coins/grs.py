from .btc import BTC


class GRS(BTC):
    coin_name = "GRS"
    friendly_name = "Groestlcoin"
    RPC_URL = "http://localhost:5010"
