from .eth import ETH


class SUI(ETH):
    coin_name = "SUI"
    xpub_name = "Address"
    friendly_name = "Sui"
    RPC_URL = "http://localhost:5012"
    is_eth_based = False
