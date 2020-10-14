import pytest

from bitcart import errors
from bitcart.errors import LightningDisabledError

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
            "amount_BTC": "0.5",
            "message": "test description",
            "expiration": 3600,
            "status": 0,
            "status_str": "Expires in about 1 hour",
            "amount_msat": 50000000000,
            "can_receive": False,
        }.items()
    )
    data_check(invoice, "timestamp", int)
    data_check(invoice, "rhash", str)
    data_check(invoice, "invoice", str)


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
    assert len(res1) > 0
    assert len(res2) >= 0
    peer = res1[0]
    assert peer.keys() == {"node_id", "address", "initialized", "features", "channels"}
    data_check(peer, "initialized", bool)
    data_check(peer, "node_id", str, 66)
    data_check(peer, "address", str)
    data_check(peer, "features", str)
    assert "LnFeatures." in peer["features"]
    data_check(peer, "channels", list, 0)


async def test_lightning_disabled(btc_wallet):
    await btc_wallet.set_config("lightning", False)
    with pytest.raises(LightningDisabledError):
        await btc_wallet.node_id
    await btc_wallet.set_config("lightning", True)  # reset back


async def test_wallet_methods_on_non_segwit(lightning_unsupported_wallet):
    with pytest.raises(errors.LightningUnsupportedError):
        await lightning_unsupported_wallet.list_channels()  # unsupported on non-segwit wallets
