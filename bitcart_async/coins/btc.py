# pylint: disable=import-error, invalid-sequence-index
import sys
import logging
from typing import Optional, Iterable, Union, Dict, SupportsInt, SupportsFloat, Callable, TYPE_CHECKING
from types import ModuleType
import warnings
import asyncio
import inspect
from ..coin import Coin

if TYPE_CHECKING:
    import requests


class InvalidEventError(Exception):
    pass


class BTC(Coin):
    coin_name = "BTC"
    friendly_name = "Bitcoin"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = [
        "jsonrpcrequests"]
    RPC_URL = "http://localhost:5000"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"
    ALLOWED_EVENTS = ["new_block", "new_transaction"]

    def __init__(
            self: "BTC",
            rpc_url: Optional[str] = None,
            rpc_user: Optional[str] = None,
            rpc_pass: Optional[str] = None,
            xpub: Optional[str] = None,
            session: Optional['requests.Session'] = None):
        super().__init__()
        if not xpub:
            warnings.warn(
                "Xpub not provided. Not all functions will be available.")
        self.rpc_url = rpc_url or self.RPC_URL
        self.rpc_user = rpc_user or self.RPC_USER
        self.rpc_pass = rpc_pass or self.RPC_PASS
        self.xpub = xpub
        self.event_handlers: Dict[str, Callable] = {}
        self.server = self.providers["jsonrpcrequests"].RPCProxy(  # type: ignore
            self.rpc_url, self.rpc_user, self.rpc_pass, self.xpub, session=session)

    async def help(self) -> list:
        return await self.server.help()  # type: ignore

    async def get_tx(self, tx: str) -> dict:
        return await self.server.get_transaction(tx)  # type: ignore

    async def get_address(self, address: str) -> list:
        out: list = await self.server.getaddresshistory(address)
        for i in out:
            i["tx"] = await self.get_tx(i["tx_hash"])
        return out

    async def balance(self) -> dict:
        data = await self.server.getbalance()
        return {"confirmed": data.get("confirmed", 0),
                "unconfirmed": data.get("unconfirmed", 0),
                "unmatured": data.get("unmatured", 0)}

    async def addrequest(self: 'BTC',
                         amount: Union[int, float],
                         description: str = "",
                         expire: Union[int, float] = 15) -> dict:
        """Add invoice

        Create an invoice and request amount in BTC, it will expire by parameter provided.
        If expire is None, it will last forever.

        Example:

        >>> c.addrequest(0.5, "My invoice", 20)
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': 'xxx',...

        Args:
            self (BTC): self
            amount (Union[int, float]): amount to open invoice
            description (str, optional): Description of invoice. Defaults to "".
            expire (Union[int, float], optional): The time invoice will expire in. Defaults to 15.

        Returns:
            dict: Invoice data
        """
        expiration = 60 * expire if expire else None
        return await self.server.addrequest(  # type: ignore
            amount=amount,
            memo=description,
            expiration=expiration,
            force=True)

    async def getrequest(self: 'BTC', address: str) -> dict:
        """Get invoice info

        Get invoice information by address got from addrequest

        Example:

        >>> c.getrequest("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ")
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': '1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ',...

        Args:
            self (BTC): self
            address (str): address of invoice

        Returns:
            dict: Invoice data
        """
        return await self.server.getrequest(address)  # type: ignore

    async def history(self: 'BTC') -> dict:
        """Get transaction history of wallet

        Example:

        >>> c.history()
        {'summary': {'end_balance': '0.', 'end_date': None, 'from_height': None, 'incoming': '0.00185511',...

        Args:
            self (BTC): self

        Returns:
            dict: dictionary with some data, where key transactions is list of transactions
        """
        return await self.server.history()  # type: ignore

    def add_event_handler(
            self: 'BTC', events: Union[Iterable[str], str], func: Callable) -> None:
        """Add event handler to handle event(s) provided

        Args:
            self (BTC): self
            events (Union[Iterable[str], str]): event or events
            func (Callable): function to handle those

        Returns:
            None: None
        """
        if isinstance(events, str):
            events = [events]
        for event in events:
            self.event_handlers[event] = func

    def on(self: 'BTC', events: Union[Iterable[str], str]) -> Callable:
        """Register on event

        Register callback function to be run when event is emmited

        All available events are accessable as:

        >>> btc.ALLOWED_EVENTS
        ['new_block', 'new_transaction']

        Function signature must be

        .. code-block:: python

            def handler(event, **kwargs):

        kwargs sent differ from event to event, as for now
        new_block event sends height kwarg as new block height
        new_transaction event sends tx kwarg as tx_hash of new transaction

        Args:
            self (BTC): self
            events (Union[Iterable[str], str]): event name or list of events for function to be run on

        Returns:
            Callable: It is a decorator
        """
        def wrapper(f: Callable) -> Callable:
            self.add_event_handler(events, f)
            return f
        return wrapper

    def poll_updates(self: 'BTC', timeout: Union[int, float] = 2) -> None:
        """Poll updates
        Poll daemon for new transactions in wallet,
        this will block forever in while True loop checking for new transactions
        Example can be found on main page of docs
        Args:
            self (BTC): self
            timeout (Union[int, float], optional): seconds to wait before requesting transactions again. Defaults to 2.
        Raises:
            InvalidEventError: If server sent invalid event name not matching ALLOWED_EVENTS
        Returns:
            None: This function runs forever
        """
        self.server.loop.run_until_complete(self.poll_updates_async(timeout))

    async def poll_updates_async(self: 'BTC', timeout: Union[int, float] = 2) -> None:
        await self.server.subscribe(list(self.event_handlers.keys()))
        while True:
            try:
                data = await self.server.get_updates()
            except Exception as err:
                logging.error(err)
                await asyncio.sleep(timeout)
                continue
            if data:
                for event_info in data:
                    event = event_info.get("event")
                    event_info.pop("event")
                    if not event or event not in self.ALLOWED_EVENTS:
                        raise InvalidEventError(
                            f"Invalid event from server: {event}")
                    handler = self.event_handlers.get(event)
                    if handler:
                        func = handler(event, **event_info)
                        if inspect.isawaitable(func):
                            await func

            await asyncio.sleep(timeout)

    async def pay_to(self: 'BTC', address: str, amount: float) -> str:
        """Pay to address in bitcoins

        This function creates bitcoin transaction, your wallet must have sufficent balance
        and address must exist

        Args:
            self (BTC): self
            address (str): address where to send BTC
            amount (float): amount of bitcoins to send

        Raises:
            ValueError: If address or amount is invalid or in other cases

        Returns:
            str: tx hash of ready transaction
        """
        tx_data = await self.server.payto(address, amount)
        return await self.server.broadcast(tx_data)  # type: ignore

    async def rate(self: 'BTC', currency: str = "USD") -> float:
        """Get bitcoin price in selected fiat currency

        It uses the same method as electrum wallet gets exchange rate-via different payment providers

        Examples:

        >>> c.rate()
        9878.527

        >>> c.rate("RUB")
        757108.226

        Args:
            self (BTC): self
            currency (str, optional): [description]. Defaults to "USD".

        Returns:
            float: price of 1 bitcoin in selected fiat currency
        """
        return await self.server.exchange_rate(currency)  # type: ignore

    async def list_fiat(self: 'BTC') -> Iterable[str]:
        """List of all available fiat currencies to get price for

        This list is list of only valid currencies that could be passed to rate() function

        Example:

        >>> c.list_fiat()
        ['AED', 'ARS', 'AUD', 'BCH', 'BDT', 'BHD', 'BMD', 'BNB', 'BRL', 'BTC', ...]

        Args:
            self (BTC): self

        Returns:
            Iterable[str]: list of available fiat currencies
        """
        return await self.server.list_currencies()  # type: ignore
