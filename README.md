# bitcart-sdk
[![CircleCI](https://circleci.com/gh/MrNaif2018/bitcart-sdk.svg?style=svg)](https://circleci.com/gh/MrNaif2018/bitcart-sdk)
[![PyPI version](https://img.shields.io/pypi/v/bitcart-async.svg)](https://pypi.python.org/pypi/bitcart-async/) 
[![Documentation Status](https://readthedocs.org/projects/bitcart-sdk/badge/?version=latest)](https://bitcart-sdk.readthedocs.io/en/latest/?badge=latest)


This is a async version of client library(wrapper) around bitcart daemon. It is used to simplify common commands. New coins may be added soon.

APIs are the same, just use async and await. poll_updates method is still blocking as it needs to run forever. 
Async callback functions for @btc.on now supported.
The only main change is that you must use async with context manager or manually close connections, like so:

```
async with btc:
    print(await btc.balance())
```

Or, if you don't use context managers, close it manually:

```
print(await btc.balance())
await btc.close()
```

For more information [Read the Docs](https://bitcart-sdk.readthedocs.io/en/latest/)
