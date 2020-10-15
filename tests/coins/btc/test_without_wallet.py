"""Tests bitcoin methods implementation on mainnet, requires daemon to be running on localhost:5000

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


@pytest.mark.parametrize("currency", ["USD", "RUB", "JPY"])
async def test_rate(btc, currency):
    price = await btc.rate(currency)
    assert price > 0
    assert isinstance(price, decimal.Decimal)


async def test_fiat(btc):
    fiat_currencies = await btc.list_fiat()
    assert ["USD", "BTC", "RUB", "JPY", "EUR"] >= fiat_currencies


@pytest.mark.parametrize("address,expected", [("x", False), ("1KQah89MJhmhxB9hRQN6DnMSkPH3RUjPev", True)])
async def test_electrum_validate_address(btc, address, expected):
    assert await btc.server.validateaddress(address) == expected


@pytest.mark.parametrize(
    "key,expected",
    [
        ("x", False),
        ("gentle expire fatal fashion envelope cheap fury hunt inner copper boy relax", True),
        (
            "xprv9s21ZrQH143K2MFWUoJmzzhhi1SNUqCFeJjbjpWvpvx9T6yxJXUpfW7fPECCNmzHGHQ6qkZYvRGvKu6D2KunXJ2kNccxT6b266F92DbRu35",
            True,
        ),
    ],
)
async def test_validate_key(btc, key, expected):
    assert await btc.validate_key(key) == expected


async def test_get_tx(btc):
    info = await btc.get_tx("0584c650e7b04cd0788832f8340ead4ce654e82127e283c8132a0bcbfabc7a01")
    assert info.items() > {"version": 1, "locktime": 0}.items()
    data_check(info, "confirmations", int)
    assert info["confirmations"] > 0
    data_check(info, "inputs", list, 1)
    assert (
        info["inputs"][0].items()
        >= {
            "prevout_hash": "f5bec7770c30679bd7e91ecc3cf243d43c5a72b28ac8e037eb8c1b5bfe520e27",
            "prevout_n": 0,
            "coinbase": False,
            "scriptSig": "",
            "nsequence": 4294967295,
            "witness": (
                "02473044022030f19cf4b53b0c5d7a9d920240f6daab0cf8a40193f80a8"
                "0d40635dc0ca213af0220487e8714a082f22dba14733f1149bd365767702"
                "f69bc88375d1c47ba8d12138c012103765314d3e5ebb0af504c4993952d9"
                "903648fa3cc645dbaedfd9c40484531836e"
            ),
        }.items()
    )
    data_check(info, "outputs", list, 2)
    assert info["outputs"][0] == {
        "value_sats": 490000,
        "address": "3NyLhw2jKrA8PF2SqgGQu4cigfCg1i6SqH",
        "scriptpubkey": "a914e970f9ca2f7d99b208b455333b0a4ab2b9b7eb3a87",
    }


async def test_config_methods(btc):
    k, v = "x", 1
    await btc.set_config(k, v)
    assert await btc.get_config(k) == v


async def test_get_address(btc):
    txes = await btc.get_address("17ncZMaFQYZYNDycTJc5aydUKaw6oCEUSQ")
    assert isinstance(txes, list)
    tx = txes[0]
    assert tx["tx_hash"] == "74fb8886abb00e66b192172d5fca504337b11af3aac658979355cefe3d51818e"
    assert tx["height"] == 645013
    assert tx["tx"] == await btc.get_tx(tx["tx_hash"])


async def test_create_wallet(btc, tmp_path):
    wallet_path = os.path.join(str(tmp_path), "my_wallet")
    wallet = await btc.server.create(wallet_path=wallet_path)
    assert set(wallet.keys()) == {"seed", "path", "msg"}
    assert wallet["path"] == wallet_path
