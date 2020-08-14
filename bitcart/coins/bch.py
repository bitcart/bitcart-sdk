from typing import Union

from ..utils import convert_amount_type
from .btc import BTC

ASYNC = True


class BCH(BTC):
    coin_name = "BCH"
    friendly_name = "Bitcoin Cash"
    RPC_URL = "http://localhost:5004"
    AMOUNT_FIELD = "amount (BCH)"

    async def history(self: "BCH") -> dict:
        return await self.server.history()  # type: ignore

    async def addrequest(self: "BCH", amount: Union[int, str], description: str = "", expire: Union[int, float] = 15,) -> dict:
        expiration = 60 * expire if expire else None
        data = await self.server.addrequest(amount=amount, memo=description, expiration=expiration, force=True)
        data[self.amount_field] = convert_amount_type(data[self.amount_field])
        return data  # type: ignore
