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
            "status": 0,
            "status_str": "Expires in 15 minutes",
            "amount_msat": 50000000000,
            "can_receive": False,
        }.items()
    )
    data_check(invoice, "timestamp", int)
    data_check(invoice, "expiration", int)
    data_check(invoice, "rhash", str)
    data_check(invoice, "lightning_invoice", str)
    assert invoice["expiration"] - invoice["timestamp"] == 900
    got_invoice = await btc_wallet.get_invoice(invoice["rhash"])
    assert got_invoice == invoice


async def test_connect(btc_wallet):
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet.connect("")
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet.connect("172.81.181.3")  # taken from electrum sources
    assert await btc_wallet.connect("0214382bdce7750dfcb8126df8e2b12de38536902dc36abcebdaeefdeca1df8284@172.81.181.3")


async def test_lightning_always_enabled(btc_wallet):
    await btc_wallet.set_config("lightning", False)
    assert await btc_wallet.node_id is not None  # env variables can't be overwritten


async def test_wallet_methods_on_non_segwit(lightning_unsupported_wallet):
    request = await lightning_unsupported_wallet.add_request(0.5)
    assert request["is_lightning"] is False
    assert "lightning_invoice" not in request
    with pytest.raises(errors.LightningUnsupportedError):
        await lightning_unsupported_wallet.list_channels()  # unsupported on non-segwit wallets
