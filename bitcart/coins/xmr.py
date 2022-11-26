from .eth import ETH


class XMR(ETH):
    coin_name = "XMR"
    friendly_name = "Monero"
    RPC_URL = "http://localhost:5011"
    additional_xpub_fields = ["address"]
