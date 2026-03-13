from .eth import ETH


class XRP(ETH):
    coin_name = "XRP"
    friendly_name = "XRP"
    RPC_URL = "http://localhost:5012"
    is_eth_based = False
