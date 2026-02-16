# Installing Bitcart SDK

## Library installation

/// tab | uv (Recommended)

```sh
uv add bitcart
```

///

/// tab | pip

```sh
pip install bitcart
```

///

## Daemon installation

But to initialize a coin instance you will need
`rpc_url`, `rpc_login` and `rpc_password` (not required, defaults
work with default ports and authentification).
For that you'll need Bitcart daemon, so:

```sh
git clone https://github.com/bitcart/bitcart
cd bitcart
uv sync --no-dev --group btc
```

Everywhere here `coin_name` refers to coin you're going to run or use,
`COIN_NAME` is the same name but in caps.
For example if you run bitcoin, `coin_name=btc, COIN_NAME=BTC`, for litecoin `coin_name=ltc, COIN_NAME=LTC`.

Run `uv sync --no-dev --group coin_name` to install
requirements for daemon of `coin_name`.

/// note
To install multiple daemons, provide multiple groups:
`uv sync --no-dev --group btc --group ltc`.
///

This will clone main Bitcart repo and install dependencies,
we recommend using one virtualenv per daemon (some daemons conflict one
with another).

To run daemon, just start it:

```sh
just daemon btc
```

Or, to run it in background (linux only)

```sh
just daemon btc &
```

Note, to run a few daemons, use
`just daemon coin_name` for each `coin_name`.

### Default credentials

Default user is `electrum` and password is `electrumz`.

You can configure the user and password in `conf/.env`
file of cloned bitcart repo:

```sh
COIN_NAME_USER=myuser
COIN_NAME_PASS=mypassword
```

### Network settings

To run daemon in other network than mainnet, set `COIN_NAME_NETWORK` variable to network name (testnet, regtest).

By default, if coin supports it, lightning network is enabled.
To disable it, set `COIN_NAME_LIGHTNING` to false.

### Ports

Each daemon runs on a different port. The general scheme to get your daemon url is `http://localhost:port`.

You can change port and host by using `COIN_NAME_HOST` and `COIN_NAME_PORT` env variables.

Default ports start from 5000 and increase for each daemon by 1
(in order how they were added to Bitcart).
Bitcoin port is 5000, litecoin is 5001, etc.
Refer to main docs for ports information.

### Using the SDK

To initialize your Bitcart instance, import it and use those settings:

```python
from bitcart import BTC
btc = BTC(xpub="your (x/y/z)pub or (x/y/z)prv or electrum seed")
```

All the variables are actually optional, so you can just do
`btc = BTC()`
and use it, but without a wallet.
To use a wallet, pass xpub like so:
`btc = BTC(xpub="your x/y/zpub or x/y/zprv or electrum seed")`
Xpub, xprv or electrum seed is the thing that represents your wallet.
You can get it from your wallet provider, or, for testing or not,
from [BIP39 mnemonic generator](https://iancoleman.io/bip39/){:target="\_blank"}.

After that you can freely use bitcart methods,
refer to [API docs](api.md) for more information.
