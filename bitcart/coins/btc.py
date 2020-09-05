import inspect
import json
import warnings
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

from ..coin import Coin
from ..errors import InvalidEventError, LightningDisabledError
from ..event_delivery import EventDelivery
from ..providers.jsonrpcrequests import RPCProxy
from ..utils import bitcoins, convert_amount_type

if TYPE_CHECKING:
    import aiohttp


def lightning(f: Callable) -> Callable:
    @wraps(f)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if len(args) > 0:
            obj = args[0]
            if not await obj.get_config("lightning"):
                raise LightningDisabledError("Lightning is disabled in current daemon.")
        return await f(*args, **kwargs)

    return wrapper


class BTC(Coin, EventDelivery):
    coin_name = "BTC"
    friendly_name = "Bitcoin"
    RPC_URL = "http://localhost:5000"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"
    ALLOWED_EVENTS = ["new_block", "new_transaction", "new_payment"]
    BALANCE_ATTRS = ["confirmed", "unconfirmed", "unmatured", "lightning"]

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_user: Optional[str] = None,
        rpc_pass: Optional[str] = None,
        xpub: Optional[str] = None,
        proxy: Optional[str] = None,
        session: Optional["aiohttp.ClientSession"] = None,
    ):
        super().__init__()
        if not xpub:
            warnings.warn("Xpub not provided. Not all functions will be available.")
        self.rpc_url = rpc_url or self.RPC_URL
        self.rpc_user = rpc_user or self.RPC_USER
        self.rpc_pass = rpc_pass or self.RPC_PASS
        self.xpub = xpub
        self.event_handlers: Dict[str, Callable] = {}
        self.amount_field = getattr(self, "AMOUNT_FIELD", f"amount_{self.coin_name}")
        self.server = RPCProxy(self.rpc_url, self.rpc_user, self.rpc_pass, self.xpub, session=session, proxy=proxy)

    @property
    async def spec(self) -> dict:
        """Returns current daemon's spec

        It contains documentation for all possible exceptions raised

        Example:

        >>> c.spec
        {'version': '0.0.1', 'electrum_map': {...}, 'exceptions': {...}}

        Returns:
            dict: spec
        """
        return await self.server.spec  # type: ignore

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
        return {attr: convert_amount_type(data.get(attr, 0)) for attr in self.BALANCE_ATTRS}

    async def addrequest(
        self,
        amount: Optional[Union[int, str]] = None,
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
            amount (Optional[Union[int, str]]): amount to open invoice. Defaults to None.
            description (str, optional): Description of invoice. Defaults to "".
            expire (Union[int, float], optional): The time invoice will expire in. Defaults to 15.

        Returns:
            dict: Invoice data
        """
        expiration = 60 * expire if expire else None
        data = await self.server.add_request(amount=amount, memo=description, expiration=expiration, force=True)
        data[self.amount_field] = convert_amount_type(data[self.amount_field])
        return data  # type: ignore

    async def getrequest(self, address: str) -> dict:
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
        data = await self.server.getrequest(address)
        data[self.amount_field] = convert_amount_type(data[self.amount_field])
        return data  # type: ignore

    async def history(self) -> dict:
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

    async def process_updates(self, updates: Iterable[dict], *args: Any, pass_instance: bool = False, **kwargs: Any) -> None:
        if not isinstance(updates, list):
            return
        for event_info in updates:
            if not isinstance(event_info, dict):
                continue
            event = event_info.pop("event", None)
            if not event or event not in self.ALLOWED_EVENTS:
                raise InvalidEventError(f"Invalid event from server: {event}")
            handler = self.event_handlers.get(event)
            if handler:
                args = (event,)
                if pass_instance:
                    args = (self,) + args
                try:
                    handler = handler(*args, **event_info)
                    if inspect.isawaitable(handler):
                        await handler  # type: ignore
                except Exception:
                    pass

    async def pay_to(
        self,
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
            fee (Optional[Union[float, Callable]], optional): Either a fixed fee, or a callable getting size and default fee
                as argument and returning fee. Defaults to None.
            feerate (Optional[float], optional): A sat/byte feerate, can't be passed together with fee argument.
                Defaults to None.
            broadcast (bool, optional): Whether to broadcast transaction to network. Defaults to True.

        Raises:
            TypeError: if you have provided both fee and feerate

        Returns:
            Union[dict, str]: tx hash of ready transaction or raw transaction, depending on broadcast argument.
        """
        if fee and feerate:
            raise TypeError("Can't specify both fee and feerate at the same time")
        is_callable = callable(fee)
        fee_arg = fee if not is_callable else None
        tx_data = await self.server.payto(
            address, amount, fee=fee_arg, feerate=feerate, for_broadcast=broadcast and not is_callable
        )
        if is_callable:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = await self.server.get_default_fee(tx_size)
            try:
                resulting_fee: Optional[str] = str(bitcoins(fee(tx_size, default_fee)))  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.payto(address, amount, fee=resulting_fee, feerate=feerate, for_broadcast=broadcast)
            elif broadcast:  # use existing tx_data
                await self.server.addtransaction(tx_data)
        if broadcast:
            return await self.server.broadcast(tx_data)  # type: ignore
        else:
            return tx_data  # type: ignore

    async def pay_to_many(
        self,
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

        >>> btc.pay_to_many([{"address":"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt","amount":0.001}, \
{"address":"mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB","amount":0.0001}])
        '60fa120d9f868a7bd03d6bbd1e225923cab0ba7a3a6b961861053c90365ed40a'

        >>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), ("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)])
        'd80f14e20af2ceaa43a8b7e15402d420246d39e235d87874f929977fb0b1cab8'

        >>> btc.pay_to_many((("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), \
("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001)), feerate=1)
        '0a6611876e04a6f2742eac02d4fac4c242dda154d85f0d547bbac1a33dbbbe34'

        >>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), \
("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)], broadcast=False)
        {'hex': '0200000...', 'complete': True, 'final': False}

        Args:
            self (BTC): self
            outputs (Iterable[Union[dict, tuple]]): An iterable with dictionary or iterable as the item
            fee (Optional[Union[float, Callable]], optional): Either a fixed fee, or a callable getting size and default fee
                as argument and returning fee. Defaults to None.
            feerate (Optional[float], optional): A sat/byte feerate, can't be passed together with fee argument.
                Defaults to None.
            broadcast (bool, optional): Whether to broadcast transaction to network. Defaults to True.

        Raises:
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
        is_callable = callable(fee)
        fee_arg = fee if not is_callable else None
        tx_data = await self.server.paytomany(
            outputs, fee=fee_arg, feerate=feerate, for_broadcast=broadcast and not is_callable
        )
        if is_callable:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = await self.server.get_default_fee(tx_size)
            try:
                resulting_fee: Optional[str] = str(bitcoins(fee(tx_size, default_fee)))  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.paytomany(outputs, fee=resulting_fee, feerate=feerate, for_broadcast=broadcast)
            elif broadcast:  # use existing tx_data
                await self.server.addtransaction(tx_data)
        if broadcast:
            return await self.server.broadcast(tx_data)  # type: ignore
        else:
            return tx_data  # type: ignore

    async def rate(self, currency: str = "USD") -> Decimal:
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

        Returns:
            Decimal: price of 1 bitcoin in selected fiat currency
        """
        rate_str = await self.server.exchange_rate(currency)
        return convert_amount_type(rate_str)

    async def list_fiat(self) -> Iterable[str]:
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

    async def set_config(self, key: str, value: Any) -> bool:
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

    async def get_config(self, key: str, default: Any = None) -> Any:
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

    async def validate_key(self, key: str) -> bool:
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
        return await self.server.validatekey(key)  # type: ignore

    ### Lightning apis ###

    @lightning
    async def open_channel(self, node_id: str, amount: Union[int, str]) -> str:
        """Open lightning channel

        Open channel with node, returns string of format
        txid:output_index

        Args:
            self (BTC): self
            node_id (str): id of node to open channel with
            amount (Union[int, str]): amount to open channel

        Returns:
            str: string of format txid:output_index
        """
        return await self.server.open_channel(node_id, amount)  # type: ignore

    @lightning
    async def addinvoice(self, amount: Union[int, str], message: Optional[str] = "") -> str:
        """Create lightning invoice

        Create lightning invoice and return bolt invoice id

        Example:

        >>> a.addinvoice(0.5)
        'lnbc500m1pwnt87fpp5d60sykcjd2swk72t3g0njwmdytfe4fu65fz5v...'

        Args:
            self (BTC): self
            amount (Union[int, str]): invoice amount
            message (Optional[str], optional): Invoice message. Defaults to "".

        Returns:
            str: bolt invoice id
        """
        return await self.server.add_lightning_request(amount, message)  # type: ignore

    @lightning
    async def close_channel(
        self, channel_id: str, force: bool = False
    ) -> str:  # pragma: no cover # TODO: remove when electrum 4.0.2
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
