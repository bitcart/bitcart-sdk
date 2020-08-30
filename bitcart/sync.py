# Thanks to https://github.com/pyrogram/pyrogram/blob/master/pyrogram/sync.py for most of the implementation
import asyncio
import functools
import inspect
import threading

from .coins import COINS
from .manager import APIManager
from .providers.jsonrpcrequests import RPCProxy


def async_to_sync_wraps(function):
    async def consume_generator(coroutine):
        return [i async for i in coroutine]

    @functools.wraps(function)
    def async_to_sync_wrap(*args, **kwargs):
        loop = asyncio.get_event_loop()
        coroutine = function(*args, **kwargs)

        if loop.is_running():
            if threading.current_thread() is threading.main_thread():
                return coroutine
            else:
                if inspect.iscoroutine(coroutine):
                    return asyncio.run_coroutine_threadsafe(coroutine, loop).result()

                if inspect.isasyncgen(coroutine):
                    return asyncio.run_coroutine_threadsafe(consume_generator(coroutine), loop).result()

        if inspect.iscoroutine(coroutine):
            return loop.run_until_complete(coroutine)

        if inspect.isasyncgen(coroutine):
            return loop.run_until_complete(consume_generator(coroutine))
        return coroutine

    return async_to_sync_wrap


def async_to_sync(obj, name):
    function = getattr(obj, name)

    setattr(obj, name, async_to_sync_wraps(function))


def wrap(source):
    for name in dir(source):
        method = getattr(source, name)

        if not name.startswith("_"):
            if inspect.iscoroutinefunction(method) or inspect.isasyncgenfunction(method):
                async_to_sync(source, name)


wrap(RPCProxy)

for source in COINS.values():
    wrap(source)

wrap(APIManager)
