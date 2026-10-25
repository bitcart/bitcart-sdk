import asyncio
import base64

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import unused_port

from bitcart.errors import ConnectionFailedError, UnknownError
from bitcart.providers.jsonrpcrequests import RPCProxy, create_request

MOCK_RPC_URL = "http://localhost:5000"


def test_create_request_args_only():
    req = create_request("foo", 1, "two")
    assert req["method"] == "foo"
    assert req["params"] == [1, "two"]


@pytest.mark.parametrize(
    "spec",
    [
        "not a dict",
        {"version": "1"},
        {"version": 1, "exceptions": {}},
        {"version": "1", "exceptions": "not a dict"},
        {"version": "1", "exceptions": {"-32600": "not a dict"}},
        {"version": "1", "exceptions": {"-32600": {"exc_name": "E"}}},
    ],
)
def test_validate_spec_rejects_invalid(spec):
    proxy = RPCProxy(MOCK_RPC_URL)
    assert proxy.validate_spec(spec) is False


def test_validate_spec_accepts_valid():
    proxy = RPCProxy(MOCK_RPC_URL)
    valid = {"version": "1", "exceptions": {"-32600": {"exc_name": "E", "docstring": "d"}}}
    assert proxy.validate_spec(valid) is True


async def test_session_reuses_passed_session():
    session = aiohttp.ClientSession()
    try:
        proxy = RPCProxy(MOCK_RPC_URL, session=session)
        assert proxy.session is session
    finally:
        await session.close()


async def test_close_cleans_up_sessions():
    session = aiohttp.ClientSession()
    proxy = RPCProxy(MOCK_RPC_URL, session=session)
    await proxy.close()
    assert session.closed
    await proxy.close()  # subsequent close is a no-op


AUTHORIZATION_HEADERS = web.AppKey("authorization_headers", list)


async def start_rpc_server():
    async def handle(request):
        request.app[AUTHORIZATION_HEADERS].append(request.headers.get("Authorization"))
        body = await request.json()
        return web.json_response({"jsonrpc": "2.0", "result": True, "id": body["id"]})

    app = web.Application()
    app[AUTHORIZATION_HEADERS] = []
    app.router.add_post("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = unused_port()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    return runner, f"http://127.0.0.1:{port}"


@pytest.mark.parametrize(
    ("username", "password", "expected"),
    [
        ("user", "pässword", "Basic " + base64.b64encode("user:pässword".encode("latin1")).decode()),
        ("user", None, "Basic " + base64.b64encode(b"user:").decode()),
        (None, None, None),
    ],
)
async def test_session_sends_basic_auth(username, password, expected):
    server, url = await start_rpc_server()
    proxy = RPCProxy(url, username, password)
    await proxy.help()
    assert server.app[AUTHORIZATION_HEADERS] == [expected]
    await proxy.close()
    await server.cleanup()


async def open_session(url):
    proxy = RPCProxy(url, "user", "pass")
    await proxy.help()
    return proxy, proxy.session


async def test_close_awaits_current_loop_session():
    server, url = await start_rpc_server()
    proxy, session = await open_session(url)
    await proxy.close()
    assert session.connector is None
    await server.cleanup()


def test_garbage_collected_proxy_closes_session_on_its_idle_loop():
    with asyncio.Runner(loop_factory=asyncio.new_event_loop) as runner:
        server, url = runner.run(start_rpc_server())
        proxy, session = runner.run(open_session(url))
        del proxy
        assert session.connector is None
        runner.run(server.cleanup())


def test_close_from_other_loop_closes_session_on_its_own_loop():
    async def close(proxy):
        await proxy.close()

    with asyncio.Runner(loop_factory=asyncio.new_event_loop) as runner:
        server, url = runner.run(start_rpc_server())
        proxy, session = runner.run(open_session(url))
        with asyncio.Runner(loop_factory=asyncio.new_event_loop) as other:
            other.run(close(proxy))
        assert session.connector is None
        runner.run(server.cleanup())


def _mock_session_with_response(mocker, body: str):
    response = mocker.MagicMock()
    response.text = mocker.AsyncMock(return_value=body)
    session = mocker.MagicMock()
    session.post.return_value.__aenter__.return_value = response
    return session


async def test_wrapper_raises_unknown_error_for_unmapped_code(mocker):
    session = _mock_session_with_response(
        mocker, '{"jsonrpc": "2.0", "error": {"code": -99999, "message": "boom"}, "id": null}'
    )
    proxy = RPCProxy(MOCK_RPC_URL, session=session)
    proxy._spec_valid = True
    with pytest.raises(UnknownError, match="boom"):
        await proxy.some_method()


async def test_wrapper_wraps_connection_errors(mocker):
    session = mocker.MagicMock()
    session.post.side_effect = aiohttp.ClientConnectionError("no route")
    proxy = RPCProxy(MOCK_RPC_URL, session=session)
    with pytest.raises(ConnectionFailedError):
        await proxy.some_method()
