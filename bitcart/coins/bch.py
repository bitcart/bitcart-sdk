from typing import Union

from .btc import BTC
from ..utils import convert_amount_type

ASYNC = True


class BCH(BTC):
    coin_name = "BCH"
    friendly_name = "Bitcoin Cash"
    RPC_URL = "http://localhost:5004"

    async def history(self: "BCH") -> dict:
        return await self.server.history()  # type: ignore

    async def addrequest(
        self: "BCH",
        amount: Union[int, float],
        description: str = "",
        expire: Union[int, float] = 15,
    ) -> dict:
        expiration = 60 * expire if expire else None
        data = await self.server.addrequest(
            amount=amount, memo=description, expiration=expiration, force=True
        )
        data["amount_BCH"] = convert_amount_type(data["amount_BCH"])
        return data  # type: ignore
