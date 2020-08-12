from typing import Union
from decimal import Decimal


def convert_amount_type(amount: str, accurate: bool) -> Union[Decimal, float]:
    """Convert amount from str to Decimal or float

    Args:
        amount (str): amount
        accurate (bool): Whether to return values harder to work with (decimals) or not very accurate floats. Defaults to False.

    Returns:
        Union[Decimal, float]
    """
    return Decimal(amount) if accurate else float(amount)
