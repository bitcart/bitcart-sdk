import warnings

import pytest

from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB_TESTNET = "tprv8ZgxMBicQKsPepFfedsYPCgWioGqkbnRbMmprdTq3jFmRf7JQwe3Yo8DMBwttKFNLpp3xVx6Rfv7ChxZbkLXgnmb8hcq4uN2hVKLmCNcTpB"


@pytest.fixture
async def coin():
    return Coin()


@pytest.fixture
async def btc_nowallet():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return BTC()


@pytest.fixture
async def btc_wallet():
    return BTC(xpub=TEST_XPUB_TESTNET)


@pytest.fixture
async def btc():
    with warnings.catch_warnings():  # to ignore no xpub passed warning
        warnings.simplefilter("ignore")
        btc_obj = BTC()
    return btc_obj


@pytest.fixture(autouse=True)
async def setup_btc_wallet(btc_wallet):
    await btc_wallet.set_config("lightning", True)
