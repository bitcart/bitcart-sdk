"""Test that Coin class methods are abstract, and test module loading
coin fixture is the abstract coin class tested
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_help(coin):
    with pytest.raises(NotImplementedError):
        await coin.help()
