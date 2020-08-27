import pytest

from bitcart.errors import LightningDisabledError

pytestmark = pytest.mark.asyncio


async def test_node_id(btc_wallet):
    assert isinstance(await btc_wallet.node_id, str)


async def test_add_invoice(btc_wallet):
    assert isinstance(await btc_wallet.addinvoice(0.5, "test description"), str)


async def test_connect(btc_wallet):
    with pytest.raises(ValueError):
        assert not await btc_wallet.connect("")
    with pytest.raises(ValueError):
        assert not await btc_wallet.connect("172.81.181.3")  # taken from electrum sources
    assert await btc_wallet.connect("0214382bdce7750dfcb8126df8e2b12de38536902dc36abcebdaeefdeca1df8284@172.81.181.3")


async def test_lightning_disabled(btc_wallet):
    await btc_wallet.set_config("lightning", False)
    with pytest.raises(LightningDisabledError):
        await btc_wallet.node_id
    await btc_wallet.set_config("lightning", True)  # reset back
