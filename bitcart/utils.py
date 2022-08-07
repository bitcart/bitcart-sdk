import inspect
import json
import traceback
from decimal import Decimal
from typing import Any, Callable, Union

from .logger import logger

CONVERT_RATE = 100000000


def convert_amount_type(amount: Union[str, Decimal]) -> Decimal:
    """Convert amount from str to Decimal

    Args:
        amount (Union[str, Decimal]): amount

    Returns:
        Decimal
    """
    if amount == "None":
        return Decimal("Nan")
    return Decimal(amount)


def satoshis(amount: Union[str, Decimal]) -> int:
    """Convert amount from bitcoins to satoshis

    Args:
        amount (Union[str, Decimal]): bitcoin amount

    Returns:
        int: same amount in satoshis
    """
    return int(convert_amount_type(amount) * CONVERT_RATE)


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
