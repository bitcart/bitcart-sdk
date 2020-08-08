import pytest
pytestmark = pytest.mark.asyncio


async def test_node_id(btc_wallet):
    assert await btc_wallet.node_id


async def test_add_invoice(btc_wallet):
    assert await btc_wallet.addinvoice(0.5, "test description")

