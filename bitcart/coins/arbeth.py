from .eth import ETH


class ARBETH(ETH):
    coin_name = "ARBETH"
    friendly_name = "Ethereum (Arbitrum)"
    RPC_URL = "http://localhost:5012"
