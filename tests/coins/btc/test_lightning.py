from decimal import Decimal

import pytest

from bitcart import errors

from ...utils import assert_contains, data_check

pytestmark = pytest.mark.asyncio


async def test_node_id(btc_wallet_lightning):
    assert isinstance(await btc_wallet_lightning.node_id, str)


async def test_add_invoice(btc_wallet_lightning):
    invoice = await btc_wallet_lightning.add_invoice(0.5, "test description")
    assert isinstance(invoice, dict)
    assert_contains(
        {
            "is_lightning": True,
            "amount_BTC": Decimal("0.5"),
            "message": "test description",
            "status": 0,
            "status_str": "Expires in about 15 minutes",
            "amount_msat": 50000000000,
            "can_receive": False,
        },
        invoice,
    )
    data_check(invoice, "timestamp", int)
    data_check(invoice, "expiry", int)
    data_check(invoice, "rhash", str)
    data_check(invoice, "lightning_invoice", str)
    assert invoice["expiry"] == 900
    got_invoice = await btc_wallet_lightning.get_invoice(invoice["rhash"])
    assert got_invoice == invoice


async def test_connect(btc_wallet_lightning):
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet_lightning.connect("")
    with pytest.raises(errors.InvalidNodeIDError):
        assert not await btc_wallet_lightning.connect("172.81.181.3")  # taken from electrum sources
    assert await btc_wallet_lightning.connect(
        "0214382bdce7750dfcb8126df8e2b12de38536902dc36abcebdaeefdeca1df8284@172.81.181.3"
    )


async def test_wallet_methods_on_non_segwit(lightning_unsupported_wallet):
    request = await lightning_unsupported_wallet.add_request(0.5)
    assert request["is_lightning"] is False
    assert "lightning_invoice" not in request
    with pytest.raises(errors.LightningUnsupportedError):
        await lightning_unsupported_wallet.list_channels()  # unsupported on non-segwit wallets
