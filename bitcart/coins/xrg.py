from .bch import BCH


class XRG(BCH):
    coin_name = "XRG"
    friendly_name = "Ergon"
    RPC_URL = "http://localhost:5005"
    AMOUNT_FIELD = "amount (XRG)"
