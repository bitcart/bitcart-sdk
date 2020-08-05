# Contributing to BitcartCC SDK

Welcome, and thank you for your interest in contributing to BitcartCC SDK!

Our [central contributing guidelines](https://github.com/MrNaif2018/bitcart/blob/master/CONTRIBUTING.md) apply to all BitcartCC repositories.

Below are the instructions for setting up development environment with BitcartCC SDK.

## Setting up development environment

Some general advice can be found in our [central contributing guidelines](https://github.com/MrNaif2018/bitcart/wiki/How-to-Contribute#setting-up-development-environment).

Instructions:

```bash
git clone https://github.com/<<<your-github-account>>>/bitcart-sdk.git
cd bitcart-sdk
virtualenv env
source env/bin/activate
pip3 install -e .
pip3 install -r test-requirements.txt # for tests
```

Development version is async only, sync version is achieved by running sync_generator.py (WARNING: overrides source files).

From now on, development environment is ready.

Make sure to follow [our coding guidelines](https://github.com/MrNaif2018/bitcart/wiki/Coding-Guidelines) when developing.

# Thank You!

Your contributions to open source, large or small, make great projects like this possible. Thank you for taking the time to contribute.
