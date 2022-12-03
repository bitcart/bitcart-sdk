import inspect
from decimal import Decimal
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Union

from ..coin import Coin
from ..errors import LightningDisabledError
from ..event_delivery import EventDelivery
from ..logger import logger
from ..providers.jsonrpcrequests import RPCProxy
from ..types import AmountType
from ..utils import bitcoins, call_universal, convert_amount_type, satoshis

if TYPE_CHECKING:
    from aiohttp import ClientSession, ClientWebSocketResponse


def lightning(f: Callable) -> Callable:
    @wraps(f)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if len(args) > 0:
            obj = args[0]
            if not await obj.get_config("lightning"):  # pragma: no cover: can't be changed during tests
                raise LightningDisabledError("Lightning is disabled in current daemon.")
        return await f(*args, **kwargs)

    return wrapper


class BTC(Coin, EventDelivery):
    coin_name = "BTC"
    friendly_name = "Bitcoin"
    RPC_URL = "http://localhost:5000"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"
    ALLOWED_EVENTS = ["new_block", "new_transaction", "new_payment", "verified_tx"]
    BALANCE_ATTRS = ["confirmed", "unconfirmed", "unmatured", "lightning"]
    is_eth_based = False
    additional_xpub_fields: List[str] = []

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        rpc_user: Optional[str] = None,
        rpc_pass: Optional[str] = None,
        xpub: Optional[str] = None,
        proxy: Optional[str] = None,
        session: Optional["ClientSession"] = None,
    ):
        super().__init__()
        self.symbol = self.coin_name
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
        return await self.server.spec

    ### High level interface ###

    async def help(self) -> list:
        """Get help

        Returns a list of all available RPC methods

        Returns:
            list: RPC methods list
        """
        return await self.server.help()  # type: ignore

    async def get_tx(self, tx: str) -> dict:  # pragma: no cover: see tests for explanation
        """Get transaction information

        Given tx hash of transaction, return full information as dictionary

        Example:

        >>> c.get_tx("54604b116b28124e31d2d20bbd4561e6f8398dca4b892080bffc8c87c27762ba")
        {'partial': False, 'version': 2, 'segwit_ser': True, 'inputs': [{'prevout_hash': 'xxxx',...

        Args:
            tx (str): tx_hash

        Returns:
            dict: transaction info
        """
        return await self.server.get_transaction(tx)  # type: ignore

    async def get_address(self, address: str) -> list:  # pragma: no cover
        """Get address history

        This method should return list of transaction informations for specified address

        Example:

        >>> c.get_address("31smpLFzLnza6k8tJbVpxXiatGjiEQDmzc")
        [{'tx_hash': '7854bdf4c4e27276ecc1fb8d666d6799a248f5e81bdd58b16432d1ddd1d4c332', 'height': 581878, 'tx': ...

        Args:
            address (str): address to get transactions for

        Returns:
            list: List of transactions
        """
        out: list = await self.server.getaddresshistory(address)
        for i in out:
            i["tx"] = await self.get_tx(i["tx_hash"])
        return out

    async def balance(self) -> dict:
        """Get balance of wallet

        Example:

        >>> c.balance()
        {"confirmed": 0.00005, "unconfirmed": 0, "unmatured": 0}

        Returns:
            dict: It should return dict of balance statuses
        """
        data = await self.server.getbalance()
        return {attr: convert_amount_type(data.get(attr, 0)) for attr in self.BALANCE_ATTRS}

    async def _add_request(self, *args: Any, **kwargs: Any) -> dict:
        return await self.server.add_request(*args, **kwargs)  # type: ignore

    async def _convert_amounts(self, data: dict) -> dict:
        if data[self.amount_field].lower() != "unknown":
            data[self.amount_field] = convert_amount_type(data[self.amount_field])
        return data

    async def _add_request_base(
        self,
        method: Callable,
        amount: Optional[AmountType] = None,
        description: str = "",
        expire: Union[int, float] = 15,
        extra_kwargs: dict = {},
    ) -> dict:
        expiration = 60 * expire if expire else None
        kwargs = {"amount": amount, "memo": description, "expiration": expiration}
        kwargs.update(extra_kwargs)
        data = await method(**kwargs)
        return await self._convert_amounts(data)

    async def add_request(
        self,
        amount: Optional[AmountType] = None,
        description: str = "",
        expire: Union[int, float] = 15,
    ) -> dict:
        """Add invoice

        Create an invoice and request amount in BTC, it will expire by parameter provided.
        If expire is None, it will last forever.

        Example:

        >>> c.add_request(0.5, "My invoice", 20)
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': 'xxx',...

        Args:
            self (BTC): self
            amount (Optional[AmountType]): amount to open invoice. Defaults to None.
            description (str, optional): Description of invoice. Defaults to "".
            expire (Union[int, float], optional): The time invoice will expire in. In minutes. Defaults to 15.

        Returns:
            dict: Invoice data
        """
        return await self._add_request_base(self._add_request, amount, description, expire, extra_kwargs={"force": True})

    async def get_request(self, address: str) -> dict:
        """Get invoice info

        Get invoice information by address got from add_request

        Example:

        >>> c.get_request("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ")
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': '1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ',...

        Args:
            self (BTC): self
            address (str): address of invoice

        Returns:
            dict: Invoice data
        """
        data = await self.server.get_request(address)
        return await self._convert_amounts(data)

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
        return await self.server.onchain_history()  # type: ignore

    async def _register_wallets(self, ws: "ClientWebSocketResponse") -> None:
        await ws.send_json({"xpub": self.xpub})

    async def process_updates(self, updates: Iterable[dict], *args: Any, pass_instance: bool = False, **kwargs: Any) -> None:
        if not isinstance(updates, list):
            logger.debug(f"Invalid updates passed: {updates}")
            return
        for event_info in updates:
            if not isinstance(event_info, dict):
                logger.debug(f"{event_info} is not a dict")
                continue
            event = event_info.pop("event", None)
            if not event or event not in self.ALLOWED_EVENTS:
                logger.error(f"Invalid event from server: {event}")
                continue
            handler = self.event_handlers.get(event)
            if handler:
                handler_keys = inspect.signature(handler).parameters.keys()
                args = (event,)
                if pass_instance:
                    args = (self,) + args
                for arg in event_info.copy():
                    if arg not in handler_keys:
                        event_info.pop(arg)
                await call_universal(handler, *args, **event_info)

    async def pay_to(
        self,
        address: str,
        amount: AmountType,
        fee: Optional[Union[AmountType, Callable]] = None,
        feerate: Optional[AmountType] = None,
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
            amount (AmountType): amount of bitcoins to send
            fee (Optional[Union[AmountType, Callable]], optional): Either a fixed fee, or a callable getting size and
                default fee as argument and returning fee. Defaults to None.
            feerate (Optional[AmountType], optional): A sat/byte feerate, can't be passed together with fee argument.
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
            address, amount, fee=fee_arg, feerate=feerate, addtransaction=broadcast and not is_callable
        )
        if is_callable:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = satoshis(await self.server.get_default_fee(tx_size))
            try:
                resulting_fee: Optional[str] = str(bitcoins(fee(tx_size, default_fee)))  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.payto(
                    address, amount, fee=resulting_fee, feerate=feerate, addtransaction=broadcast
                )
            elif broadcast:  # use existing tx_data
                await self.server.addtransaction(tx_data)
        if broadcast:
            return await self.server.broadcast(tx_data)  # type: ignore
        else:
            return tx_data  # type: ignore

    async def pay_to_many(
        self,
        outputs: Iterable[Union[dict, tuple]],
        fee: Optional[Union[AmountType, Callable]] = None,
        feerate: Optional[AmountType] = None,
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
            fee (Optional[Union[AmountType, Callable]], optional): Either a fixed fee, or a callable getting size and
                default fee as argument and returning fee. Defaults to None.
            feerate (Optional[AmountType], optional): A sat/byte feerate, can't be passed together with fee argument.
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
            outputs, fee=fee_arg, feerate=feerate, addtransaction=broadcast and not is_callable
        )
        if is_callable:
            tx_size = await self.server.get_tx_size(tx_data)
            default_fee = satoshis(await self.server.get_default_fee(tx_size))
            try:
                resulting_fee: Optional[str] = str(bitcoins(fee(tx_size, default_fee)))  # type: ignore
            except Exception:
                resulting_fee = None
            if resulting_fee:
                tx_data = await self.server.paytomany(outputs, fee=resulting_fee, feerate=feerate, addtransaction=broadcast)
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
        return convert_amount_type(await self.server.exchange_rate(currency))

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

    async def validate_key(self, key: str, *args: Any, **kwargs: Any) -> bool:
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
        return await self.server.validatekey(key, *args, **kwargs)  # type: ignore

    ### Lightning apis ###

    @lightning
    async def open_channel(self, node_id: str, amount: AmountType) -> str:
        """Open lightning channel

        Open channel with node, returns string of format
        txid:output_index

        Args:
            self (BTC): self
            node_id (str): id of node to open channel with
            amount (AmountType): amount to open channel

        Returns:
            str: string of format txid:output_index
        """
        return await self.server.open_channel(node_id, amount)  # type: ignore

    @lightning
    async def add_invoice(
        self,
        amount: AmountType,
        description: str = "",
        expire: Union[int, float] = 15,
    ) -> dict:
        """Create a lightning invoice

        Create a lightning invoice and return invoice data with bolt invoice id
        All parameters are the same as in add_request

        Example:

        >>> a.add_invoice(0.5, "My invoice", 20)
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'invoice': 'lnbc500m',...

        Args:
            self (BTC): self
            amount (AmountType): amount to open invoice
            description (str, optional): Description of invoice. Defaults to "".
            expire (Union[int, float], optional): The time invoice will expire in. In minutes. Defaults to 15.

        Returns:
            dict: Invoice data
        """
        return await self.add_request(amount, description, expire)

    @lightning
    async def close_channel(self, channel_id: str, force: bool = False) -> str:
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

    @property
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
    async def list_peers(self, gossip: bool = False) -> list:
        """Get a list of lightning peers

        Args:
            gossip (bool, optional): Whether to return peers of a gossip (one per node) or of a wallet. Defaults to False.

        Returns:
            list: list of lightning peers
        """
        return await self.server.list_peers(gossip=gossip)  # type: ignore

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

    @lightning
    async def get_invoice(self, rhash: str) -> dict:
        """Get lightning invoice info

        Get lightning invoice information by rhash got from add_invoice

        Example:

        >>> c.get_invoice("e34d7fb4cda66e0760fc193496c302055d0fd960cfd982432355c8bfeecd5f33")
        {'is_lightning': True, 'amount_BTC': Decimal('0.5'), 'timestamp': 1619273042, 'expiration': 900, ...

        Args:
            rhash (str): invoice rhash

        Returns:
            dict: invoice data
        """
        data = await self.server.get_invoice(rhash)
        return await self._convert_amounts(data)
