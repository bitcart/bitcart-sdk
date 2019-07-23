import importlib
from typing import Dict, Iterable, Union
from types import ModuleType
SYSTEM_PACKAGES = ["electrum"]


class Coin:
    """Coins should reimplement some methods,
    and initialize coin-specific info.
    Required information is:
    coin_name str
    friendly_name str
    providers list
    For more info see the docs.
    """

    coin_name = "Base"
    friendly_name = "Base"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = []

    def __init__(self: 'Coin') -> None:
        # Initialize the providers.
        self.providers_new: Dict[str, ModuleType] = {}
        for i in self.providers:
            if i not in SYSTEM_PACKAGES:
                self.providers_new[i] = importlib.import_module(
                    ".providers." + i, "bitcart")
            else:
                self.providers_new[i] = importlib.import_module(i)
        self.providers = self.providers_new
        del self.providers_new

    def help(self) -> list:
        """Get help

        Returns a list of all available RPC methods

        Raises:
            NotImplementedError: Implement in your subclass

        Returns:
            list: RPC methods list
        """
        raise NotImplementedError()

    def get_tx(self, tx: str) -> dict:
        """Get transaction information

        Given tx hash of transaction, return full information as dictionary

        Example:

        >>> c.get_tx("54604b116b28124e31d2d20bbd4561e6f8398dca4b892080bffc8c87c27762ba")
        {'partial': False, 'version': 2, 'segwit_ser': True, 'inputs': [{'prevout_hash': 'xxxx',...

        Args:
            tx (str): tx_hash

        Raises:
            NotImplementedError: Implement in your subclass

        Returns:
            dict: transaction info
        """
        raise NotImplementedError()

    def get_address(self, address: str) -> list:
        """Get address history

        This method should return list of transaction informations for specified address

        Example:

        >>> c.get_address("31smpLFzLnza6k8tJbVpxXiatGjiEQDmzc")
        [{'tx_hash': '7854bdf4c4e27276ecc1fb8d666d6799a248f5e81bdd58b16432d1ddd1d4c332', 'height': 581878, 'tx': {'partial': False,...

        Args:
            address (str): address to get transactions for

        Raises:
            NotImplementedError: Override this method in subclass

        Returns:
            list: List of transactions
        """
        raise NotImplementedError()

    def balance(self) -> dict:
        """Get balance of wallet

        Example:

        >>> self.balance()
        {"confirmed": "0.00005", "unconfirmed": 0, "unmatured": 0}

        Raises:
            NotImplementedError: Implement in your subclass

        Returns:
            dict: It should return dict of balance statuses
        """
        raise NotImplementedError()
