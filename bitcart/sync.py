# Thanks to https://github.com/pyrogram/pyrogram/blob/master/pyrogram/sync.py for most of the implementation
import asyncio
import functools
import inspect
import threading
from typing import Any, AsyncGenerator, Callable, Coroutine, List, Union

from .coins import COINS
from .manager import APIManager
from .providers.jsonrpcrequests import RPCProxy


def async_to_sync_wraps(function: Callable, is_property: bool = False) -> Callable:
    async def consume_generator(coroutine: AsyncGenerator) -> List[Any]:
        return [i async for i in coroutine]

    @functools.wraps(function)
    def async_to_sync_wrap(*args: Any, **kwargs: Any) -> Union[Coroutine, Any]:
        loop = asyncio.get_event_loop()
        if is_property:
            coroutine = function.__get__(*args, **kwargs)  # type: ignore
        else:
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

    result = async_to_sync_wrap
    if is_property:
        result = property(result)  # type: ignore
    return result


def async_to_sync(obj: object, name: str, is_property: bool = False) -> None:
    function = getattr(obj, name)

    setattr(obj, name, async_to_sync_wraps(function, is_property=is_property))


def wrap(source: object) -> None:
    for name in dir(source):
        method = getattr(source, name)

        if not name.startswith("_"):
            if inspect.iscoroutinefunction(method) or inspect.isasyncgenfunction(method):
                async_to_sync(source, name)


wrap(RPCProxy)

for source in COINS.values():
    wrap(source)

async_to_sync(COINS["BTC"], "node_id", is_property=True)  # special case: property
wrap(APIManager)
