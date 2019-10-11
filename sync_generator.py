import inspect
from typing import Any

import bitcart
from bitcart.providers.jsonrpcrequests import RPCProxy


def transform_sync(f: Any) -> str:
    filename = inspect.getfile(f)
    with open(filename) as f:
        source: str = f.read()
    source = (
        source.replace("async def", "def")
        .replace("await ", "")
        .replace("asyncio.sleep", "time.sleep")
        .replace("import asyncio\n", "")
        .replace("ASYNC = True", "ASYNC = False")
    )
    with open(filename, "w") as f:
        f.write(source)
    return source


def main() -> None:
    for name in bitcart.__all__:
        coin = getattr(bitcart, name)
        if issubclass(coin, bitcart.coin.Coin):
            transform_sync(coin)

    transform_sync(RPCProxy)


if __name__ == "__main__":
    main()
