import socket

import pytest
from aiohttp import ClientSession, TCPConnector, web
from aiohttp.resolver import DefaultResolver
from aiohttp.test_utils import unused_port

from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB = "vpub5Uako7h1ZsQzm31AKwSsEiLj494RpbZ7iYQt9zGMbLW2EcafkmWTTESDe5NJpKTBeyyf15mPKPTPgNYdS5756jua2KFBHuGAdXqQfXkk9oQ"
# deterministic channels support only seeds
REGTEST_XPUB = "dutch field mango comfort symptom smooth wide senior tongue oyster wash spoon"
REGTEST_XPUB2 = "hungry ordinary similar more spread math general wire jealous valve exhaust emotion"
LIGHTNING_UNSUPPORTED_XPUB = (
    "tpubDCrWxr5Vm9TtZAkcWyYa4jK5GLoia1c9HisBP5YUyh9bCu3ePsw74mp4GoYZXH3vYDhg4pRjskbsr7PkD4REnwiWB93d78HkdJnYY7aGjy1"
)


@pytest.fixture
async def xpub():
    return TEST_XPUB


@pytest.fixture
async def coin():
    return Coin()


@pytest.fixture
async def btc_nowallet():
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
async def regtest_node():
    return BTC(xpub=REGTEST_XPUB2, rpc_url="http://localhost:5110")


@pytest.fixture
async def regtest_node_id(regtest_node):
    return await regtest_node.node_id


@pytest.fixture
async def btc():
    return BTC()


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
        await self.reply_to_websocket(ws)
        await ws.close()

    async def reply_to_websocket(self, ws):
        await ws.send_json({"wallet": TEST_XPUB, "updates": [{"event": "new_transaction", "tx": "test"}]})


class FakeBadJSONDaemon(FakeDaemon):
    async def reply_to_websocket(self, ws):
        await ws.send_str("")


class FakeBadCurrencyDaemon(FakeDaemon):
    async def reply_to_websocket(self, ws):
        await ws.send_json({"currency": "test", "updates": [{"event": "new_transaction", "tx": "test"}]})


async def patched_session_maker(daemon_class):
    fake_daemon = daemon_class()
    info = await fake_daemon.start()
    resolver = FakeResolver(info)
    connector = TCPConnector(resolver=resolver)
    fake_session = ClientSession(connector=connector)
    return fake_session, fake_daemon


@pytest.fixture
async def patched_session():
    session, daemon = await patched_session_maker(FakeDaemon)
    yield session
    await daemon.stop()


@pytest.fixture
async def patched_session_bad_json():
    session, daemon = await patched_session_maker(FakeBadJSONDaemon)
    yield session
    await daemon.stop()


@pytest.fixture
async def patched_session_bad_currency():
    session, daemon = await patched_session_maker(FakeBadCurrencyDaemon)
    yield session
    await daemon.stop()
