import asyncio
import inspect
import json
import signal
import threading
import traceback
from decimal import Decimal
from typing import Any, Callable, NoReturn

from .logger import logger

CONVERT_RATE = 100000000


def convert_amount_type(amount: str) -> Decimal:
    """Convert amount from str to Decimal

    Args:
        amount (str): amount

    Returns:
        Decimal
    """
    if amount == "None":
        return Decimal("Nan")
    return Decimal(amount)


def satoshis(amount: Decimal) -> int:
    """Convert amount from bitcoins to satoshis

    Args:
        amount (Decimal): bitcoin amount

    Returns:
        int: same amount in satoshis
    """
    return int(amount * CONVERT_RATE)


def bitcoins(amount: int) -> Decimal:
    """Convert amount from satoshis to bitcoins

    Args:
        amount (int): amount in satoshis

    Returns:
        Decimal: amount in bitcoins
    """
    return Decimal(amount) / Decimal(CONVERT_RATE)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)  # pragma: no cover


def json_encode(obj: Any) -> Any:
    """json.dumps supporting Decimals

    Args:
        obj (Any): any object

    Returns:
        Any: return value of json.dumps
    """
    return json.dumps(obj, cls=CustomJSONEncoder)


async def call_universal(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Call a function: async or sync one. All passed arguments are passed to the function too

    Args:
        func (Callable): a function to call: either sync or async one

    Returns:
        Any: function execution result
    """
    try:
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result
    except Exception:
        logger.error(f"Error occured:\n{traceback.format_exc()}")


def _get_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        # NOTE: do NOT remove those 2 lines. Otherwise everything just hangs because of incorrect loop being used
        if threading.current_thread() is threading.main_thread():
            return asyncio.get_event_loop_policy().get_event_loop()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Useful utility for getting event loop. Acts like get_event_loop(), but also creates new event loop if needed

    Returns:
        asyncio.AbstractEventLoop: event loop
    """
    loop = _get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def idle() -> NoReturn:
    """Useful for making event loop idle in the main thread for other threads to work"""

    def signal_handler(*args, **kwargs):
        nonlocal is_idling

        is_idling = False

    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGABRT):
        signal.signal(s, signal_handler)

    is_idling = True

    while is_idling:
        await asyncio.sleep(1)
