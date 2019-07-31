# pylint: disable=import-error, invalid-sequence-index
import sys
import time
import logging
from typing import Optional, Iterable, Union, Dict, SupportsInt, SupportsFloat, Callable, TYPE_CHECKING
from types import ModuleType
import warnings
from ..coin import Coin

if TYPE_CHECKING:
    import requests


class BTC(Coin):
    coin_name = "BTC"
    friendly_name = "Bitcoin"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = [
        "jsonrpcrequests"]
    RPC_URL = "http://localhost:5000"
    RPC_USER = "electrum"
    RPC_PASS = "electrumz"

    def __init__(
            self: "BTC",
            rpc_url: Optional[str] = None,
            rpc_user: Optional[str] = None,
            rpc_pass: Optional[str] = None,
            xpub: Optional[str] = None,
            session: Optional['requests.Session'] = None):
        super().__init__()
        if not xpub:
            warnings.warn(
                "Xpub not provided. Not all functions will be available.",
                stacklevel=2)
        self.rpc_url = rpc_url or self.RPC_URL
        self.rpc_user = rpc_user or self.RPC_USER
        self.rpc_pass = rpc_pass or self.RPC_PASS
        self.xpub = xpub
        self.notify_func: Optional[Callable] = None
        self.server = self.providers["jsonrpcrequests"].RPCProxy(  # type: ignore
            self.rpc_url, self.rpc_user, self.rpc_pass, self.xpub, session=session)

    def help(self) -> list:
        return self.server.help()  # type: ignore

    def get_tx(self, tx: str) -> dict:
        return self.server.get_transaction(tx)  # type: ignore

    def get_address(self, address: str) -> list:
        out: list = self.server.getaddresshistory(address)
        for i in out:
            i["tx"] = self.get_tx(i["tx_hash"])
        return out

    def balance(self) -> dict:
        data = self.server.getbalance()
        return {"confirmed": data.get("confirmed", 0),
                "unconfirmed": data.get("unconfirmed", 0),
                "unmatured": data.get("unmatured", 0)}

    def addrequest(self: 'BTC',
                   amount: Union[int, float],
                   description: str = "",
                   expire: Union[int, float] = 15) -> dict:
        """Add invoice

        Create an invoice and request amount in BTC, it will expire by parameter provided.
        If expire is None, it will last forever.

        Example:

        >>> c.addrequest(0.5, "My invoice", 20)
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': 'xxx',...

        Args:
            self (BTC): self
            amount (Union[int, float]): amount to open invoice
            description (str, optional): Description of invoice. Defaults to "".
            expire (Union[int, float], optional): The time invoice will expire in. Defaults to 15.

        Returns:
            dict: Invoice data
        """
        expiration = 60 * expire if expire else None
        return self.server.addrequest(  # type: ignore
            amount=amount,
            memo=description,
            expiration=expiration,
            force=True)

    def getrequest(self: 'BTC', address: str) -> dict:
        """Get invoice info

        Get invoice information by address got from addrequest

        Example:

        >>> c.getrequest("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ")
        {'time': 1562762334, 'amount': 50000000, 'exp': 1200, 'address': '1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ',...

        Args:
            self (BTC): self
            address (str): address of invoice

        Returns:
            dict: Invoice data
        """
        return self.server.getrequest(address)  # type: ignore

    def history(self: 'BTC') -> dict:
        """Get transaction history of wallet

        Example:

        >>> c.history()
        {'summary': {'end_balance': '0.', 'end_date': None, 'from_height': None, 'incoming': '0.00185511',...

        Args:
            self (BTC): self

        Returns:
            dict: dictionary with some data, where key transactions is list of transactions
        """
        return self.server.history()  # type: ignore

    def notify(
            self: 'BTC',
            f: Optional[Callable] = None,
            skip: bool = True) -> Callable:
        """Notify decorator

        Notify of incoming transactions on wallet

        Example usage can be found on main page of docs.

        Args:
            self (BTC): self
            f (Optional[Callable], optional): Function to call
            skip (bool, optional): Either to skip old transactions or not. Defaults to True.

        Returns:
            Callable: It is a decorator
        """
        def wrapper(f: Callable) -> Callable:
            self.notify_func = f
            self.skip = skip
            return f
        if f:
            wrapper(f)
            return f
        else:
            return wrapper

    def poll_updates(self: 'BTC', timeout: Union[int, float] = 2) -> None:
        """Poll updates

        Poll daemon for new transactions in wallet,
        this will block forever in while True loop checking for new transactions

        Example can be found on main page of docs

        Args:
            self (BTC): self
            timeout (Union[int, float], optional): seconds to wait before requesting transactions again. Defaults to 2.

        Raises:
            AttributeError: If no function was marked with @notify decorator

        Returns:
            None: This function runs forever
        """
        if not self.notify_func:
            raise AttributeError(
                "No notification function set. Set it with @notify decorator")
        self.server.register_notify(skip=self.skip)
        while True:
            try:
                data = self.server.notify_tx()
            except Exception as err:
                logging.error(err)
                time.sleep(timeout)
                continue
            if data:
                self.notify_func(data)
            time.sleep(timeout)

    def pay_to(self: 'BTC', address: str, amount: float) -> str:
        """Pay to address in bitcoins

        This function creates bitcoin transaction, your wallet must have sufficent balance
        and address must exist

        Args:
            self (BTC): self
            address (str): address where to send BTC
            amount (float): amount of bitcoins to send

        Raises:
            ValueError: If address or amount is invalid or in other cases

        Returns:
            str: tx hash of ready transaction
        """
        tx_data = self.server.payto(address, amount)
        return self.server.broadcast(tx_data)  # type: ignore

    def rate(self: 'BTC') -> float:
        """Get bitcoin price in USD

        It uses the same method as electrum wallet gets exchange rate-via different payment providers

        Example:

        >>> c.rate()
        9878.527

        Args:
            self (BTC): self

        Returns:
            float: price of 1 bitcoin in USD
        """
        return self.server.exchange_rate()  # type: ignore
