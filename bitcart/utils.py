from decimal import Decimal

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
