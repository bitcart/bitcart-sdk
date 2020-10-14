import multiprocessing

import pytest

test_queue = multiprocessing.Queue()

pytestmark = pytest.mark.asyncio


def new_tx_handler(event, tx):
    test_queue.put(True)


async def test_event_delivery(patched_session, btc_wallet, mocker):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    mocker.patch.object(btc_wallet.server, "session", patched_session)
    await btc_wallet.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True
