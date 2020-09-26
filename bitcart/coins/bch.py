from typing import Any

from .btc import BTC


class BCH(BTC):
    coin_name = "BCH"
    friendly_name = "Bitcoin Cash"
    RPC_URL = "http://localhost:5004"
    AMOUNT_FIELD = "amount (BCH)"

    async def history(self) -> dict:  # pragma: no cover
        return await self.server.history()  # type: ignore

    async def _add_request(self, *args: Any, **kwargs: Any) -> dict:  # pragma: no cover
        return await self.server.addrequest(*args, **kwargs)  # type: ignore
