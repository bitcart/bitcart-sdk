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
    info = await get_tx(btc, "15967d9ed9b63f068c7578d54b7adff859f4aadc1253ba316b429d251da6b48c")
    assert info.items() > {"version": 2, "locktime": 1895035}.items()
    data_check(info, "confirmations", int)
    assert info["confirmations"] > 0
    data_check(info, "inputs", list, 1)
    assert (
        info["inputs"][0].items()
        >= {
            "prevout_hash": "3fb55b64df34ded97e97cbd5cfc17b6f114a086950fbb0bffe3c985bfa9f5af8",
            "prevout_n": 1,
            "coinbase": False,
            "nsequence": 4294967294,
            "scriptSig": "",
            "witness": (
                "024730440220331290fdbb259fde31d6e0c4eea883e7b7442b1fb1dab0b7"
                "63cd82c1c5b27a6a02205f37387895fbedb5514a6eb3f374c3943ffefd5d"
                "f589ac5c59f34f99558386a501210314ef5ee304b86a5c2bbc9d9e1987cd"
                "0cb156ca6942ea41dfb487f8d5494bc5bf"
            ),
        }.items()
    )
    data_check(info, "outputs", list, 2)
    assert info["outputs"][0] == {
        "scriptpubkey": "a9144eee7441c8104f1470e6dde89f1439cab91fdc9987",
        "address": "2MzSaML6Y3kGn7mPx1T9xXZW1r2N9vKhGo2",
        "value_sats": 1515748829,
    }


async def test_config_methods(btc):
    k, v = "x", 1
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v


async def test_get_address(btc):
    txes = await get_address(btc, "2MzSaML6Y3kGn7mPx1T9xXZW1r2N9vKhGo2")
    assert isinstance(txes, list)
    tx = txes[0]
    assert tx["tx_hash"] == "15967d9ed9b63f068c7578d54b7adff859f4aadc1253ba316b429d251da6b48c"
    assert tx["height"] == 1895036
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
