import asyncio
from collections import UserDict, defaultdict
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional
from urllib.parse import urljoin

from .coins import COINS
from .event_delivery import EventDelivery

if TYPE_CHECKING:
    from .coin import Coin


class CustomDict:
    def __getattr__(self, name: str) -> Any:
        return self.__getitem__(name)


class ExtendedDefaultDict(defaultdict, CustomDict):
    pass


class ExtendedDict(UserDict, CustomDict):
    pass


class APIManager(EventDelivery):
    def __init__(self, wallets: Dict[str, Iterable[str]] = {}):
        super().__init__()
        self.wallets = ExtendedDefaultDict(
            lambda: ExtendedDict(),
            {currency: self.load_wallets(currency, wallets) for currency, wallets in wallets.items()},
        )
        self.sessions = {}
        self.session_url = {}
        for currency in self.wallets:
            coin = next(iter(self.wallets[currency].values()))
            self.sessions[currency] = coin.server.session
            self.session_url[currency] = coin.server.url
        self.event_handlers = {}

    @classmethod
    def load_wallets(cls, currency: str, wallets: Iterable[str]) -> ExtendedDict:
        return ExtendedDict(
            {wallet: cls.load_wallet(currency, wallet) for wallet in wallets} or {"": cls.load_wallet(currency, None)}
        )

    @classmethod
    def load_wallet(cls, currency: str, wallet: str) -> "Coin":
        return COINS[currency](xpub=wallet)

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

    async def _configure_notifications(self, autoconfigure: bool = True) -> None:
        for currency in self.wallets:
            for wallet in self.wallets[currency].values():
                try:
                    if autoconfigure:
                        await wallet.server.configure_notifications("http://localhost:6000")
                except Exception:
                    pass

    async def register_wallets(self, ws):
        pass  # listen on all wallets

    async def start_websocket_for_currency(self, currency):
        async with self.sessions[currency].ws_connect(urljoin(self.session_url[currency], "/ws")) as ws:
            await self.start_websocket_processing(ws)

    async def start_websocket(self):
        tasks = []
        for currency in self.wallets:
            tasks.append(self.start_websocket_for_currency(currency))
        await asyncio.gather(*tasks)

    async def process_updates(
        self, updates: Iterable[dict], currency: Optional[str] = None, wallet: Optional[str] = None
    ) -> None:
        wallet_obj = self.wallets[currency].get(wallet)
        if wallet_obj:
            self._merge_event_handlers(wallet_obj)
            await wallet_obj.process_updates(updates, pass_instance=True)
