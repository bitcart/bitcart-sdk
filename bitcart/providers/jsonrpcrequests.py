import asyncio
from typing import Any, Callable, Optional
from urllib.parse import urljoin

import aiohttp
from jsonrpcclient.clients.aiohttp_client import AiohttpClient as RPC
from jsonrpcclient.exceptions import ReceivedErrorResponseError
from jsonrpcclient.requests import Request

from ..errors import ConnectionFailedError, UnknownError, generate_exception
from ..utils import json_encode


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
        self._spec = {"exceptions": {"-32600": {"exc_name": "UnauthorizedError", "docstring": "Unauthorized"}}}
        self._spec_valid = False
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

    def validate_spec(self, spec: Any) -> bool:
        if not isinstance(spec, dict):
            return False
        if not spec.keys() >= {"version", "exceptions"}:
            return False
        if not isinstance(spec["version"], str) or not isinstance(spec["exceptions"], dict):
            return False
        if not all(
            isinstance(code, str) and isinstance(exc, dict) and exc.keys() >= {"exc_name", "docstring"}
            for code, exc in spec["exceptions"].items()
        ):
            return False
        return True

    async def fetch_spec(self) -> Any:
        resp = await self.session.get(urljoin(self.url, "/spec"))
        spec = await resp.json()
        return spec

    @property
    async def spec(self) -> dict:
        if self._spec_valid:
            return self._spec
        try:
            spec = await self.fetch_spec()
            self._spec_valid = self.validate_spec(spec)
            if self._spec_valid:
                self._spec = spec
        except Exception:
            pass
        return self._spec

    def __getattr__(self, method: str, *args: Any, **kwargs: Any) -> Callable:
        from ..sync import async_to_sync_wraps

        @async_to_sync_wraps
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return (
                    await self.rpc.send(
                        json_encode(Request(method, xpub=self.xpub, *args, **kwargs)),
                        validate_against_schema=False,
                    )
                ).data.result
            except ReceivedErrorResponseError as e:
                message = e.response.message
                error_code = str(e.response.code)
                exceptions = (await self.spec)["exceptions"]
                if error_code in exceptions:
                    exc = exceptions[error_code]
                    raise generate_exception(exc["exc_name"])(exc["docstring"]) from e
                raise UnknownError(f"Unknown error from server: {message}") from e
            except aiohttp.ClientConnectionError as e:
                raise ConnectionFailedError() from e

        return wrapper

    async def _close(self) -> None:
        await self.session.close()

    def __del__(self) -> None:
        if self._loop.is_running():
            self._loop.create_task(self._close())
        else:
            self.session._connector._closed = True  # type: ignore
