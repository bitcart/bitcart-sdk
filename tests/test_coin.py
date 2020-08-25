"""Test that Coin class methods are abstract, and test module loading
coin fixture is the abstract coin class tested
"""
import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("method,args", [("help", []), ("get_tx", ["test"]), ("get_address", ["address"]), ("balance", [])])
async def test_abstract(coin, method, args):
    with pytest.raises(NotImplementedError):
        await getattr(coin, method)(*args)
