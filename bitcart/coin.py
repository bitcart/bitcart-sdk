from collections.abc import Callable


class Coin:
    coin_name: str
    xpub_name: str
    friendly_name: str
    event_handlers: dict[str, Callable]
    xpub: str | None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coin):
            return NotImplemented
        return (self.coin_name, self.xpub) == (other.coin_name, other.xpub)
