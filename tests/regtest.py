import asyncio

import pytest

from bitcart import errors

from .utils import data_check, run_shell

pytestmark = pytest.mark.asyncio

BTC_ADDRESS = (
    "bcrt1qe0ppfnuz6wjw3vn8jefn8p4fxmyn7tqxkjt557"  # can be got by run_shell(["newaddress"]) or regtest_wallet.add_request()
)

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


@pytest.fixture
async def wait_for_utxos(regtest_wallet):
    while True:
        utxos = [utxo for utxo in await regtest_wallet.server.listunspent() if utxo["height"] != -2]
        # ensure we have nonlocal utxos to use to open channel
        if len(utxos) == 0:
            await asyncio.sleep(1)
        else:
            break


def check_tx(tx, broadcast):
    assert isinstance(tx, str)
    if broadcast:
        assert len(tx) == 64
    # if it is not broadcast, it returns raw transaction


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


async def test_open_channel(regtest_wallet, regtest_node_id, wait_for_utxos):
    # works only with nonlocal balances
    result = await regtest_wallet.open_channel(regtest_node_id, 0.002)
    assert isinstance(result, str)
    assert len(result) == 66
    assert ":" in result
    splitted = result.split(":")
    assert len(splitted) == 2
    int(splitted[1])  # integer
    run_shell(["newblocks", "3"])


async def test_list_channels(regtest_wallet, regtest_node_id):
    pubkey = regtest_node_id.split("@")[0]
    result = await regtest_wallet.list_channels()
    assert isinstance(result, list)
    assert len(result) > 0
    channel = result[-1]  # last channel is last in the list
    assert "short_channel_id" in channel
    assert isinstance(channel["short_channel_id"], str) or channel["short_channel_id"] is None
    data_check(channel, "channel_id", str, 64)
    data_check(channel, "channel_point", str, 66)
    data_check(channel, "peer_state", str)
    assert channel["peer_state"] == "GOOD"
    data_check(channel, "state", str)
    assert channel["remote_pubkey"] == pubkey
    assert channel["local_balance"] == 200000
    assert channel["remote_balance"] == 0
    data_check(channel, "local_reserve", int)
    data_check(channel, "remote_reserve", int)
    data_check(channel, "local_unsettled_sent", int)
    data_check(channel, "remote_unsettled_sent", int)
    assert channel["local_reserve"] == channel["remote_reserve"] == 2000
    assert channel["local_unsettled_sent"] == channel["remote_unsettled_sent"] == 0


async def test_lnpay(regtest_wallet):
    with pytest.raises(errors.InvalidLightningInvoiceError):
        assert not await regtest_wallet.lnpay("")
    response = await regtest_wallet.lnpay((await regtest_wallet.add_invoice(0.1))["invoice"])
    assert isinstance(response, dict)
    assert (
        response.items()
        > {
            "success": False,
            "preimage": None,
            "log": [["None", "N/A", "No path found"]],
        }.items()
    )
    data_check(response, "payment_hash", str)


async def test_close_channel(regtest_wallet):
    channels = await regtest_wallet.list_channels()
    channel_id = channels[-1]["channel_point"]  # last channel is last in the list
    assert isinstance(await regtest_wallet.close_channel(channel_id), str)
