from decimal import Decimal

import pytest

pytestmark = pytest.mark.asyncio


async def test_balance(btc_wallet):
    attrs = ["confirmed", "unconfirmed", "unmatured", "lightning"]
    balance = await btc_wallet.balance()
    for attr in attrs:
        assert balance[attr] >= 0
        assert isinstance(balance[attr], Decimal)


async def test_history(btc_wallet):
    history = await btc_wallet.history()
    assert isinstance(history["summary"], dict)
    assert isinstance(history["transactions"], list)


async def test_payment_request(btc_wallet):
    # request1
    request1_amount = "0.5"
    request1 = await btc_wallet.addrequest(request1_amount)
    assert request1[btc_wallet.amount_field] == request1["amount_BTC"] == Decimal(request1_amount)
    # request2
    request2_amount, request2_desc = "0.6", "test description"
    request2 = await btc_wallet.addrequest(request2_amount, request2_desc)
    assert request2["amount_BTC"] == Decimal(request2_amount)
    assert request2["memo"] == request2_desc
    # get request2
    response2 = await btc_wallet.getrequest(request2["address"])
    assert response2["amount_BTC"] == Decimal(request2_amount)
    assert response2["memo"] == request2_desc


async def test_insufficient_funds_pay(btc_wallet):
    with pytest.raises(ValueError):
        await btc_wallet.pay_to("2MzEqRRjMwECrZRH9fg5BDsa11SWsKSCE95", 0.1)


@pytest.mark.skip(reason="TODO: need a way having a wallet with sufficient fund")
@pytest.mark.parametrize(
    "fee,feerate,broadcast",
    [
        (None, None, True),
        (None, None, False),
        (1e-06, None, True),
        (1e-06, None, True),
        (lambda size: size / 4, None, True),
        (lambda size: size / 4, None, False),
        (None, 1, False),
        (None, 1, False),
    ],
)
async def test_payment_to_single(btc_wallet, fee, feerate, broadcast):
    await btc_wallet.pay_to(
        "37NFX8KWAQbaodUG6pE1hNUH1dXgkpzbyZ", 0.1, fee=fee, feerate=feerate, broadcast=broadcast,
    )


@pytest.mark.skip(reason="TODO: need a way having a wallet with sufficient fund")
@pytest.mark.parametrize(
    "payload",
    [
        [("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1), ("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1)],
        [
            {"address": "1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", "amount": 0.1},
            {"address": "1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", "amount": 0.1},
        ],
    ],
)
async def test_payment_to_many(btc_wallet, payload):
    await btc_wallet.pay_to_many(payload)
