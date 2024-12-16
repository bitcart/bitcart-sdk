import asyncio
from collections.abc import Callable, Iterable
from functools import partial
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bitcart.errors import CurrencyUnsupportedError, NoCurrenciesRegisteredError

from .coins import COINS
from .event_delivery import EventDelivery
from .logger import logger
from .types import ExtendedDefaultDict, ExtendedDict

if TYPE_CHECKING:
    from aiohttp import ClientWebSocketResponse

    from .coin import Coin
    from .providers.jsonrpcrequests import RPCProxy


class APIManager(EventDelivery):
    def __init__(self, wallets: dict[str, Iterable[str]] | None = None, custom_params: dict[str, dict] | None = None):
        if custom_params is None:
            custom_params = {}
        if wallets is None:
            wallets = {}
        super().__init__()
        self.custom_params = custom_params
        self.wallets = ExtendedDefaultDict(
            lambda: ExtendedDict(),
            {currency: self.load_wallets(currency, wallets) for currency, wallets in wallets.items()},
        )
        self.event_handlers = {}

    def load_wallets(self, currency: str, wallets: Iterable[str]) -> ExtendedDict:
        return ExtendedDict({wallet: self.load_wallet(currency, wallet) for wallet in wallets})

    def load_wallet(self, currency: str, wallet: str | None = None) -> "Coin":
        currency = currency.upper()
        if currency not in COINS:
            raise CurrencyUnsupportedError()
        return COINS[currency](xpub=wallet, **self.custom_params.get(currency, {}))

    def add_wallet(self, currency: str, wallet: str) -> None:
        self.wallets[currency][wallet] = self.load_wallet(currency, wallet)

    def add_wallets(self, currency: str, wallets: Iterable[str]) -> None:
        self.wallets[currency].update(self.load_wallets(currency, wallets))

    def __getitem__(self, key: str) -> Any:
        return self.wallets.__getitem__(key)

    def __getattr__(self, key: str) -> Any:
        return self.__getitem__(key)

    def _merge_event_handlers(self, wallet: "Coin") -> None:
        wallet.event_handlers.update(self.event_handlers)

    async def _register_wallets(self, ws: "ClientWebSocketResponse") -> None:
        pass  # listen on all wallets

    def _get_websocket_server(self, currency: str) -> "RPCProxy":
        try:
            coin = next(iter(self.wallets[currency].values()))
        except StopIteration:  # pragma: no cover
            coin = self.load_wallet(currency, None)
        return coin.server  # type: ignore

    async def _start_websocket_for_currency(self, currency: str, reconnect_callback: Callable | None = None) -> None:
        if reconnect_callback:
            reconnect_callback = partial(reconnect_callback, currency)
        server = self._get_websocket_server(currency)
        async with server.session.ws_connect(urljoin(server.url, "/ws")) as ws:
            await self._start_websocket_processing(ws, reconnect_callback=reconnect_callback)

    async def start_websocket_for_currency(
        self,
        currency: str,
        reconnect_callback: Callable | None = None,
        force_connect: bool = False,
        auto_reconnect: bool = True,
    ) -> None:
        await self._websocket_base_loop(
            partial(self._start_websocket_for_currency, currency=currency),
            reconnect_callback=reconnect_callback,
            force_connect=force_connect,
            auto_reconnect=auto_reconnect,
        )

    async def start_websocket(
        self, reconnect_callback: Callable | None = None, force_connect: bool = False, auto_reconnect: bool = True
    ) -> None:
        tasks = []
        for currency in self.wallets:
            tasks.append(
                self.start_websocket_for_currency(
                    currency, reconnect_callback=reconnect_callback, force_connect=force_connect, auto_reconnect=auto_reconnect
                )
            )
        await asyncio.gather(*tasks)
        if not tasks:
            raise NoCurrenciesRegisteredError()

    async def process_updates(self, updates: Iterable[dict], currency: str | None = None, wallet: str | None = None) -> None:
        wallet_obj = self.wallets[currency].get(wallet)
        if not wallet_obj:
            try:
                wallet_obj = self.load_wallet(currency, wallet)  # type: ignore
            except CurrencyUnsupportedError:
                logger.error(f"Received event for unsupported currency: {currency}")
                return
        self._merge_event_handlers(wallet_obj)
        await wallet_obj.process_updates(updates, pass_instance=True)
