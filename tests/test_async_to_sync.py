import inspect
import multiprocessing
import time
from threading import Thread

import pytest

from bitcart import BTC
from bitcart.utils import get_event_loop, idle

MAXSECONDS = 1


def test_sync_works(btc):
    assert isinstance(btc.help(), list)
    assert isinstance(btc.help(), list)  # ensure there are no loop mismatch error


def test_sync_works_with_properties(btc_wallet):
    assert isinstance(btc_wallet.node_id, str)  # property: special case


# single threaded
# synchronous main thread style
def sync_(client):
    sync_work(client)


# multi threaded
# synchronous main thread + synchronous thread style
def sync_sync(client):
    t = Thread(target=sync_work, args=(client,), daemon=True)
    t.start()
    idle()
    t.join()


# multi threaded
# synchronous main thread + asynchronous thread style
def sync_async(client):
    t = Thread(target=run, args=(async_work(client),), daemon=True)
    t.start()
    idle()
    t.join()


# single threaded
# asynchronous main thread style
async def async_(client):
    await async_work(client)


# multi threaded
# asynchronous main thread + synchronous thread style
async def async_sync(client):
    t = Thread(target=sync_work, args=(client,), daemon=True)
    t.start()
    await idle()
    t.join()


# multi threaded
# asynchronous main thread + asynchronous thread style
async def async_async(client):
    t = Thread(target=run, args=(async_work(client),), daemon=True)
    t.start()
    await idle()
    t.join()


def run(coro):
    loop = get_event_loop()
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def sync_work(client):
    print(client.help())
    called = True  # noqa: F841: injected via exec


async def async_work(client):
    print(await client.help())
    called = True  # noqa: F841: injected via exec


base_src = inspect.getsource(run) + "\n" + inspect.getsource(sync_work) + "\n" + inspect.getsource(async_work)

# NOTE: we use exec here because there is no easy way to test completely different execution models in one test run
# this way we achieve isolation


@pytest.mark.parametrize(
    "func",
    [
        "sync_",
        "sync_sync",
        "sync_async",
        "async_",
        "async_sync",
        "async_async",
    ],
)
def test_coding_style(func):
    src = inspect.getsource(globals()[func])
    call_code = f"{func}(btc)"
    if func.startswith("async_"):
        call_code = f"run({call_code})"
    full_src = f"{base_src}\n{src}\nbtc = BTC()\n{call_code}"
    global_vars = {
        "BTC": BTC,
        "Thread": Thread,
        "idle": idle,
        "get_event_loop": get_event_loop,
        "called": True,
    }

    def inner():
        exec(full_src, global_vars)

    process = multiprocessing.Process(target=inner)
    process.start()
    total = 0
    while not global_vars["called"]:
        time.sleep(0.1)
        total += 0.1
        if total >= MAXSECONDS:
            break
    process.kill()
    assert global_vars["called"]
