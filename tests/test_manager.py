import multiprocessing

import pytest

from bitcart import BTC, GZRO, LTC
from bitcart.errors import NoCurrenciesRegisteredError
from bitcart.manager import APIManager

pytestmark = pytest.mark.asyncio

test_queue = multiprocessing.Queue()
test_queue2 = multiprocessing.Queue()


def new_tx_handler(instance, event, tx):
    if isinstance(instance, BTC):
        test_queue.put(True)


def reconnect_callback(currency):
    test_queue2.put(currency)


@pytest.fixture
async def manager(xpub):
    return APIManager({"BTC": [xpub, xpub]})


@pytest.fixture
async def websocket_manager(xpub):
    return APIManager({"BTC": [xpub, "test"]})


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


async def test_manager_start_websocket(patched_session, websocket_manager, mocker):
    websocket_manager.add_event_handler("new_transaction", new_tx_handler)
    mocker.patch.dict(websocket_manager.sessions, {"BTC": patched_session})
    await websocket_manager.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True


async def test_manager_reconnect_callback(patched_session, websocket_manager, mocker):
    mocker.patch.dict(websocket_manager.sessions, {"BTC": patched_session})
    await websocket_manager.start_websocket(auto_reconnect=False, reconnect_callback=reconnect_callback)
    assert test_queue2.qsize() == 1
    assert test_queue2.get() == "BTC"


async def test_manager_no_currencies():
    with pytest.raises(NoCurrenciesRegisteredError):
        await APIManager().start_websocket(auto_reconnect=False)
