from typing import Union
from decimal import Decimal


def convert_coin_value_type(amount: str, accurate: bool) -> Union[Decimal, float]:
    """Convert coin amount type from str to Decimal or float

    Args:
        amount (str): coin amount
        accurate (bool): Whether to return values harder to work with(decimals) or not very accurate floats. Defaults to False.

    Returns:
        Union[Decimal, float]
    """
    return Decimal(amount) if accurate else float(amount)
