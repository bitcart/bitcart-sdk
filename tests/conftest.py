import warnings
import pytest
from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB_MAINNET = "xprv9yFGRF1GzMMydx5AK9FEU3UhqcHAmKZNSy8EvfBtztGvNtSfB1jLnkAJa4cvc33DJEpY5JXMDAdhN3fyanJJsNGcXSNsojKxzeX7EPEe8rg"
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
    return BTC()
