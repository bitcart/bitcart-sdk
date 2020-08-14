"""Tests bitcoin methods implementation on mainnet, requires daemon to be running on localhost:5000

If this succeeds, most likely other coins will succeed too
"""
import decimal
import os

import pytest

pytestmark = pytest.mark.asyncio


async def test_help(btc):
    data = await btc.help()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "broadcast" in data
    assert "gettransaction" in data
    assert "help" in data


@pytest.mark.parametrize("currency", ["USD", "RUB", "JPY"])
async def test_rate(btc, currency):
    price = await btc.rate(currency)
    assert price > 0
    assert isinstance(price, decimal.Decimal)


async def test_fiat(btc):
    fiat_currencies = await btc.list_fiat()
    assert ["USD", "BTC", "RUB", "JPY", "EUR"] >= fiat_currencies


@pytest.mark.parametrize("address,expected", [("x", False), ("2MxtJ3iBTaEUvmiEshfW35jDzLHsY5kh9ZM", True)])
async def test_electrum_validate_address(btc, address, expected):
    assert await btc.server.validateaddress(address) == expected


async def test_get_tx(btc):
    info = await btc.get_tx("1d8a65ec103338bb51d125015fc736a3aa93eae1d7d534ec374f6517f665c5e2")
    assert (
        info.items()
        >= {
            "partial": False,
            "version": 1,
            "segwit_ser": True,
            "inputs": [
                {
                    "prevout_hash": "3d4131a9659c442706d00b387030931778040c1d431ea188b97b090781637de3",
                    "prevout_n": 0,
                    "scriptSig": "1600144784353af5633deb3711ea68596a4d02de7bbcd0",
                    "sequence": 4294967295,
                    "type": "unknown",
                    "address": None,
                    "num_sig": 0,
                    "witness": (
                        "02483045022100e6d2b31377269c43e2aad18d252f43ef2aa36ea0ab8a822dbb9b559e"
                        "33cca42e02201a25f1cf2b97c35bdf510cce0138ca2ae2a2413dbb32fd7d6f5d9fa3b0"
                        "29f19801210282b7d73ee29098c55e011e2624f5271d0723311c880bd1d63142037a3ec9ce32"
                    ),
                }
            ],
            "outputs": [
                {
                    "value": 73061,
                    "type": 0,
                    "address": "2MxtJ3iBTaEUvmiEshfW35jDzLHsY5kh9ZM",
                    "scriptPubKey": "a9143ddb68695d7f35307c2f2e36c92cc19c06eeb31f87",
                    "prevout_n": 0,
                }
            ],
            "lockTime": 0,
        }.items()
    )


async def test_config_methods(btc):
    k, v = "x", 1
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v


async def test_get_address(btc):
    txes = await btc.get_address("2NGHDQcccX3EVehSRtSMXj8u5AhpGQ4nR6b")
    assert isinstance(txes, list)
    tx = txes[0]
    assert tx["tx_hash"] == "0eca272d77ab362e9fbcabd9a5803ba3a7fd4382a302ae9028cfacd015cc65b9"
    assert tx["height"] == 1805666
    assert tx["tx"] == await btc.get_tx(tx["tx_hash"])


async def test_create_wallet(btc, tmp_path):
    wallet_path = os.path.join(str(tmp_path), "my_wallet")
    wallet = await btc.server.create(wallet_path=wallet_path)
    assert set(wallet.keys()) == {"seed", "path", "msg"}
    assert wallet["path"] == wallet_path
