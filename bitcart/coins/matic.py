from .eth import ETH


class MATIC(ETH):
    coin_name = "MATIC"
    friendly_name = "Polygon"
    RPC_URL = "http://localhost:5008"
