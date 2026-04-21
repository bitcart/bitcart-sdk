import asyncio

import aiohttp
import pytest
from universalasync import get_event_loop

from bitcart.errors import ConnectionFailedError, UnknownError
from bitcart.providers.jsonrpcrequests import RPCProxy, _cleanup_sessions, create_request

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
    assert not proxy._finalizer.alive
    await proxy.close()  # subsequent close is a no-op


def test_cleanup_skips_closed_or_none_sessions(mocker):
    _cleanup_sessions({})

    closed_session = mocker.MagicMock(closed=True)
    closed_session.close = mocker.AsyncMock()

    loop = asyncio.new_event_loop()
    try:
        sessions = {loop: closed_session, object(): None}
        _cleanup_sessions(sessions)
        assert sessions == {}
        closed_session.close.assert_not_called()
    finally:
        loop.close()


def _mock_session_with_response(mocker, body: str):
    response = mocker.MagicMock()
    response.text = mocker.AsyncMock(return_value=body)
    session = mocker.MagicMock()
    session.post.return_value.__aenter__.return_value = response
    return session


async def test_wrapper_raises_unknown_error_for_unmapped_code(mocker):
    proxy = RPCProxy(MOCK_RPC_URL)
    proxy._spec_valid = True
    proxy._sessions[get_event_loop()] = _mock_session_with_response(
        mocker, '{"jsonrpc": "2.0", "error": {"code": -99999, "message": "boom"}, "id": null}'
    )
    with pytest.raises(UnknownError, match="boom"):
        await proxy.some_method()


async def test_wrapper_wraps_connection_errors(mocker):
    proxy = RPCProxy(MOCK_RPC_URL)
    session = mocker.MagicMock()
    session.post.side_effect = aiohttp.ClientConnectionError("no route")
    proxy._sessions[get_event_loop()] = session
    with pytest.raises(ConnectionFailedError):
        await proxy.some_method()
