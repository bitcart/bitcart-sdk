"""Tests bitcoin methods implementation on testnet, requires daemon to be running on localhost:5000

If this succeeds, most likely other coins will succeed too
"""

import os

import pytest

from bitcart import BTC

pytestmark = pytest.mark.asyncio


async def test_compare(btc):
    assert btc == BTC()
    assert btc != 1


async def test_help(btc):
    data = await btc.help()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "broadcast" in data
    assert "gettransaction" in data
    assert "help" in data


@pytest.mark.parametrize("address,expected", [("x", False), ("tb1qzq67gkmp7fl45y5h87emyhhzdl3s77904h99c8", True)])
async def test_electrum_validate_address(btc, address, expected):
    assert await btc.server.validateaddress(address) == expected


@pytest.mark.parametrize(
    "key,expected",
    [
        ("x", False),
        ("gentle expire fatal fashion envelope cheap fury hunt inner copper boy relax", True),
        (
            "vprv9FbQPcA7jVrhYYvhDuursaPzW7DwR8qGMKVHMbrk2zy3MpFXDECCuS7jnpUV7iJZccW9ExKWMzCsf2QBeiMqGBKaKnFzcsURjUR33SNmcri",
            True,
        ),
    ],
)
async def test_validate_key(btc, key, expected):
    assert await btc.validate_key(key) == expected


async def test_config_methods(btc):
    k, v = "auto_connect", False
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v
    await btc.set_config(k, True)


async def test_create_wallet(btc, tmp_path):
    wallet_path = os.path.join(str(tmp_path), "my_wallet")
    wallet = await btc.server.create(wallet_path=wallet_path)
    assert set(wallet.keys()) == {"seed", "path", "msg"}
    assert wallet["path"] == wallet_path
