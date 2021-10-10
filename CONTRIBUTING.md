# Contributing to BitcartCC SDK

Welcome, and thank you for your interest in contributing to BitcartCC SDK!

Our [central contributing guidelines](https://github.com/bitcartcc/bitcart/blob/master/CONTRIBUTING.md) apply to all BitcartCC repositories.

Below are the instructions for setting up development environment with BitcartCC SDK.

## Setting up development environment

Some general advice can be found in our [central contributing guidelines](https://github.com/bitcartcc/bitcart/blob/master/CONTRIBUTING.md#setting-up-development-environment).

Instructions:

```bash
git clone https://github.com/<<<your-github-account>>>/bitcart-sdk.git
cd bitcart-sdk
virtualenv env
source env/bin/activate
pip3 install -e .
pip3 install -r test-requirements.txt # for tests
```

The library is async, sync version is supported by file `bitcart/sync.py` by wrapping all functions and returning coroutines or function results
based on context.

From now on, development environment is ready.

Make sure to follow [our coding guidelines](https://github.com/bitcartcc/bitcart/blob/master/CODING_STANDARDS.md) when developing.

This repository uses pre-commit hooks for better development experience. Install them with:

```
pre-commit install
```

It will run automatically on commits.

If you ever need to run the full pre-commit checks on all files, run:

```
pre-commit run --all-files
```

To run all checks before commiting (including tests), use `make` command.

## Running extended test suite

Some of the SDK tests require sending functionality. On bitcoin mainnet it is impossible to test it easily.

We use regtest bitcoin network for some tests, which can be found at `tests/regtest.py` file.

To run regtest test suite, you'll need to install bitcoind and Fulcrum.

It is not required, but recommended to run extended test suite before submitting a PR.

CI can run it for you if needed.

You can get Fulcrum from https://github.com/cculianu/Fulcrum/releases

Bitcoind installation instructions differ on different distros and OSes.

Here are installation instructions for ubuntu:

```bash
sudo add-apt-repository -y ppa:luke-jr/bitcoincore
sudo apt-get -qq update
sudo apt-get install -yq bitcoind
sudo apt-get -y install libsecp256k1-0
```

Before running extended test suite, start bitcoind and fulcrum. Each time regtest network is recreated.

Run `make bitcoind` to start bitcoind, `make fulcrum` to start fulcrum.

After that, stop your mainnet BitcartCC daemon, and start regtest one from cloned `bitcart` repo by running `make regtest`.

You should also start an lightning node for testing, run `make regtestln` in another terminal.

To run extended test suite, run `make regtest`.

Coverage from extended test suite is appended to main test coverage.

# Thank You!

Your contributions to open source, large or small, make great projects like this possible. Thank you for taking the time to contribute.
