import asyncio

import pytest

from bitcart import errors

from .utils import data_check, run_shell

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
    run_shell(["startup", "5", BTC_ADDRESS])  # make blockchain mature and add funds


@pytest.fixture
async def wait_for_balance(regtest_wallet):
    while True:
        balance = await regtest_wallet.balance()
        balance = balance["confirmed"] + balance["unconfirmed"]
        if balance < 5:
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
            "bcrt1qx4y7d5wt9cn585cqyxc7899khtz2dsl0qnufkz",
            0.1,
            fee=fee,
            feerate=feerate,
            broadcast=broadcast,
        ),
        broadcast,
    )


@pytest.mark.parametrize("fee,feerate,broadcast", TEST_PARAMS)
async def test_payment_to_many(regtest_wallet, fee, feerate, broadcast, wait_for_balance):
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


async def test_open_channel(regtest_wallet, wait_for_balance):
    await asyncio.sleep(
        5
    )  # works only at times at current electrum commit, sometimes helps # TODO: electrum 4.0.2 will fix this
    result = await regtest_wallet.open_channel(await regtest_wallet.node_id, 0.002)
    assert isinstance(result, str)
    assert len(result) == 66
    assert ":" in result
    splitted = result.split(":")
    assert len(splitted) == 2
    int(splitted[1])  # integer
    run_shell(["newblocks", "3"])


async def test_list_channels(regtest_wallet):
    node_id = await regtest_wallet.node_id
    pubkey = node_id.split("@")[0]
    result = await regtest_wallet.list_channels()
    assert isinstance(result, list)
    assert len(result) > 0
    channel = result[0]
    assert "channel_id" in channel
    assert isinstance(channel["channel_id"], str) or channel["channel_id"] is None
    data_check(channel, "full_channel_id", str, 64)
    data_check(channel, "channel_point", str, 66)
    data_check(channel, "state", str)
    assert channel["remote_pubkey"] == pubkey
    assert channel["local_balance"] == 200000
    assert channel["remote_balance"] == 0
    data_check(channel, "local_htlcs", dict)
    assert channel["local_htlcs"] == {
        "adds": {},
        "locked_in": {},
        "settles": {},
        "fails": {},
        "fee_updates": [[45000, {"1": 0, "-1": 0}]],
        "revack_pending": False,
        "next_htlc_id": 0,
        "ctn": 0,
    }
    data_check(channel, "remote_htlcs", dict)
    assert channel["remote_htlcs"] == {
        "adds": {},
        "locked_in": {},
        "settles": {},
        "fails": {},
        "fee_updates": [[45000, {"1": 0, "-1": 0}]],
        "revack_pending": False,
        "next_htlc_id": 0,
        "ctn": 0,
    }


async def test_lnpay(regtest_wallet):
    with pytest.raises(errors.InvalidLightningInvoiceError):
        assert not await regtest_wallet.lnpay("")
    with pytest.raises(errors.NoPathFoundError):
        assert await regtest_wallet.lnpay(await regtest_wallet.addinvoice(0.5))


@pytest.mark.skip("Fixed in next electrum version")
async def test_close_channel(regtest_wallet):
    channels = await regtest_wallet.list_channels()
    channel_id = channels[0]["channel_point"]
    assert isinstance(await regtest_wallet.close_channel(channel_id), str)
