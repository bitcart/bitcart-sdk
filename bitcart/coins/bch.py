from typing import Any

from .btc import BTC


class BCH(BTC):
    coin_name = "BCH"
    friendly_name = "Bitcoin Cash"
    RPC_URL = "http://localhost:5004"
    AMOUNT_FIELD = "amount (BCH)"
    EXPIRATION_KEY = "expiration"

    async def history(self) -> dict:  # pragma: no cover
        return await self.server.history()  # type: ignore

    async def _add_request(self, *args: Any, **kwargs: Any) -> dict:  # pragma: no cover
        return await self.server.addrequest(*args, **kwargs)  # type: ignore

    async def _convert_amounts(self, data: dict) -> dict:  # pragma: no cover
        if not hasattr(self, "_fetched_token") and isinstance(self.xpub, dict):
            contract = self.xpub.get("contract")
            if contract:
                self.symbol = (await self.server.readcontract(contract, "symbol")).upper()
                self._fetched_token = True
                self.amount_field = f"amount ({self.symbol})"
        return await super()._convert_amounts(data)
