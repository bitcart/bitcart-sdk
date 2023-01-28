# BitcartCC SDK

[![CircleCI](https://circleci.com/gh/bitcartcc/bitcart-sdk.svg?style=svg)](https://circleci.com/gh/bitcartcc/bitcart-sdk)
[![Codecov](https://img.shields.io/codecov/c/github/bitcartcc/bitcart-sdk?style=flat-square)](https://codecov.io/gh/bitcartcc/bitcart-sdk)
[![PyPI version](https://img.shields.io/pypi/v/bitcart.svg?style=flat-square)](https://pypi.python.org/pypi/bitcart/)
[![Read the Docs](https://img.shields.io/readthedocs/bitcart-sdk?style=flat-square)](https://sdk.bitcartcc.com)

This is a client library(wrapper) around BitcartCC daemon. It is used to simplify common commands.
Coins support(⚡ means lightning is supported):

- Bitcoin (⚡)
- Bitcoin Cash
- Monero
- Ethereum
- Binance coin (BNB)
- SmartBCH
- Polygon (MATIC)
- Tron (TRX)
- Ergon
- Litecoin (⚡)
- Globalboost (⚡)
- Groestlcoin (⚡)

Main focus is Bitcoin.

This library supports both asynchronous and synchronous usages.

You can call it's methods synchronously, like so:

```python
print(btc.help())
```

Or you can await it's methods when using from async functions:

```python
async def main():
    print(await btc.help())
```

Async callback functions for `@btc.on` are supported.

For more information [Read the Docs](https://sdk.bitcartcc.com)

## Release versioning

We follow a custom variant of semver:

`major.minor.feature.bugfix`

Where `major` is changed not frequently, and means significant changes to the SDK

`minor` means breaking changes

`feature` means adding new features without breaking existing APIs

`bugfix` means fixing bugs without breaking existing APIs

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Copyright and License

Copyright (C) 2019 MrNaif2018

Licensed under the [MIT license](LICENSE)
