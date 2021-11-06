"""Tests bitcoin methods implementation on testnet, requires daemon to be running on localhost:5000

If this succeeds, most likely other coins will succeed too
"""
import decimal
import os

import pytest

from bitcart import BTC

from ...utils import data_check

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


@pytest.mark.parametrize("currency", ["USD", "RUB", "JPY", "nonexisting"])
async def test_rate(btc, currency):
    price = await btc.rate(currency)
    if currency == "nonexisting":
        assert price.is_nan()
    else:
        assert price > 0
    assert isinstance(price, decimal.Decimal)


async def test_fiat(btc):
    fiat_currencies = await btc.list_fiat()
    assert ["USD", "BTC", "RUB", "JPY", "EUR"] >= fiat_currencies


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


async def get_tx(btc, tx_hash):
    # TODO: remove when protocol 1.5 is released
    # This is temporarily using SPV verification to reliably get confirmations
    # This helps avoiding CI failures, see https://github.com/spesmilo/electrum/issues/7342
    return await btc.server.get_transaction(tx_hash, use_spv=True)


async def get_address(btc, address):
    out = await btc.server.getaddresshistory(address)
    for i in out:
        i["tx"] = await get_tx(btc, i["tx_hash"])
    return out


async def test_get_tx(btc):
    info = await get_tx(btc, "8cf9bacdddca9d1059774d2b30327e9844175635d484c971c695b5d4b831b81b")
    assert info.items() > {"version": 2, "locktime": 2102908}.items()
    data_check(info, "confirmations", int)
    assert info["confirmations"] > 0
    data_check(info, "inputs", list, 1)
    assert (
        info["inputs"][0].items()
        >= {
            "prevout_hash": "2948fda648b840900c3fbc396e8f4156eac33b73ffef52a32f61554499824054",
            "prevout_n": 1,
            "coinbase": False,
            "scriptSig": "160014e2f0082306143e08f484ffde4f80001e5f4fb17a",
            "nsequence": 4294967294,
            "witness": (
                "024630430220069d39247b7aa70f15468e193a98ee350890c779268c39e1"
                "0d35329acffb167f021f7ed94659c9b381abbe7b6f0bfb6b2f04766c88f2"
                "0f8faf7170f9a53724842b012102145e6b3bb6c8d409754da495460573a0"
                "209dbc33fe22193014993423f032c3bc"
            ),
        }.items()
    )
    data_check(info, "outputs", list, 2)
    assert info["outputs"][0] == {
        "value_sats": 3430096510,
        "address": "2MwCzCcXzvmKuB4A1CMy3Atd9eH4fJQLq7H",
        "scriptpubkey": "a9142b74297c318e8f20a817e2afb21a8fd366f6659387",
    }


async def test_config_methods(btc):
    k, v = "x", 1
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v


async def test_get_address(btc):
    txes = await get_address(btc, "2MwCzCcXzvmKuB4A1CMy3Atd9eH4fJQLq7H")
    assert isinstance(txes, list)
    tx = txes[0]
    assert tx["tx_hash"] == "8cf9bacdddca9d1059774d2b30327e9844175635d484c971c695b5d4b831b81b"
    assert tx["height"] == 2102909
    tx2 = await get_tx(btc, tx["tx_hash"])
    # To avoid comparing exact confirmations
    # TODO: remove when SPV verification is the default
    tx["tx"].pop("confirmations")
    tx2.pop("confirmations")
    assert tx["tx"] == tx2


async def test_create_wallet(btc, tmp_path):
    wallet_path = os.path.join(str(tmp_path), "my_wallet")
    wallet = await btc.server.create(wallet_path=wallet_path)
    assert set(wallet.keys()) == {"seed", "path", "msg"}
    assert wallet["path"] == wallet_path
