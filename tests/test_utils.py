import asyncio
import multiprocessing
import threading
import time
from decimal import Decimal

import pytest

from bitcart.utils import bitcoins, convert_amount_type, get_event_loop, idle, satoshis

MAXSECONDS = 1


@pytest.mark.parametrize("btc,expected", [(0.1, 10000000), (1, 100000000), (0.00000001, 1), (5, 500000000)])
def test_satoshis(btc, expected):
    result = satoshis(btc)
    assert isinstance(result, int)
    assert result == expected


@pytest.mark.parametrize("sats,expected", [(10000000, "0.1"), (100000000, "1"), (1, "0.00000001"), (500000000, "5")])
def test_bitcoins(sats, expected):
    result = bitcoins(sats)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


def test_convertability():
    assert bitcoins(satoshis(1)) == 1


def test_convert_amount_type():
    assert convert_amount_type("1") == Decimal("1")
    assert convert_amount_type("None").is_nan()


@pytest.mark.asyncio
async def test_decimal_sending(btc_wallet):
    amount = Decimal("0.5")
    req = await btc_wallet.add_request(amount)  # ensures that it is possible to pass decimal
    assert req[btc_wallet.amount_field] == amount


def test_get_event_loop():
    def inner():
        loop = get_event_loop()
        assert isinstance(loop, asyncio.AbstractEventLoop)

    thread = threading.Thread(target=inner)
    thread.start()
    thread.join()
    loop = get_event_loop()
    assert isinstance(loop, asyncio.AbstractEventLoop)
    loop.close()
    loop2 = get_event_loop()
    assert loop is not loop2


def test_idle():
    def inner(called):
        idle()
        called.value = True

    called = multiprocessing.Value("b", False)
    process = multiprocessing.Process(target=inner, args=(called,))
    process.start()
    total = 0
    while not called.value:
        time.sleep(0.1)
        total += 0.1
        if total >= MAXSECONDS:
            break
    process.terminate()
    process.join()
    assert called.value
