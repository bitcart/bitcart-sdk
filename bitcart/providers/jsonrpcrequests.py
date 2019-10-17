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
        verify: Optional[bool] = True,
    ):
        self.url = url
        self.username = username
        self.password = password
        self.xpub = xpub
        self.verify = verify
        self.session: Union["aiohttp.ClientSession", "requests.Session"]
        if ASYNC:
            self._loop = asyncio.get_event_loop()
        if session:
            self.sesson = session
        else:
            self.create_session()
        if ASYNC:
            self.rpc = RPC(endpoint=self.url, session=self.session)
        else:
            self.rpc = RPC(endpoint=self.url)
            self.rpc.session = self.session

    def create_session(self: "RPCProxy") -> None:
        if ASYNC:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.verify),
                auth=aiohttp.BasicAuth(self.username, self.password),  # type: ignore
            )
        else:
            self.session = requests.Session()
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
        if ASYNC:
            if self._loop.is_running():
                self._loop.create_task(self._close())
            else:
                self.session.connector._closed = True  # type: ignore
