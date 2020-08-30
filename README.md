# BitcartCC SDK
[![CircleCI](https://circleci.com/gh/MrNaif2018/bitcart-sdk.svg?style=svg)](https://circleci.com/gh/MrNaif2018/bitcart-sdk)
[![Codecov](https://img.shields.io/codecov/c/github/MrNaif2018/bitcart-sdk?style=flat-square)](https://codecov.io/gh/MrNaif2018/bitcart-sdk)
[![PyPI version](https://img.shields.io/pypi/v/bitcart.svg?style=flat-square)](https://pypi.python.org/pypi/bitcart/)
[![Read the Docs](https://img.shields.io/readthedocs/bitcart-sdk?style=flat-square)](https://sdk.bitcartcc.com)


This is a client library(wrapper) around BitcartCC daemon. It is used to simplify common commands.
Coins support(⚡ means lightning is supported):
- Bitcoin(⚡)
- Bitcoin Cash
- Litecoin(⚡)
- Gravity Zero(⚡)
- Globalboost(⚡)

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


## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).