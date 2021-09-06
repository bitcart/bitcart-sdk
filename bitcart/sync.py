# Thanks to https://github.com/pyrogram/pyrogram/blob/master/pyrogram/sync.py for most of the implementation
import asyncio
import functools
import inspect
import threading
from typing import Any, AsyncGenerator, Callable, List

from .coins import COINS
from .manager import APIManager
from .providers.jsonrpcrequests import RPCProxy


async def consume_generator(coroutine: AsyncGenerator) -> List[Any]:
    return [i async for i in coroutine]


def run_sync_ctx(coroutine: Any, loop: asyncio.AbstractEventLoop) -> Any:
    if inspect.iscoroutine(coroutine):
        return loop.run_until_complete(coroutine)

    if inspect.isasyncgen(coroutine):
        return loop.run_until_complete(consume_generator(coroutine))

    return coroutine


def run_from_another_thread(coroutine: Any, loop: asyncio.AbstractEventLoop) -> Any:
    if inspect.iscoroutine(coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result()

    if inspect.isasyncgen(coroutine):
        return asyncio.run_coroutine_threadsafe(consume_generator(coroutine), loop).result()


def async_to_sync_wraps(function: Callable, is_property: bool = False) -> Callable:
    main_loop = asyncio.get_event_loop()

    @functools.wraps(function)
    def async_to_sync_wrap(*args: Any, **kwargs: Any) -> Any:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = main_loop
        if is_property:
            coroutine = function.__get__(*args, **kwargs)  # type: ignore
        else:
            coroutine = function(*args, **kwargs)

        if loop.is_running():
            if threading.current_thread() is threading.main_thread():
                return coroutine
            else:
                return run_from_another_thread(coroutine, loop)

        try:
            return run_sync_ctx(coroutine, loop)
        except KeyboardInterrupt:
            shutdown_tasks(loop)
            raise
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())

    result = async_to_sync_wrap
    if is_property:
        result = property(result)  # type: ignore
    return result


def shutdown_tasks(loop: asyncio.AbstractEventLoop) -> None:
    tasks = asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True)
    tasks.add_done_callback(lambda t: loop.stop())
    tasks.cancel()
    while not tasks.done() and not loop.is_closed():
        loop.run_forever()


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
async_to_sync(COINS["BTC"], "spec", is_property=True)
async_to_sync(RPCProxy, "spec", is_property=True)
wrap(APIManager)
