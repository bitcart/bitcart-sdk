import asyncio

import pytest

from .utils import run_shell

pytestmark = pytest.mark.asyncio

BTC_ADDRESS = "mjHXzpMTjhLePAdWgoesdhqEzCCRh6mwkJ"  # can be got by run_shell(["newaddress"]) or regtest_wallet.addrequest()

TEST_PARAMS = [
    (None, None, True),
    (None, None, False),
    (0.01, None, True),
    (0.01, None, False),
    (lambda size, default_fee: default_fee, None, True),
    (lambda size, default_fee: default_fee, None, False),
    (lambda size, default_fee: default_fee / 0, None, True),  # silent fallback to default fee if exception is raised
    (lambda size, default_fee: default_fee / 0, None, False),
    (None, 5, True),
    (None, 5, False),
]


def setup_module(module):
    run_shell(["startup", "1", BTC_ADDRESS])  # make blockchain mature and add funds


@pytest.fixture
async def wait_for_balance(regtest_wallet):
    while True:
        balance = await regtest_wallet.balance()
        balance = max(balance["confirmed"], balance["unconfirmed"])
        if balance < 1:
            await asyncio.sleep(1)
        else:
            break


def check_tx(tx, broadcast):
    if broadcast:
        assert isinstance(tx, str)
        assert len(tx) == 64
    else:
        assert isinstance(tx, dict)
        assert set(tx.keys()) == {"hex", "complete", "final"}
        assert isinstance(tx["hex"], str)
        assert isinstance(tx["complete"], bool)
        assert isinstance(tx["final"], bool)


@pytest.mark.parametrize("fee,feerate,broadcast", TEST_PARAMS)
async def test_payment_to_single(regtest_wallet, fee, feerate, broadcast, wait_for_balance):
    check_tx(
        await regtest_wallet.pay_to(
            "bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz", 0.1, fee=fee, feerate=feerate, broadcast=broadcast,
        ),
        broadcast,
    )


@pytest.mark.parametrize("fee,feerate,broadcast", TEST_PARAMS)
async def test_payment_to_many(regtest_wallet, fee, feerate, broadcast, wait_for_balance):
    print(regtest_wallet.xpub)
    check_tx(
        await regtest_wallet.pay_to_many(
            [("bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz", 0.1), ("bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz", 0.1)],
            fee=fee,
            feerate=feerate,
            broadcast=broadcast,
        ),
        broadcast,
    )
    check_tx(
        await regtest_wallet.pay_to_many(
            [
                {"address": "bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz", "amount": 0.1},
                {"address": "bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz", "amount": 0.1},
            ],
            fee=fee,
            feerate=feerate,
            broadcast=broadcast,
        ),
        broadcast,
    )
