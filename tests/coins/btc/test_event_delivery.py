import multiprocessing
import time

import pytest
from aiohttp import ClientSession

test_queue = multiprocessing.Queue()


def setup_func(func, btc_wallet):
    btc_wallet.add_event_handler("new_transaction", new_tx_handler)
    process = multiprocessing.Process(target=getattr(btc_wallet, func))  # wallet required
    process.start()
    time.sleep(1)
    yield
    process.terminate()
    process.join()


@pytest.yield_fixture
def setup_webhook(btc_wallet):
    yield from setup_func("start_webhook", btc_wallet)


def new_tx_handler(event, tx):
    test_queue.put(True)


@pytest.mark.asyncio
async def test_test(setup_webhook, btc_wallet):
    async with ClientSession() as session:
        async with session.post("http://localhost:6000") as resp:  # no json passed, silently ignoring
            assert await resp.json() == {}
        assert test_queue.qsize() == 0
        async with session.post("http://localhost:6000", json={"event": "new_transaction", "tx": "test"}) as resp:
            assert await resp.json() == {}
        assert test_queue.qsize() == 1
        assert test_queue.get() is True
