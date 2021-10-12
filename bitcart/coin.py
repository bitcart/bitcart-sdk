from typing import Callable, Dict, Optional


class Coin:
    coin_name: str
    friendly_name: str
    event_handlers: Dict[str, Callable]
    xpub: Optional[str]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coin):
            return NotImplemented
        return (self.coin_name, self.xpub) == (other.coin_name, other.xpub)
