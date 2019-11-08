# pylint: disable=import-error, invalid-sequence-index
import asyncio
import inspect
import json
import logging
import sys
import time
import warnings
from decimal import Decimal
from functools import wraps
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Optional,
    SupportsFloat,
    SupportsInt,
    Union,
)

from ..coin import Coin
from ..errors import InvalidEventError, LightningDisabledError

if TYPE_CHECKING:
    import requests

ASYNC = True

webhook_available = True
try:
    if ASYNC:
        from aiohttp import web
    else:
        from flask import Flask, request
except (ModuleNotFoundError, ImportError):
    webhook_available = False


def lightning(f: Callable) -> Callable:
    @wraps(f)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if len(args) > 0:
            obj = args[0]
            if not await obj.get_config("lightning"):
                raise LightningDisabledError("Lightning is disabled in current daemon.")
        return await f(*args, **kwargs)

    return wrapper


class BTC(Coin):
    coin_name = "BTC"
    friendly_name = "Bitcoin"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = ["jsonrpcrequests"]
    RPC_URL = "http://localhost:5000"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"
    ALLOWED_EVENTS = ["new_block", "new_transaction", "new_payment"]

    def __init__(
        self: "BTC",
        rpc_url: Optional[str] = None,
        rpc_user: Optional[str] = None,
        rpc_pass: Optional[str] = None,
        xpub: Optional[str] = None,
        session: Optional["requests.Session"] = None,
    ):
        super().__init__()
        if not xpub:
            warnings.warn("Xpub not provided. Not all functions will be available.")
        self.rpc_url = rpc_url or self.RPC_URL
        self.rpc_user = rpc_user or self.RPC_USER
        self.rpc_pass = rpc_pass or self.RPC_PASS
        self.xpub = xpub
        self.event_handlers: Dict[str, Callable] = {}
        self.server = self.providers["jsonrpcrequests"].RPCProxy(  # type: ignore
            self.rpc_url, self.rpc_user, self.rpc_pass, self.xpub, session=session
        )
        if ASYNC:
            self._configure_webhook = self._configure_webhook_async
            self.handle_webhook = self.handle_webhook_async
            self._start_webhook = self._start_webhook_async
        else:
            self._configure_webhook = self._configure_webhook_sync
            self.handle_webhook = self.handle_webhook_sync  # type: ignore
            self._start_webhook = self._start_webhook_sync

    ### High level interface ###

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
        return {
            "confirmed": data.get("confirmed", 0),
            "unconfirmed": data.get("unconfirmed", 0),
            "unmatured": data.get("unmatured", 0),
            "lightning": data.get("lightning", 0),
        }

    async def addrequest(
        self: "BTC",
        amount: Union[int, float],
        description: str = "",
        expire: Union[int, float] = 15,
    ) -> dict:
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
        return await self.server.add_request(  # type: ignore
            amount=amount, memo=description, expiration=expiration, force=True
        )

    async def getrequest(self: "BTC", address: str) -> dict:
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

    async def history(self: "BTC") -> dict:
        """Get transaction history of wallet

        Example:

        >>> c.history()
        {'summary': {'end_balance': '0.', 'end_date': None, 'from_height': None, 'incoming': '0.00185511',...

        Args:
            self (BTC): self

        Returns:
            dict: dictionary with some data, where key transactions is list of transactions
        """
        return json.loads(await self.server.onchain_history())  # type: ignore

    def add_event_handler(
        self: "BTC", events: Union[Iterable[str], str], func: Callable
    ) -> None:
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

    def on(self: "BTC", events: Union[Iterable[str], str]) -> Callable:
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

    async def process_updates(self: "BTC", updates: Iterable[dict]) -> None:
        for event_info in updates:
            event = event_info.get("event")
            event_info.pop("event")
            if not event or event not in self.ALLOWED_EVENTS:
                raise InvalidEventError(f"Invalid event from server: {event}")
            handler = self.event_handlers.get(event)
            if handler:
                handler = handler(event, **event_info)
                if inspect.isawaitable(handler):
                    await handler  # type: ignore

    async def poll_updates(self: "BTC", timeout: Union[int, float] = 2) -> None:
        await self.server.subscribe(list(self.event_handlers.keys()))
        while True:
            try:
                data = await self.server.get_updates()
            except Exception as err:
                logging.error(err)
                await asyncio.sleep(timeout)
                continue
            await self.process_updates(data)
            await asyncio.sleep(timeout)

    def poll_updates_sync(self: "BTC", timeout: Union[int, float] = 2) -> None:
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
        self.server._loop.run_until_complete(self.poll_updates(timeout))

    async def pay_to(
        self: "BTC",
        address: str,
        amount: float,
        fee: Optional[Union[float, Callable]] = None,
        feerate: Optional[float] = None,
        broadcast: bool = True,
    ) -> Union[dict, str]:
        """Pay to address

        This function creates a transaction, your wallet must have sufficent balance
        and address must exist.

        Examples:

        >>> btc.pay_to("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt", 0.001)
        '608d9af34032868fd2849723a4de9ccd874a51544a7fba879a18c847e37e577b'

        >>> btc.pay_to("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001, feerate=1)
        '23d0aec06f6ea6100ba9c6ce8a1fa5d333a6c1d39a780b5fadc4b2836d71b66f'

        >>> btc.pay_to("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt", 0.001, broadcast=False)
        {'hex': '02000000026.....', 'complete': True, 'final': False, 'name': None, 'csv_delay': 0, 'cltv_expiry': 0}

        Args:
            self (BTC): self
            address (str): address where to send BTC
            amount (float): amount of bitcoins to send
            fee (Optional[Union[float, Callable]], optional): Either a fixed fee, or a callable getting size and default fee as argument and returning fee. Defaults to None.
            feerate (Optional[float], optional): A sat/byte feerate, can't be passed together with fee argument. Defaults to None.
            broadcast (bool, optional): Whether to broadcast transaction to network. Defaults to True.

        Raises:
            ValueError: If address or amount is invalid or in other cases
            TypeError: if you have provided both fee and feerate

        Returns:
            Union[dict, str]: tx hash of ready transaction or raw transaction, depending on broadcast argument.
        """
        if fee and feerate:
            raise TypeError("Can't specify both fee and feerate at the same time")
        fee_arg = fee if not callable(fee) else None
        tx_data = await self.server.payto(address, amount, fee=fee_arg, feerate=feerate)
        if not fee_arg:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = await self.server.get_default_fee(tx_size)
            try:
                resulting_fee = fee(tx_size, default_fee)  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.payto(
                    address, amount, fee=resulting_fee, feerate=feerate
                )
        if broadcast:
            return await self.server.broadcast(tx_data)  # type: ignore
        else:
            return tx_data  # type: ignore

    async def pay_to_many(
        self: "BTC",
        outputs: Iterable[Union[dict, tuple]],
        fee: Optional[Union[float, Callable]] = None,
        feerate: Optional[float] = None,
        broadcast: bool = True,
    ) -> Union[dict, str]:
        """Pay to multiple addresses(batch transaction)

        This function creates a batch transaction, your wallet must have sufficent balance
        and addresses must exist.
        outputs parameter is either an iterable of ``(address, amount)`` tuples(or any iterables) or a dict with two
        keys: address and amount ``{"address": "someaddress", "amount": 0.5}``

        Examples:

        >>> btc.pay_to_many([{"address":"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt","amount":0.001}, {"address":"mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB","amount":0.0001}])
        '60fa120d9f868a7bd03d6bbd1e225923cab0ba7a3a6b961861053c90365ed40a'

        >>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), ("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)])
        'd80f14e20af2ceaa43a8b7e15402d420246d39e235d87874f929977fb0b1cab8'

        >>> btc.pay_to_many((("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001),("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001)), feerate=1)
        '0a6611876e04a6f2742eac02d4fac4c242dda154d85f0d547bbac1a33dbbbe34'

        >>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), ("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)], broadcast=False)
        {'hex': '0200000...', 'complete': True, 'final': False}

        Args:
            self (BTC): self
            outputs (Iterable[Union[dict, tuple]]): An iterable with dictionary or iterable as the item
            fee (Optional[Union[float, Callable]], optional): Either a fixed fee, or a callable getting size and default fee as argument and returning fee. Defaults to None.
            feerate (Optional[float], optional): A sat/byte feerate, can't be passed together with fee argument. Defaults to None.
            broadcast (bool, optional): Whether to broadcast transaction to network. Defaults to True.

        Raises:
            ValueError: If address or amount is invalid or in other cases
            TypeError: if you have provided both fee and feerate

        Returns:
            Union[dict, str]: tx hash of ready transaction or raw transaction, depending on broadcast argument.
        """
        if fee and feerate:
            raise TypeError("Can't specify both fee and feerate at the same time")
        new_outputs = []
        dict_outputs = False
        for output in outputs:
            if isinstance(output, dict):
                dict_outputs = True
                new_outputs.append((output["address"], output["amount"]))
        outputs = new_outputs if dict_outputs else outputs
        fee_arg = fee if not callable(fee) else None
        tx_data = await self.server.paytomany(outputs, fee=fee_arg, feerate=feerate)
        if not fee_arg:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = await self.server.get_default_fee(tx_size)
            try:
                resulting_fee = fee(tx_size, default_fee)  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.paytomany(
                    outputs, fee=resulting_fee, feerate=feerate
                )
        if broadcast:
            return await self.server.broadcast(tx_data)  # type: ignore
        else:
            return tx_data  # type: ignore

    async def rate(
        self: "BTC", currency: str = "USD", accurate: bool = False
    ) -> Union[float, Decimal]:
        """Get bitcoin price in selected fiat currency

        It uses the same method as electrum wallet gets exchange rate-via different payment providers

        Examples:

        >>> c.rate()
        9878.527

        >>> c.rate("RUB")
        757108.226

        Args:
            self (BTC): self
            currency (str, optional): Currency to get rate into. Defaults to "USD".
            accurate (bool, optional): Whether to return values harder to work with(decimals) or not very accurate floats. Defaults to False.

        Returns:
            Union[float, Decimal]: price of 1 bitcoin in selected fiat currency
        """
        rate_str = await self.server.exchange_rate(currency)
        return Decimal(rate_str) if accurate else float(rate_str)

    async def list_fiat(self: "BTC") -> Iterable[str]:
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

    async def set_config(self: "BTC", key: str, value: Any) -> bool:
        """Set config key to specified value

        It sets the config value in electrum's config store, usually
        $HOME/.electrum/config

        You can set any keys and values using this function(as long as JSON serializable),
        and some are used to configure underlying electrum daemon.

        Example:

        >>> c.set_config("x", 5)
        True

        Args:
            self (BTC): self
            key (str): key to set
            value (Any): value to set

        Returns:
            bool: True on success, False otherwise
        """
        return await self.server.setconfig(key, value)  # type: ignore

    async def get_config(self: "BTC", key: str, default: Any = None) -> Any:
        """Get config key

        If the key doesn't exist, default value is returned.
        Keys are stored in electrum's config file, check :meth:`bitcart.coins.btc.BTC.set_config` doc for details.

        Example:

        >>> c.get_config("x")
        5

        Args:
            self (BTC): self
            key (str): key to get
            default (Any, optional): The value to default to when key doesn't exist. Defaults to None.

        Returns:
            Any: value of the key or default value provided
        """
        return await self.server.getconfig(key) or default

    async def validate_key(self: "BTC", key: str) -> bool:
        """Validate whether provided key is valid to restore a wallet
        
        If the key is x/y/z pub/prv or electrum seed at the network daemon is running
        at, then it would be valid(True), else False

        Examples:

        >>> c.validate_key("test")
        False

        >>> c.validate_key("your awesome electrum seed")
        True

        >>> c.validate_key("x/y/z pub/prv here")
        True
        
        Args:
            self (BTC): self
            key (str): key to check
        
        Returns:
            bool: Whether the key is valid or not
        """
        return await self.server.validatekey(key) # type: ignore

    ### Webhooks ###

    def handle_webhook_sync(self: "BTC") -> dict:
        self.process_updates([request.json])
        return {}

    async def handle_webhook_async(
        self: "BTC", request: "web.Request"
    ) -> "web.Response":
        await self.process_updates([await request.json()])
        return web.json_response({})

    def _configure_webhook_async(self) -> None:
        self.webhook_app = web.Application()
        self.webhook_app.router.add_post("/", self.handle_webhook)

    def _configure_webhook_sync(self) -> None:
        self.webhook_app = Flask(__name__)  # type: ignore
        self.webhook_app.add_url_rule(  # type: ignore
            "/", "handle_webhook", self.handle_webhook, methods=["POST"]
        )

    async def configure_webhook(self: "BTC", autoconfigure: bool = True) -> None:
        if not webhook_available:
            raise ValueError(
                "Webhook support not installed. Install it with pip install bitcart[webhook]"
            )
        self._configure_webhook()
        await self.server.subscribe(list(self.event_handlers.keys()))
        if autoconfigure:
            await self.server.configure_notifications("http://localhost:6000")

    def _start_webhook_sync(self: "BTC", port: int = 6000, **kwargs: Any) -> None:
        self.webhook_app.run(port=port, **kwargs)  # type: ignore

    def _start_webhook_async(self: "BTC", port: int = 6000, **kwargs: Any) -> None:
        web.run_app(self.webhook_app, port=port, **kwargs)

    def start_webhook(self: "BTC", port: int = 6000, **kwargs: Any) -> None:
        if not webhook_available:
            raise ValueError(
                "Webhook support not installed. Install it with pip install bitcart[webhook]"
            )
        if ASYNC:
            self.server._loop.run_until_complete(self.configure_webhook())
        else:
            self.configure_webhook()
        self._start_webhook(port=port, **kwargs)

    ### Lightning apis ###

    @lightning
    async def open_channel(self: "BTC", node_id: str, amount: Union[int, float]) -> str:
        """Open lightning channel

        Open channel with node, returns string of format
        txid:output_index

        Args:
            self (BTC): self
            node_id (str): id of node to open channel with
            amount (Union[int, float]): amount to open channel

        Returns:
            str: string of format txid:output_index
        """
        return await self.server.open_channel(node_id, amount)  # type: ignore

    @lightning
    async def addinvoice(
        self: "BTC", amount: Union[int, float], message: Optional[str] = ""
    ) -> str:
        """Create lightning invoice

        Create lightning invoice and return bolt invoice id

        Example:

        >>> a.addinvoice(0.5)
        'lnbc500m1pwnt87fpp5d60sykcjd2swk72t3g0njwmdytfe4fu65fz5v...'

        Args:
            self (BTC): self
            amount (Union[int,float]): invoice amount
            message (Optional[str], optional): Invoice message. Defaults to "".

        Returns:
            str: bolt invoice id
        """
        return await self.server.add_lightning_request(amount, message)  # type: ignore

    @lightning
    async def close_channel(self: "BTC", channel_id: str, force: bool = False) -> str:
        """Close lightning channel

        Close channel by channel_id got from open_channel, returns transaction id

        Args:
            self (BTC): self
            channel_id (str): channel_id from open_channel
            force (bool): Create new address beyond gap limit, if no more addresses are available.

        Returns:
            str: tx_id of closed channel
        """
        return await self.server.close_channel(channel_id, force)  # type: ignore

    @property  # type: ignore
    @lightning
    async def node_id(self) -> str:
        """Get node id

        Electrum's lightning implementation itself is a lightning node,
        that way you can get a super light node, this method returns it's id

        Example:

        >>> a.node_id
        '030ff29580149a366bdddf148713fa808f0f4b934dccd5f7820f3d613e03c86e55'

        Returns:
            str: id of your node
        """
        return await self.server.nodeid()  # type: ignore

    @lightning
    async def lnpay(self, invoice: str) -> bool:
        """Pay lightning invoice

        Returns True on success, False otherwise

        Args:
            invoice (str): invoice to pay

        Returns:
            bool: success or not
        """
        return await self.server.lnpay(invoice)  # type: ignore

    @lightning
    async def connect(self, connection_string: str) -> bool:
        """Connect to lightning node

        connection string must respect format pubkey@ipaddress

        Args:
            connection_string (str): connection string

        Returns:
            bool: True on success, False otherwise
        """
        return await self.server.add_peer(connection_string)  # type: ignore

    @lightning
    async def list_channels(self) -> list:
        """List all channels ever opened

        Possible channel statuses:
        OPENING, OPEN, CLOSED, DISCONNECTED

        Example:

        >>> a.server.list_channels()
        [{'local_htlcs': {'adds': {}, 'locked_in': {}, 'settles': {}, 'fails': {}}, 'remote_htlcs': ...

        Returns:
            list: list of channels
        """
        return await self.server.list_channels()  # type: ignore
