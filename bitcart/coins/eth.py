from ..errors import NotImplementedError
from .btc import BTC


class ETH(BTC):
    coin_name = "ETH"
    friendly_name = "Ethereum"
    RPC_URL = "http://localhost:5002"
    ALLOWED_EVENTS = ["new_block", "new_transaction", "new_payment"]

    async def history(self) -> dict:  # pragma: no cover
        return await self.server.history()

    async def get_address(self, *args, **kwargs):
        raise NotImplementedError("Full address history lookup not implemented for ETH to remain lightweight")

    async def pay_to_many(self, *args, **kwargs):
        raise NotImplementedError("Pay to many not available in ETH directly")
