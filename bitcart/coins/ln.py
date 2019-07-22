# pylint: disable=import-error, invalid-sequence-index
from typing import Optional, Iterable, Union, Dict
from types import ModuleType
from .btc import BTC


class LN(BTC):
    coin_name = "LN"
    friendly_name = "Bitcoin(Lightning)"
    providers: Union[Iterable[str], Dict[str, ModuleType]] = [
        "jsonrpcrequests"]
    RPC_URL = "http://localhost:5001"

    def open_channel(self: 'LN', node_id: str,
                     amount: Union[int, float]) -> str:
        """Open lightning channel

        Open channel with node, returns string of format
        txid:output_index

        Args:
            self (LN): self
            node_id (str): id of node to open channel with
            amount (Union[int, float]): amount to open channel

        Returns:
            str: string of format txid:output_index
        """
        return self.server.open_channel(node_id, amount)  # type: ignore

    def addinvoice(self: 'LN',
                   amount: Union[int,
                                 float],
                   message: Optional[str] = "") -> str:
        """Create lightning invoice

        Create lightning invoice and return bolt invoice id

        Example:

        >>> a.addinvoice(0.5)
        'lnbc500m1pwnt87fpp5d60sykcjd2swk72t3g0njwmdytfe4fu65fz5v...'

        Args:
            self (LN): self
            amount (Union[int,float]): invoice amount
            message (Optional[str], optional): Invoice message. Defaults to "".

        Returns:
            str: bolt invoice id
        """
        return self.server.addinvoice(amount, message)  # type: ignore

    def balance(self) -> dict:
        """Get balance of wallet

        Lightning balance is in lightning key of the dictionary

        Example:

        >>> self.balance()
        {"confirmed": "0.00005", "unconfirmed": 0, "unmatured": 0, "lightning": 0}

        Returns:
            dict: It should return dict of balance statuses
        """
        data = super().balance()
        data['lightning'] = data.get('lightning', 0)
        return data

    def close_channel(self: 'LN', channel_id: str, force: bool = False) -> str:
        """Close lightning channel

        Close channel by channel_id got from open_channel, returns transaction id

        Args:
            self (LN): self
            channel_id (str): channel_id from open_channel
            force (bool): Create new address beyond gap limit, if no more addresses are available.

        Returns:
            str: tx_id of closed channel
        """
        return self.server.close_channel(channel_id, force)  # type: ignore
