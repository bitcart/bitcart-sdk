import asyncio
from typing import Any, Callable, Optional

import aiohttp
import jsonrpcclient
from jsonrpcclient.clients.aiohttp_client import AiohttpClient as RPC


class RPCProxy:
    session: aiohttp.ClientSession

    def __init__(
        self,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        xpub: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
        proxy: Optional[str] = None,
        verify: Optional[bool] = True,
    ):
        self.url = url
        self.username = username
        self.password = password
        self.xpub = xpub
        self.proxy = proxy
        self.verify = verify
        self._connector_class = aiohttp.TCPConnector
        self._connector_init = dict(ssl=self.verify)
        self._loop = asyncio.get_event_loop()
        self._loop.set_exception_handler(lambda loop, context: None)
        if session:
            self.sesson = session
        else:
            self.create_session()
        self.rpc = RPC(endpoint=self.url, session=self.session, timeout=5 * 60)

    def init_proxy(self) -> None:
        if self.proxy:
            from aiohttp_socks import ProxyConnector
            from aiohttp_socks.utils import parse_proxy_url

            proxy_type, host, port, username, password = parse_proxy_url(self.proxy)
            self._connector_class = ProxyConnector
            self._connector_init.update(
                proxy_type=proxy_type,
                host=host,
                port=port,
                username=username,
                password=password,
                rdns=True,
            )

    def create_session(self) -> None:
        self.init_proxy()
        self.session = aiohttp.ClientSession(
            connector=self._connector_class(**self._connector_init),  # type: ignore
            loop=self._loop,
            auth=aiohttp.BasicAuth(self.username, self.password),  # type: ignore
        )

    def __getattr__(self, method: str, *args: Any, **kwargs: Any) -> Callable:
        from ..sync import async_to_sync_wraps

        @async_to_sync_wraps
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return (
                    await self.rpc.request(
                        method,
                        validate_against_schema=False,
                        xpub=self.xpub,
                        *args,
                        **kwargs,
                    )
                ).data.result
            except jsonrpcclient.exceptions.ReceivedErrorResponseError as e:
                raise ValueError("Error from server: {}".format(e.response.message))

        return wrapper

    async def _close(self) -> None:
        await self.session.close()  # type: ignore

    def __del__(self) -> None:
        if self._loop.is_running():
            self._loop.create_task(self._close())
