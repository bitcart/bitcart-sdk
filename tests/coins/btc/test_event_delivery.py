import multiprocessing
import time

import pytest
from aiohttp import ClientSession

test_queue = multiprocessing.Queue()


@pytest.yield_fixture
def setup_webhook(btc_wallet):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    process = multiprocessing.Process(target=btc_wallet.start_websocket)  # wallet required
    process.start()
    time.sleep(2)
    yield
    process.terminate()
    process.join()


def new_tx_handler(event, tx):
    test_queue.put(True)


@pytest.mark.asyncio
async def test_event_delivery(setup_webhook):
    async with ClientSession() as session:
        async with session.post("http://localhost:6000") as resp:  # no json passed, silently ignoring
            assert await resp.json() == {}
        assert test_queue.qsize() == 0
        async with session.post(
            "http://localhost:6000", json={"updates": [{"event": "new_transaction", "tx": "test"}]}
        ) as resp:
            assert await resp.json() == {}
        assert test_queue.qsize() == 1
        assert test_queue.get() is True
