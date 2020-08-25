import warnings

import pytest

from bitcart import BTC
from bitcart.coin import Coin

TEST_XPUB = "xprv9s21ZrQH143K3tZPHG8CbfZ7uUY5stdHmaEXeSqawGrZuAoBdHPgKHjdkfmHSdxDJSbo29JiU1PcWhzEsgFryqMHQfr2T5TWBPK8EqFjscZ"
REGTEST_XPUB = (
    "tprv8ZgxMBicQKsPepFfedsYPCgWioGqkbnRbMmprdTq3jFmRf7JQwe3Yo8DMBwttKFNLpp3xVx6Rfv7ChxZbkLXgnmb8hcq4uN2hVKLmCNcTpB"
)


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
    return BTC(xpub=TEST_XPUB)


@pytest.fixture
async def regtest_wallet():
    return BTC(xpub=REGTEST_XPUB)


@pytest.fixture
async def btc():
    with warnings.catch_warnings():  # to ignore no xpub passed warning
        warnings.simplefilter("ignore")
        btc_obj = BTC()
    return btc_obj
