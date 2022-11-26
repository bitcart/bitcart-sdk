from typing import Any, NoReturn

from ..errors import NotImplementedError
from .btc import BTC


class ETH(BTC):
    coin_name = "ETH"
    friendly_name = "Ethereum"
    RPC_URL = "http://localhost:5002"
    ALLOWED_EVENTS = ["new_block", "new_transaction", "new_payment"]
    is_eth_based = True

    async def history(self) -> dict:  # pragma: no cover
        return await self.server.history()  # type: ignore

    async def get_address(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotImplementedError(f"Full address history lookup not implemented for {self.coin_name} to remain lightweight")

    async def pay_to_many(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise NotImplementedError(f"Pay to many not available in {self.coin_name} directly")

    async def _convert_amounts(self, data: dict) -> dict:  # pragma: no cover
        if not hasattr(self, "_fetched_token") and isinstance(self.xpub, dict):
            contract = self.xpub.get("contract")
            if contract:
                self._fetched_token = True
                self.symbol = (await self.server.readcontract(contract, "symbol")).upper()
                self.amount_field = f"amount_{self.symbol}"
        return await super()._convert_amounts(data)
