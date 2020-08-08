import pytest
from bitcart.errors import LightningDisabledError

pytestmark = pytest.mark.asyncio


async def test_node_id(btc_wallet):
    assert (await btc_wallet.node_id, str)


async def test_add_invoice(btc_wallet):
    assert (await btc_wallet.addinvoice(0.5, "test description"), str)


async def test_lightning_disabled(btc_wallet):
    await btc_wallet.set_config("lightning", False)
    with pytest.raises(LightningDisabledError):
        await btc_wallet.node_id
