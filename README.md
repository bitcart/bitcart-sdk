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

This library supports both asynchronous and synchronous versions.
Use `bitcart` as a sync version(better for beginners), and `bitcart-async` for async version.

If you install from github, by default it is async.
Use:
```
ASYNC=false python setup.py install
```
For it to convert async version to sync and install that.
That process is done via ``sync_generator.py``.

For more information [Read the Docs](https://sdk.bitcartcc.com)

Async version's APIs are the same as sync, just use async and await.
Async callback functions for @btc.on now supported.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).