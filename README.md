# bitcart-sdk
[![CircleCI](https://circleci.com/gh/MrNaif2018/bitcart-sdk.svg?style=svg)](https://circleci.com/gh/MrNaif2018/bitcart-sdk)
[![codecov](https://codecov.io/gh/MrNaif2018/bitcart-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/MrNaif2018/bitcart-sdk)
[![PyPI version](https://img.shields.io/pypi/v/bitcart.svg)](https://pypi.python.org/pypi/bitcart/)
[![Documentation Status](https://readthedocs.org/projects/bitcart-sdk/badge/?version=latest)](https://bitcart-sdk.readthedocs.io/en/latest/?badge=latest)


This is a client library(wrapper) around bitcart daemon. It is used to simplify common commands.
Coins support(⚡ means lightning is supported):
- Bitcoin(⚡)
- Litecoin(⚡)
- Gravity Zero(⚡)

Main focus is Bitcoin.

This library supports both asynchronous and synchronous versions.
Use bitcart as a sync version(better for beginners), and bitcart-async for async version.

If you install from github, by default it is async.
Use:
```
ASYNC=false python setup.py install
```
For it to convert async version to sync and install that.
That process is done via ``sync_generator.py``.

For more information [Read the Docs](https://bitcart-sdk.readthedocs.io/en/latest/)

Async version's APIs are the same as sync, just use async and await.
Async callback functions for @btc.on now supported.
