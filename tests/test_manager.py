import multiprocessing

import pytest

from bitcart import BCH, BTC, LTC
from bitcart.errors import CurrencyUnsupportedError, NoCurrenciesRegisteredError
from bitcart.manager import APIManager
from tests.utils import patch_session

pytestmark = pytest.mark.asyncio

test_queue = multiprocessing.Queue()
test_queue2 = multiprocessing.Queue()


class DummyServer:
    url = "http://localhost:5000"
    session = None


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


@pytest.fixture
async def websocket_manager_no_wallets():
    return APIManager({"BTC": []})


async def test_manager_storage(manager, xpub):
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}}
    assert manager.wallets.BTC == manager.wallets["BTC"] == manager.BTC == manager["BTC"]


async def test_manager_methods(xpub):
    manager = APIManager()
    assert manager.load_wallet("BTC", xpub) == BTC(xpub=xpub)
    assert manager.load_wallets("BTC", [xpub, xpub]) == {xpub: BTC(xpub=xpub)}
    with pytest.raises(CurrencyUnsupportedError):
        manager.load_wallet("test")
    with pytest.raises(CurrencyUnsupportedError):
        manager.load_wallets("test", [xpub])


async def test_manager_add_wallets(manager, xpub):
    assert manager.add_wallet("LTC", xpub) is None
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}, "LTC": {xpub: LTC(xpub=xpub)}}
    assert manager.add_wallets("BCH", [xpub, xpub]) is None
    assert manager.wallets == {"BTC": {xpub: BTC(xpub=xpub)}, "LTC": {xpub: LTC(xpub=xpub)}, "BCH": {xpub: BCH(xpub=xpub)}}


async def test_manager_start_websocket(patched_session, websocket_manager, xpub, mocker):
    websocket_manager.add_event_handler("new_transaction", new_tx_handler)
    patch_session(mocker, patched_session)
    await websocket_manager.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True


async def test_manager_reconnect_callback(patched_session, websocket_manager, xpub, mocker):
    patch_session(mocker, patched_session)
    await websocket_manager.start_websocket(auto_reconnect=False, reconnect_callback=reconnect_callback)
    assert test_queue2.qsize() == 1
    assert test_queue2.get() == "BTC"


async def test_manager_no_wallets(patched_session, websocket_manager_no_wallets, mocker):
    websocket_manager_no_wallets.add_event_handler("new_transaction", new_tx_handler)
    server = DummyServer()
    server.session = patched_session
    mocker.patch("bitcart.APIManager._get_websocket_server", return_value=server)
    await websocket_manager_no_wallets.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 1
    assert test_queue.get() is True


async def test_manager_no_currencies():
    with pytest.raises(NoCurrenciesRegisteredError):
        await APIManager().start_websocket(auto_reconnect=False)


async def test_manager_bad_currency(patched_session_bad_currency, websocket_manager, xpub, mocker, caplog):
    websocket_manager.add_event_handler("new_transaction", new_tx_handler)
    patch_session(mocker, patched_session_bad_currency)
    await websocket_manager.start_websocket(auto_reconnect=False)
    assert test_queue.qsize() == 0
    assert "Received event for unsupported currency: test" in caplog.text
