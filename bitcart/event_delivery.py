import asyncio
import logging
import time  # noqa: F401: for sync generator
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union

if TYPE_CHECKING:
    from providers.jsonrpcrequests import RPCProxy

ASYNC = True


webhook_available = True
try:
    if ASYNC:
        from aiohttp import web
    else:  # pragma: no cover
        from flask import Flask, request
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    webhook_available = False


class EventDelivery:
    server: "RPCProxy"
    event_handlers: Dict[str, Callable]

    def __init__(self) -> None:
        self.webhook_available = webhook_available
        if ASYNC:
            self._configure_webhook = self._configure_webhook_async
            self.handle_webhook = self.handle_webhook_async
            self._start_webhook = self._start_webhook_async
            self._loop = asyncio.get_event_loop()
            self._loop.set_exception_handler(lambda loop, context: None)
        else:  # pragma: no cover
            self._configure_webhook = self._configure_webhook_sync
            self.handle_webhook = self.handle_webhook_sync  # type: ignore
            self._start_webhook = self._start_webhook_sync

    def handle_webhook_sync(self) -> dict:
        json = request.json
        self.process_updates(json.get("updates", []), json.get("currency", "BTC"), json.get("wallet"))
        return {}

    async def handle_webhook_async(self, request: "web.Request") -> "web.Response":
        try:
            json = await request.json()
        except JSONDecodeError:
            return web.json_response({})
        await self.process_updates(json.get("updates", []), json.get("currency", "BTC"), json.get("wallet"))
        return web.json_response({})

    async def process_updates(
        self, updates: Iterable[dict], currency: Optional[str] = None, wallet: Optional[str] = None
    ) -> None:
        raise NotImplementedError()

    def _configure_webhook_async(self) -> None:
        self.webhook_app = web.Application()
        self.webhook_app.router.add_post("/", self.handle_webhook)

    def _configure_webhook_sync(self) -> None:
        self.webhook_app = Flask(__name__)  # type: ignore
        self.webhook_app.add_url_rule("/", "handle_webhook", self.handle_webhook, methods=["POST"])  # type: ignore

    def check_webhook_support(self) -> None:
        if not webhook_available:
            raise ValueError("Webhook support not installed. Install it with pip install bitcart[webhook]")

    async def _configure_notifications(self, autoconfigure: bool = True) -> None:
        await self.server.subscribe(list(self.event_handlers.keys()))
        if autoconfigure:
            await self.server.configure_notifications("http://localhost:6000")

    async def configure_webhook(self, autoconfigure: bool = True) -> None:
        self.check_webhook_support()
        self._configure_webhook()
        await self._configure_notifications()

    def _start_webhook_sync(self, port: int = 6000, **kwargs: Any) -> None:
        self.webhook_app.run(port=port, **kwargs)  # type: ignore

    def _start_webhook_async(self, port: int = 6000, **kwargs: Any) -> None:
        web.run_app(self.webhook_app, port=port, **kwargs)

    def start_webhook(self, port: int = 6000, **kwargs: Any) -> None:
        self.check_webhook_support()
        if ASYNC:
            self._loop.run_until_complete(self.configure_webhook())
        else:  # pragma: no cover
            self.configure_webhook()
        self._start_webhook(port=port, **kwargs)

    async def poll_updates(self, timeout: Union[int, float] = 2) -> None:  # pragma: no cover
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

    def poll_updates_sync(self, timeout: Union[int, float] = 2) -> None:
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
        self._loop.run_until_complete(self.poll_updates(timeout))

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
