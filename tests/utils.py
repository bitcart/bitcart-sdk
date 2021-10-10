import asyncio
import subprocess
import time

from bitcart.utils import call_universal


def run_shell(args=[], timeout=30):
    process = subprocess.Popen(["tests/regtest/regtest.sh"] + args, stdout=subprocess.PIPE, universal_newlines=True)
    process.wait(timeout=timeout)
    assert process.returncode == 0
    return process.stdout.read().strip()


def data_check(data, key, check_type, length=None):
    assert key in data
    assert isinstance(data[key], check_type)
    if length:
        assert len(data[key]) == length


async def wait_timeout(func, predicate, callback, timeout=10):
    start = time.time()
    while True:
        data = await call_universal(func)
        if await call_universal(predicate, data):
            await call_universal(callback, data)
            break
        if time.time() - start >= timeout:
            raise Exception("Timeout")
        await asyncio.sleep(0.1)
