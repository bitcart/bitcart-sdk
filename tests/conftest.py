import asyncio
import warnings

import pytest

from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB = "xprv9yFGRF1GzMMydx5AK9FEU3UhqcHAmKZNSy8EvfBtztGvNtSfB1jLnkAJa4cvc33DJEpY5JXMDAdhN3fyanJJsNGcXSNsojKxzeX7EPEe8rg"


@pytest.yield_fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="session")
async def coin():
    return Coin()


@pytest.fixture(autouse=True, scope="session")
async def btc_nowallet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return BTC()


@pytest.fixture(autouse=True, scope="session")
async def btc():
    return BTC(xpub=TEST_XPUB)
