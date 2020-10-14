import socket
import warnings

import pytest
from aiohttp import ClientSession, TCPConnector, web
from aiohttp.resolver import DefaultResolver
from aiohttp.test_utils import unused_port

from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB = "zprvAWgYBBk7JR8GkUwcwyhT1qk8FQpym8cHboGyDEdMhHcL1NRe8bioZR3uo5gTSTG47iqQX6VqPL6iHHDNK55taJiV9MEscu6UiqSR1tAiSUq"
REGTEST_XPUB = (
    "vprv9DMUxX4ShgxMMQduKMSnoNsX4jZjdqmRRapGRRFbok1XXrjkvFyAnvSVPbs4t8ZDA73fTT9DLzdCyHBh39AZHG8nsP1gEj11EwSdYP8zhKF"
)
LIGHTNING_UNSUPPORTED_XPUB = (
    "xprv9s21ZrQH143K3tZPHG8CbfZ7uUY5stdHmaEXeSqawGrZuAoBdHPgKHjdkfmHSdxDJSbo29JiU1PcWhzEsgFryqMHQfr2T5TWBPK8EqFjscZ"
)


@pytest.fixture
async def xpub():
    return TEST_XPUB


@pytest.fixture
async def coin():
    return Coin()


@pytest.fixture
async def btc_nowallet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return BTC()


@pytest.fixture
async def btc_wallet():
    return BTC(xpub=TEST_XPUB)


@pytest.fixture
async def lightning_unsupported_wallet():
    return BTC(xpub=LIGHTNING_UNSUPPORTED_XPUB)


@pytest.fixture
async def regtest_wallet():
    return BTC(xpub=REGTEST_XPUB)


@pytest.fixture
async def regtest_node_id():
    return await BTC(xpub=REGTEST_XPUB, rpc_url="http://localhost:5110").node_id


@pytest.fixture
async def btc():
    with warnings.catch_warnings():  # to ignore no xpub passed warning
        warnings.simplefilter("ignore")
        btc_obj = BTC()
    return btc_obj


class FakeResolver:
    _LOCAL_HOST = {0: "127.0.0.1", socket.AF_INET: "127.0.0.1", socket.AF_INET6: "::1"}

    def __init__(self, fakes):
        """fakes -- dns -> port dict"""
        self._fakes = fakes
        self._resolver = DefaultResolver()

    async def resolve(self, host, port=0, family=socket.AF_INET):
        fake_port = self._fakes.get(host)
        if fake_port is not None:
            return [
                {
                    "hostname": host,
                    "host": self._LOCAL_HOST[family],
                    "port": fake_port,
                    "family": family,
                    "proto": 0,
                    "flags": socket.AI_NUMERICHOST,
                }
            ]
        else:
            return await self._resolver.resolve(host, port, family)


class FakeDaemon:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_routes([web.get("/ws", self.handle_websocket)])
        self.runner = None

    async def start(self):
        port = unused_port()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "127.0.0.1", port)
        await site.start()
        return {"localhost": port}

    async def stop(self):
        await self.runner.cleanup()

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_json({"wallet": TEST_XPUB, "updates": [{"event": "new_transaction", "tx": "test"}]})
        await ws.close()


@pytest.yield_fixture
async def patched_session():
    try:
        fake_daemon = FakeDaemon()
        info = await fake_daemon.start()
        resolver = FakeResolver(info)
        connector = TCPConnector(resolver=resolver)
        fake_session = ClientSession(connector=connector)
        yield fake_session
    finally:
        await fake_daemon.stop()
