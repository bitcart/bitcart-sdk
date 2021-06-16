from typing import Any

from .btc import BTC
from decimal import Decimal
from ..utils import convert_amount_type


class XRG(BTC):
    coin_name = "XRG"
    friendly_name = "Ergon"
    RPC_URL = "http://localhost:5005"
    AMOUNT_FIELD = "amount (XRG)"

    async def history(self) -> dict:  # pragma: no cover
        return await self.server.history()  # type: ignore

    async def _add_request(self, *args: Any, **kwargs: Any) -> dict:  # pragma: no cover
        return await self.server.addrequest(*args, **kwargs)  # type: ignore

    async def rate(self, currency: str = "USD") -> Decimal:
        """Get Ergon price in selected fiat currency

        It uses the same method as electrum wallet gets exchange rate-via different payment providers

        Examples:

        >>> c.rate()
        9878.527

        >>> c.rate("RUB")
        757108.226

        Args:
            self (BTC): self
            currency (str, optional): Currency to get rate into. Defaults to "USD".

        Returns:
            Decimal: price of 1 bitcoin in selected fiat currency
        """
        rate = await self.server.exchange_rate(currency)
        if rate == 'None':
            return convert_amount_type('1')
        else:
            return convert_amount_type(rate)
