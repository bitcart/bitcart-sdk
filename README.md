# bitcart-sdk
[![CircleCI](https://circleci.com/gh/MrNaif2018/bitcart-sdk.svg?style=svg)](https://circleci.com/gh/MrNaif2018/bitcart-sdk)
[![PyPI version](https://img.shields.io/pypi/v/bitcart.svg)](https://pypi.python.org/pypi/bitcart/) 
[![Documentation Status](https://readthedocs.org/projects/bitcart-sdk/badge/?version=latest)](https://bitcart-sdk.readthedocs.io/en/latest/?badge=latest)


This is a async version of client library(wrapper) around bitcart daemon. It is used to simplify common commands. New coins may be added soon.

APIs are the same, just use async and await. poll_updates method is still blocking as it needs to run forever. 
Async callback functions for @btc.notify now supported.

For more information [Read the Docs](https://bitcart-sdk.readthedocs.io/en/latest/)
