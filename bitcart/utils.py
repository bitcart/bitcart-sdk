import json
from decimal import Decimal
from typing import Any

CONVERT_RATE = 100000000


def convert_amount_type(amount: str) -> Decimal:
    """Convert amount from str to Decimal

    Args:
        amount (str): amount

    Returns:
        Decimal
    """
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
