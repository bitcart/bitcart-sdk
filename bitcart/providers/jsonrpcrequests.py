from typing import Any, Callable, Optional, Union

ASYNC = True


try:
    import jsonrpcclient

    if ASYNC:
        import aiohttp
        from jsonrpcclient.clients.aiohttp_client import AiohttpClient as RPC
        import asyncio
    else:
        import requests
        from jsonrpcclient.clients.http_client import HTTPClient as RPC
except (ModuleNotFoundError, ImportError):
    pass  # probably during CI build


class RPCProxy:
    def __init__(
        self: "RPCProxy",
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        xpub: Optional[str] = None,
        session: Optional[Union["aiohttp.ClientSession", "requests.Session"]] = None,
        proxy: Optional[str] = None,
        verify: Optional[bool] = True,
    ):
        self.url = url
        self.username = username
        self.password = password
        self.xpub = xpub
        self.proxy = proxy
        if not ASYNC and self.proxy:
            self.proxy = self.proxy.replace(
                "socks5://", "socks5h://"
            )  # replace protocol
        self.verify = verify
        self.session: Union["aiohttp.ClientSession", "requests.Session"]
        if ASYNC:
            self._connector_class = aiohttp.TCPConnector
            self._connector_init = dict(ssl=self.verify)
            self._loop = asyncio.get_event_loop()
            self._loop.set_exception_handler(lambda loop, context: None)
        if session:
            self.sesson = session
        else:
            self.create_session()
        if ASYNC:
            self.rpc = RPC(endpoint=self.url, session=self.session)
        else:
            self.rpc = RPC(endpoint=self.url)  # pylint: disable=no-value-for-parameter
            self.rpc.session = self.session

    def init_proxy(self: "RPCProxy") -> None:
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

    def create_session(self: "RPCProxy") -> None:
        if ASYNC:
            self.init_proxy()
            self.session = aiohttp.ClientSession(
                connector=self._connector_class(**self._connector_init),  # type: ignore
                loop=self._loop,
                auth=aiohttp.BasicAuth(self.username, self.password),  # type: ignore
            )
        else:
            proxies = {"http": self.proxy, "https": self.proxy}
            self.session = requests.Session()
            self.session.proxies = proxies  # type: ignore
            self.session.auth = (self.username, self.password)  # type: ignore

    def __getattr__(
        self: "RPCProxy", method: str, *args: Any, **kwargs: Any
    ) -> Callable:
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

    async def _close(self: "RPCProxy") -> None:
        await self.session.close()  # type: ignore

    def __del__(self: "RPCProxy") -> None:
        if ASYNC and self._loop.is_running():
            self._loop.create_task(self._close())
