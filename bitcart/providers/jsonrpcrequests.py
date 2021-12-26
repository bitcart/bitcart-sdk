import asyncio
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import urljoin

import aiohttp
from jsonrpcclient import Ok, parse_json, request
from universalasync import async_to_sync_wraps, get_event_loop

from ..errors import ConnectionFailedError, UnknownError, generate_exception
from ..utils import json_encode


def create_request(method: str, *args: Any, **kwargs: Any) -> dict:
    params: Union[list, dict] = []
    if args and kwargs:
        # It actually violates json-rpc 2.0 spec but is pretty convenient for passing both positional and named arguments
        params = list(args)
        params.append(kwargs)
    elif args:
        params = list(args)
    elif kwargs:
        params = kwargs
    return request(method, params)


class RPCProxy:
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
        self._spec = {"exceptions": {"-32600": {"exc_name": "UnauthorizedError", "docstring": "Unauthorized"}}}
        self._spec_valid = False
        self._sessions: Dict[asyncio.AbstractEventLoop, aiohttp.ClientSession] = {}
        if session is not None:
            self._sessions[get_event_loop()] = session

    @property
    def session(self) -> aiohttp.ClientSession:
        loop = get_event_loop()
        session = self._sessions.get(loop)
        if session is not None:
            return session
        self._sessions[loop] = self.create_session()
        return self._sessions[loop]

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

    def create_session(self) -> aiohttp.ClientSession:
        self.init_proxy()
        return aiohttp.ClientSession(
            connector=self._connector_class(**self._connector_init),  # type: ignore
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
        @async_to_sync_wraps
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                async with self.session.post(
                    self.url, data=json_encode(create_request(method, xpub=self.xpub, *args, **kwargs)), timeout=5 * 60
                ) as response:
                    parsed = parse_json(await response.text())
                    if isinstance(parsed, Ok):
                        return parsed.result
                    else:
                        message = parsed.message
                        error_code = str(parsed.code)
                        exceptions = (await self.spec)["exceptions"]
                        if error_code in exceptions:
                            exc = exceptions[error_code]
                            raise generate_exception(exc["exc_name"])(exc["docstring"])
                        raise UnknownError(f"Unknown error from server: {message}")
            except aiohttp.ClientConnectionError as e:
                raise ConnectionFailedError() from e

        return wrapper

    async def _close(self) -> None:
        for session in self._sessions.values():
            if session is not None:
                await session.close()

    def __del__(self) -> None:
        loop = get_event_loop()
        if loop.is_running():
            loop.create_task(self._close())
        else:
            loop.run_until_complete(self._close())
