"""Tests bitcoin methods implementation on mainnet, requires daemon to be running on localhost:5000

If this succeeds, most likely other coins will succeed too
"""
import os
import pytest
import decimal

pytestmark = pytest.mark.asyncio


async def test_help(btc):
    data = await btc.help()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "broadcast" in data
    assert "gettransaction" in data
    assert "help" in data


@pytest.mark.parametrize("currency,accurate", [
    ("USD", True),
    ("USD", False),
    ("RUB", True),
    ("RUB", False),
    ("JPY", True),
    ("JPY", False),
])
async def test_rate(btc, currency, accurate):
    price = await btc.rate(currency, accurate)
    assert price > 0
    price_type = decimal.Decimal if accurate else float
    assert isinstance(price, price_type)


async def test_fiat(btc):
    assert await btc.list_fiat()


@pytest.mark.parametrize("address,expected", [
    ("x", False),
    ("2MxtJ3iBTaEUvmiEshfW35jDzLHsY5kh9ZM", True),
])
async def test_electrum_validate_address(btc, address, expected):
    is_valid = await btc.server.validateaddress(address)
    assert is_valid == expected


async def test_get_tx(btc):
    info = await btc.get_tx("1d8a65ec103338bb51d125015fc736a3aa93eae1d7d534ec374f6517f665c5e2")
    assert set(info.keys()) == {'partial', 'version', 'segwit_ser', 'inputs', 'outputs', 'lockTime', 'confirmations'}


async def test_config_methods(btc):
    k, v = "x", 1
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v


async def test_get_address(btc):
    assert await btc.get_address("2NGHDQcccX3EVehSRtSMXj8u5AhpGQ4nR6b")


async def test_create_wallet(btc, tmp_path):
    wallet_path = os.path.join(str(tmp_path), 'my_wallet')
    wallet = await btc.server.create(wallet_path=wallet_path)
    assert set(wallet.keys()) == {'seed', 'path', 'msg'}
    assert wallet['path'] == wallet_path



