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

    def open_channel(self: 'LN', node_id: str, amount: Union[int, float]):
        return self.server.open_channel(node_id, amount)

    def addinvoice(self: 'LN', amount: Union[int, float], message: Optional[str] = ""):
        return self.server.addinvoice(amount, message)

    def balance(self) -> dict:
        data = super().balance()
        data['lightning'] = data.get('lightning', 0)
        return data

    def close_channel(self: 'LN', channel_id):
        return self.server.close_channel(channel_id)