import multiprocessing
import time

import pytest
from aiohttp import ClientSession

from bitcart import BTC, GZRO, LTC
from bitcart.manager import APIManager

pytestmark = pytest.mark.asyncio

test_queue = multiprocessing.Queue()


def new_tx_handler(instance, event, tx):
    if isinstance(instance, BTC):
        test_queue.put(True)


@pytest.fixture
async def manager(xpub):
    return APIManager({"BTC": [xpub, xpub]})


@pytest.fixture
async def webhook_manager(xpub):
    return APIManager({"BTC": [xpub, "test"]})


@pytest.yield_fixture
def setup_webhook(webhook_manager):
    webhook_manager.add_event_handler("new_transaction", new_tx_handler)
    process = multiprocessing.Process(target=webhook_manager.start_webhook)
    process.start()
    time.sleep(2)
    yield
    process.terminate()
    process.join()


async def test_manager_storage(manager, xpub):
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}}
    assert manager.wallets.BTC == manager.wallets["BTC"] == manager.BTC == manager["BTC"]


async def test_manager_classmethods(xpub):
    assert APIManager.load_wallet("BTC", xpub) == BTC(xpub=xpub)
    assert APIManager.load_wallets("BTC", [xpub, xpub]) == {xpub: BTC(xpub=xpub)}


async def test_manager_add_wallets(manager, xpub):
    assert manager.add_wallet("LTC", xpub) is None
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}, "LTC": {xpub: LTC(xpub=xpub)}}
    assert manager.add_wallets("GZRO", [xpub, xpub]) is None
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}, "LTC": {xpub: LTC(xpub=xpub)}, "GZRO": {xpub: GZRO(xpub=xpub)}}


async def test_manager_start_webhook(setup_webhook, xpub):
    async with ClientSession() as session:
        async with session.post(
            "http://localhost:6000", json={"wallet": xpub, "updates": [{"event": "new_transaction", "tx": "test"}]}
        ) as resp:
            assert await resp.json() == {}
        assert test_queue.qsize() == 1
        assert test_queue.get() is True
