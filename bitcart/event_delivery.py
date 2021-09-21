import asyncio
import traceback
from json import JSONDecodeError
from typing import TYPE_CHECKING, Callable, Dict, Iterable, Optional, Union
from urllib.parse import urljoin

from aiohttp import ClientConnectionError, WSMsgType

from .errors import ConnectionFailedError
from .logger import logger
from .utils import call_universal

if TYPE_CHECKING:
    from aiohttp import ClientWebSocketResponse

    from .providers.jsonrpcrequests import RPCProxy


class EventDelivery:
    server: "RPCProxy"
    event_handlers: Dict[str, Callable]

    async def process_updates(
        self, updates: Iterable[dict], currency: Optional[str] = None, wallet: Optional[str] = None
    ) -> None:
        raise NotImplementedError()

    async def _register_wallets(self, ws: "ClientWebSocketResponse") -> None:
        raise NotImplementedError()

    async def _start_websocket_processing(
        self, ws: "ClientWebSocketResponse", reconnect_callback: Optional[Callable] = None
    ) -> None:
        await self._register_wallets(ws)
        if reconnect_callback:
            await call_universal(reconnect_callback)
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = msg.json()
                    await self.process_updates(data.get("updates", []), data.get("currency", "BTC"), data.get("wallet"))
                except JSONDecodeError:
                    pass
            elif msg.type == WSMsgType.CLOSED or msg.type == WSMsgType.ERROR:  # pragma: no cover
                break

    async def _start_websocket_inner(self, reconnect_callback: Optional[Callable] = None) -> None:
        async with self.server.session.ws_connect(urljoin(self.server.url, "/ws")) as ws:
            await self._start_websocket_processing(ws, reconnect_callback=reconnect_callback)

    async def _websocket_base_loop(
        self,
        func: Callable,
        reconnect_callback: Optional[Callable] = None,
        force_connect: bool = False,
        auto_reconnect: bool = True,
    ) -> None:
        first = True
        while True:
            try:
                await func(reconnect_callback=reconnect_callback)
            except ClientConnectionError as e:
                if first and not force_connect:
                    raise ConnectionFailedError() from e
            first = False
            if not auto_reconnect:
                break
            await asyncio.sleep(5)  # wait a bit before re-estabilishing a connection # pragma: no cover

    async def start_websocket(
        self, reconnect_callback: Optional[Callable] = None, force_connect: bool = False, auto_reconnect: bool = True
    ) -> None:
        """Start a websocket connection to daemon

        Args:
            reconnect_callback (Optional[Callable], optional): Callback to be called right after
                each succesful connection. Defaults to None.
            force_connect (bool, optional): Whether to try reconnecting even on first failure (handshake)
                to daemon. Defaults to False.
            auto_reconnect (bool, optional): Whether to enable auto-reconnecting on websocket closing. Defaults to True.
        """
        await self._websocket_base_loop(
            self._start_websocket_inner,
            reconnect_callback=reconnect_callback,
            force_connect=force_connect,
            auto_reconnect=auto_reconnect,
        )

    async def poll_updates(self, timeout: Union[int, float] = 1) -> None:  # pragma: no cover
        """Poll updates

        Poll daemon for new transactions in wallet,
        this will block forever in while True loop checking for new transactions

        Example can be found on main page of docs

        Args:
            self (BTC): self
            timeout (Union[int, float], optional): seconds to wait before requesting transactions again. Defaults to 1.

        Returns:
            None: This function runs forever
        """
        while True:
            try:
                data = await self.server.get_updates()
            except Exception:
                logger.error(f"Error occured during event polling:\n{traceback.format_exc()}")
                await asyncio.sleep(timeout)
                continue
            await self.process_updates(data)
            await asyncio.sleep(timeout)

    def add_event_handler(self, events: Union[Iterable[str], str], func: Callable) -> None:
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

    def on(self, events: Union[Iterable[str], str]) -> Callable:
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
