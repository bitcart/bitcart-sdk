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

    @property
    def node_id(self) -> str:
        """Get node id

        Electrum's lightning implementation itself is a lightning node,
        that way you can get a super light node, this method returns it's id

        Example:

        >>> a.node_id
        '030ff29580149a366bdddf148713fa808f0f4b934dccd5f7820f3d613e03c86e55'

        Returns:
            str: id of your node
        """
        return self.server.nodeid()  # type: ignore

    def lnpay(self, invoice: str) -> bool:
        """Pay lightning invoice

        Returns True on success, False otherwise

        Args:
            invoice (str): invoice to pay

        Returns:
            bool: success or not
        """
        return self.server.lnpay(invoice)  # type: ignore

    def connect(self, connection_string: str) -> bool:
        """Connect to lightning node
        
        connection string must respect format pubkey@ipaddress
        
        Args:
            connection_string (str): connection string
        
        Returns:
            bool: True on success, False otherwise
        """
        return self.server.add_peer(connection_string) # type: ignore

    def list_channels(self) -> list:
        """List all channels ever opened
        
        Possible channel statuses:
        OPENING, OPEN, CLOSED, DISCONNECTED

        Example:

        >>> a.server.list_channels()
        [{'local_htlcs': {'adds': {}, 'locked_in': {}, 'settles': {}, 'fails': {}}, 'remote_htlcs': ...

        Returns:
            list: list of channels
        """
        return self.server.list_channels() # type: ignore

    def history(self) -> dict:
        return self.server.onchain_history() # type: ignore
