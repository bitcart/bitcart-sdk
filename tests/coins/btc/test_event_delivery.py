import multiprocessing

import pytest

from bitcart.errors import ConnectionFailedError
from tests.utils import patch_session

test_queue = multiprocessing.Queue()

pytestmark = pytest.mark.asyncio


def new_tx_handler(event, tx):
    test_queue.put(True)


def new_tx_handler_less_params(event):
    test_queue.put(True)


async def test_event_delivery(patched_session, btc_wallet, mocker):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    patch_session(mocker, patched_session)
    await btc_wallet.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True


async def test_bad_connection(btc_wallet):
    btc_wallet.server.url = "http://localhost1:11234"  # nothing running
    with pytest.raises(ConnectionFailedError):
        await btc_wallet.start_websocket(auto_reconnect=False)


async def test_bad_json(patched_session_bad_json, btc_wallet, mocker):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    patch_session(mocker, patched_session_bad_json)
    await btc_wallet.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 0


async def test_bad_json_reconnect_callback(patched_session_bad_json, btc_wallet, mocker):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    patch_session(mocker, patched_session_bad_json)
    await btc_wallet.start_websocket(auto_reconnect=False, reconnect_callback=lambda: test_queue.put(True))
    assert test_queue.qsize() == 1  # from reconnect_callback
    assert test_queue.get() is True


async def test_event_delivery_less_params(patched_session, btc_wallet, mocker):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler_less_params)
    patch_session(mocker, patched_session)
    await btc_wallet.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True
