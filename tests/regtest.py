import asyncio
import json
from decimal import Decimal

import pytest

from bitcart import errors

from .utils import data_check, run_shell

pytestmark = pytest.mark.asyncio

BTC_ADDRESS = (
    "bcrt1qttft7vh7w3er2akkpr4lu78z2ptdhgfxf739xf"  # can be got by run_shell(["newaddress"]) or regtest_wallet.add_request()
)


def use_default_fee(size, default_fee):
    return default_fee


def failing_fee(size, default_fee):
    return default_fee / 0


TEST_PARAMS = [
    (None, None, True),
    (None, None, False),
    (0.01, None, True),
    (0.01, None, False),
    (use_default_fee, None, True),
    (use_default_fee, None, False),
    (failing_fee, None, True),  # silent fallback to default fee if exception is raised
    (failing_fee, None, False),
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
async def confirmed_tx(btc, regtest_wallet, wait_for_balance):
    address = run_shell(["newaddress"])
    tx_hash = await regtest_wallet.pay_to(address, 0.1)
    run_shell(["newblock"])
    while not (history := await btc.server.getaddresshistory(address)) or history[0]["height"] <= 0:
        await asyncio.sleep(1)
    return address, tx_hash


def find_open_channel(channels):  # there is also BACKUP type
    for channel in channels:
        if channel["type"] == "CHANNEL" and channel["state"] == "OPEN":
            return channel


def find_channel_by_id(channels, channel_point):
    for channel in channels:
        if channel["channel_point"] == channel_point:
            return channel


async def wait_for_channel_opening(regtest_wallet, channel_point):
    while True:
        channels = await regtest_wallet.list_channels()
        channel = find_channel_by_id(channels, channel_point)
        await asyncio.sleep(1)
        if channel["state"] == "OPEN":
            break
    await asyncio.sleep(1)


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


def bitcoind_tx(tx_hash):
    tx = json.loads(run_shell(["gettx", tx_hash]), parse_float=Decimal)
    return {
        "version": tx["version"],
        "locktime": tx["locktime"],
        "inputs": [
            {
                "prevout_hash": tx_input["txid"],
                "prevout_n": tx_input["vout"],
                "coinbase": False,
                "nsequence": tx_input["sequence"],
                "scriptSig": tx_input["scriptSig"]["hex"],
                "witness": tx_input["txinwitness"],
            }
            for tx_input in tx["vin"]
        ],
        "outputs": [
            {
                "scriptpubkey": output["scriptPubKey"]["hex"],
                "address": output["scriptPubKey"]["address"],
                "value_sats": int(output["value"] * 100_000_000),
            }
            for output in tx["vout"]
        ],
    }


async def test_get_tx(btc, confirmed_tx):
    address, tx_hash = confirmed_tx
    info = await btc.server.get_transaction(tx_hash)
    assert info == {**bitcoind_tx(tx_hash), "confirmations": 1}
    assert {"address": address, "value_sats": 10_000_000} in [
        {"address": output["address"], "value_sats": output["value_sats"]} for output in info["outputs"]
    ]
    assert await btc.server.get_transaction(tx_hash, use_spv=True) == info


async def test_get_address(btc, confirmed_tx):
    address, tx_hash = confirmed_tx
    history = await btc.server.getaddresshistory(address)
    assert history == [{"tx_hash": tx_hash, "height": int(run_shell(["txheight", tx_hash]))}]


async def test_connect(regtest_wallet, regtest_node_id):
    with pytest.raises(errors.InvalidNodeIDError):
        await regtest_wallet.connect("")
    with pytest.raises(errors.InvalidNodeIDError):
        await regtest_wallet.connect(regtest_node_id.split("@")[1])
    assert await regtest_wallet.connect(regtest_node_id)


async def test_open_channel(regtest_wallet, regtest_node_id):
    # works only with nonlocal balances
    result = await regtest_wallet.open_channel(regtest_node_id, 0.1)
    assert isinstance(result, str)
    assert len(result) == 66
    assert ":" in result
    splitted = result.split(":")
    assert len(splitted) == 2
    int(splitted[1])  # integer
    run_shell(["newblocks", "3"])
    await wait_for_channel_opening(regtest_wallet, result)


async def test_list_peers(regtest_wallet, regtest_node_id):  # running on regtest to ensure we always have a peer connected
    peers = await regtest_wallet.list_peers()
    assert len(peers) > 0
    peer = peers[0]
    assert peer.keys() == {"node_id", "address", "initialized", "features", "channels"}
    data_check(peer, "initialized", bool)
    assert peer["node_id"] == regtest_node_id.split("@")[0]
    data_check(peer, "address", str)
    data_check(peer, "features", str)
    data_check(peer, "channels", list, 0)


async def test_list_channels(regtest_wallet, regtest_node_id):
    pubkey = regtest_node_id.split("@")[0]
    result = await regtest_wallet.list_channels()
    assert isinstance(result, list)
    assert len(result) > 0
    channel = find_open_channel(result)
    assert "short_channel_id" in channel
    assert isinstance(channel["short_channel_id"], str) or channel["short_channel_id"] is None
    data_check(channel, "channel_id", str, 64)
    data_check(channel, "channel_point", str, 66)
    data_check(channel, "peer_state", str)
    assert channel["peer_state"] == "GOOD"
    assert channel["state"] == "OPEN"
    assert channel["remote_pubkey"] == pubkey
    assert channel["local_balance"] == 10000000
    assert channel["remote_balance"] == 0
    data_check(channel, "local_reserve", int)
    data_check(channel, "remote_reserve", int)
    data_check(channel, "local_unsettled_sent", int)
    data_check(channel, "remote_unsettled_sent", int)
    assert channel["local_reserve"] == channel["remote_reserve"] == 100000
    assert channel["local_unsettled_sent"] == channel["remote_unsettled_sent"] == 0


async def test_lnpay(regtest_wallet, regtest_node):
    with pytest.raises(errors.InvalidLightningInvoiceError):
        assert not await regtest_wallet.lnpay("")
    invoice = (await regtest_node.add_invoice(0.01))["lightning_invoice"]
    response = await regtest_wallet.lnpay(invoice)
    assert isinstance(response, dict)
    assert response.keys() == {"payment_hash", "success", "preimage", "log"}
    data_check(response, "payment_hash", str)
    assert response["success"]
    data_check(response, "preimage", str)
    data_check(response, "log", list, 1)


async def test_close_channel(regtest_wallet):
    channels = await regtest_wallet.list_channels()
    channel_id = find_open_channel(channels)["channel_point"]
    assert isinstance(await regtest_wallet.close_channel(channel_id), str)
