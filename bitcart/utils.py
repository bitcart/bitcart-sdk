from decimal import Decimal


def convert_amount_type(amount: str) -> Decimal:
    """Convert amount from str to Decimal

    Args:
        amount (str): amount

    Returns:
        Decimal
    """
    return Decimal(amount)
