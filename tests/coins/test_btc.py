"""Tests bitcoin methods implementation on mainnet, requires daemon to be running on localhost:5000

If this succeeds, most likely other coins will succeed too
"""
import pytest

pytestmark = pytest.mark.asyncio


async def test_help(btc):
    data = await btc.help()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "broadcast" in data
    assert "gettransaction" in data
    assert "help" in data
