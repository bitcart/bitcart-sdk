from decimal import Decimal

import pytest

from bitcart import errors

from ...utils import data_check

pytestmark = pytest.mark.asyncio


async def test_node_id(btc_wallet):
    assert isinstance(await btc_wallet.node_id, str)


async def test_add_invoice(btc_wallet):
    invoice = await btc_wallet.add_invoice(0.5, "test description")
    assert isinstance(invoice, dict)
    assert (
        invoice.items()
        > {
            "is_lightning": True,
            "amount_BTC": Decimal("0.5"),
            "message": "test description",
            "expiration": 900,
            "status": 0,
            "status_str": "Expires in 15 minutes",
            "amount_msat": 50000000000,
            "can_receive": False,
        }.items()
    )
    data_check(invoice, "timestamp", int)
    data_check(invoice, "rhash", str)
    data_check(invoice, "invoice", str)
    got_invoice = await btc_wallet.get_invoice(invoice["rhash"])
    assert got_invoice == invoice


async def test_connect(btc_wallet):
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet.connect("")
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet.connect("172.81.181.3")  # taken from electrum sources
    assert await btc_wallet.connect("0214382bdce7750dfcb8126df8e2b12de38536902dc36abcebdaeefdeca1df8284@172.81.181.3")


async def test_list_peers(btc_wallet):
    res1 = await btc_wallet.list_peers()
    res2 = await btc_wallet.list_peers(True)
    assert isinstance(res1, list)
    assert isinstance(res2, list)
    assert len(res1) >= 0
    assert len(res2) >= 0
    peer = res1[0]
    assert peer.keys() == {"node_id", "address", "initialized", "features", "channels"}
    data_check(peer, "initialized", bool)
    data_check(peer, "node_id", str, 66)
    data_check(peer, "address", str)
    data_check(peer, "features", str)
    assert "LnFeatures." in peer["features"]
    data_check(peer, "channels", list, 0)


async def test_lightning_always_enabled(btc_wallet):
    await btc_wallet.set_config("lightning", False)
    assert await btc_wallet.node_id is not None  # env variables can't be overwritten


async def test_wallet_methods_on_non_segwit(lightning_unsupported_wallet):
    with pytest.raises(errors.LightningUnsupportedError):
        await lightning_unsupported_wallet.list_channels()  # unsupported on non-segwit wallets
