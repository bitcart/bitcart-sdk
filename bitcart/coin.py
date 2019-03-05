import sys
import importlib

SYSTEM_PACKAGES=["electrum"]

class Coin:
    """Coins should reimplement some methods,
    and initialize coin-specific info.
    Required information is:
    coin_name str
    friendly_name str
    providers list
    For more info see the docs.
    """

    coin_name="Base"
    friendly_name="Base"
    providers=[]

    def __init__(self):
        # Initialize the providers.
        self.providers_new = {}
        for i in self.providers:
            if i not in SYSTEM_PACKAGES:
                self.providers_new[i] = importlib.import_module(".providers."+i,"bitcart")
            else:
                self.providers_new[i] = importlib.import_module(i)
        self.providers = self.providers_new
        del self.providers_new

    def get_tx(self, tx: str) -> dict:
        """Override this method for getting transaction info,
        leave the function signature the same.
        For example of required output see the docs
        """
        raise NotImplementedError()

    def get_address(self, address: str) -> list:
        """Override this method for getting address info,
        leave the function signature the same.
        For example of required output see the docs
        """
        raise NotImplementedError()

    def balance(self) -> dict:
        """Override this method to return dict of balances,
        exactly like this:
        >>> self.balance()
        {"confirmed": "0.00005", "unconfirmed": None, "unmatured": None}
        """
        raise NotImplementedError()
