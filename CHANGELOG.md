# Release Notes

## Latest changes

## 1.3.2.1

PyPI readme fixes

## 1.3.2.0

Added XRG support (#25)

## 1.3.1.0

Added new `get_invoice` method to get lightning invoices by their rhash

## 1.3.0.0

Drop python 3.6 support (we support 3 latest python releases)

## 1.2.1.0

License change to LGPLv3+

Python 3.9 support

## 1.2.0.0

`add_invoice` now works same way as `add_request` (breaking change)

This means:

- `message` parameter renamed to `description`
- added `expire` parameter, which also defaults to 15 minutes (was 60 minutes before)
- `amount` field in invoice data is Decimal too

## 1.1.0.5

Fixed APIManager websockets for multiple currencies

## 1.1.0.4

APIManager now supports more customization of connection options by not overriding them.

No more "no xpub provided" warnings.

## 1.1.0.3

APIManager now auto-reconnects properly when using multiple currencies

## 1.1.0.2

APIManager now calls it's handlers even when no wallet was matched

## 1.1.0.1

Fixed APIManager's `reconnect_callback`: now currency parameter is passed to it to differentiate between calls.

## 1.1.0.0

### Features

New event delivery method: websockets!

Websockets should be a better way of receiving updates than webhooks.

They are better because SDK doesn't need to know it's own address, and daemon doesn't need to be notified of webhook.

That way, with less complexity, any amount of listeners per wallet are possible now.

To use it, run:

```python
btc.start_websocket()
```

It will connect to websocket with auto-reconnect feature.

You can disable it by setting `auto_reconnect` parameter to `False`.

If `force_connect` is set to `True`, first time connection errors will be ignored.
By default, if connecting to websocket failed first time (might mean invalid URL), then `ConnectionFailedError` is raised.

On successful connection to websocket, `reconnect_callback` function is called.

If called from APIManager, `currency` parameter is passed.

### Breaking changes

As webhook method is not very easy to use, it is removed in favor of websockets.

So, `start_webhook`, `configure_webhook` and similar related methods are removed.

Also, daemon-side all event subscription methods are removed. Now all events are sent, and are filtered by SDK.

`start_websocket` in APIManager with no currencies set will now raise `NoCurrenciesRegisteredError`

## 1.0.1

Fixed issues with aiohttp warning and async functions in threads

## 1.0.0

All the SDK is now tested via our extensive test suite, we now gurantee to find all changes in electrum if they happen.

All the code is now following our code style.

### Features

#### Async/sync support in one library

Before, `bitcart` and `bitcart-async` packages existed, one providing sync API, another one async API.

Now both use cases are supported in a single `bitcart` package.

You can use either:

```python
btc.help()
```

Or

```python
async def main():
    await btc.help()
```

#### Better exceptions

It is now possible to catch specific exceptions in commands, not just a general one.

```python
from bitcart import errors
from bitcart.errors import generate_exception, ConnectionFailedError

try:
    coin.help()
except ConnectionFailedError:
    print("Failed connecting to daemon")
except errors.LoadingWalletError:
    print("Error loading wallet")
except RequestError as e:
    print(e)
```

New `ConnectionFailedError` is raised when SDK failed to connect to daemon.

`UnknownError` is raised when server returned an error code not from the spec, or spec failed loading.

`RequestError` is a base error from all errors returned from server.

generate_exception function creates a new dynamic exception by passing it's name to it, used for except.

`generate_exception("test") == errors.test`

errors object is just a convenience wrapper around `generate_exception`.

All other errors are raised and created dynamically, by the spec.

You can find your version of the spec at daemon's `/spec` endpoint.

[Most recent spec url](https://github.com/bitcartcc/bitcart/blob/master/daemons/spec/btc.json)

#### APIManager

APIManager provides an easy-to-use interface to manage multiple wallets/currencies.

It is useful for tracking payments on many wallets at once, for example.

[APIManager documentation](https://sdk.bitcartcc.com/en/latest/apimanager.html)

#### New utilities

New module `bitcart.utils` was added.

It has the following functions:

- `satoshis(amount: Decimal) -> int` converts btc amount to satoshis

- `bitcoins(amount: int) -> Decimal` converts satoshis amount to btc

- `json_encode(obj: Any) -> Any` `json.dumps` supporting decimals

#### New list_peers method

`list_peers(gossip=False)` method will list all the lightning peers.

#### COINS variable

Now `COINS` variable is available, it's a dict, where keys are strings, values are coins of respective types.

It allows introspection of available coins.

```python
from bitcart import COINS
COINS["BTC"] # bitcart.BTC class
```

#### Coins instances now can be compared

You can now check if two coin instances are the same like so:

```python
if coin1 == coin2:
    print("equal")
```

Two coin objects are equal, if their xpubs are equal, and their `coin_name` is equal.

#### All methods now support passing Decimals to it

It is needed to work with latest breaking changes, see below.

#### Electrum 4.0.3

SDK 1.0 is based on the latest daemon, which is using Electrum 4.0.3 for btc and other currencies, and Electron Cash 4.1.1

#### New spec property

`spec` property on coin objects and `RPCProxy` objects return exceptions spec returned from daemon.

#### add_request function now can work without arguments

`add_request` amount argument now defaults to `None`, so it can be used to just query a new address, for example.

#### Misc changes and fixes

- `poll_updates` default `timeout` argument changed from 2 to 1 second
- Many refactorings in the code
- `pay_to` and `pay_to_many` functions now work without issues in concurrent environments

### Breaking changes

This update is a major version change, it means that there will be lots of breaking changes between 0.x.y -> 1.x.y series, but between 1.x.y series there should be no breaking changes. We are following semver.

#### All fields which were float before or required float now require Decimal

It is added to prevent loss of precision with floats. You should use Decimals everywhere, and SDK methods now return Decimals. See related breaking changes below:

#### rate function no longer accepts accurate parameter

Rate function now returns Decimals always, so there is no accurate parameter anymore (this behaviour was achieved before by `rate(accurate=True)`)

#### Balance function dict's keys are now always Decimals

Before, if some balance didn't exist in a wallet, it returned `0` (int), but if it existed it returned amount as string.
This inconsistent behaviour is now fixed, but now every amount is Decimal.

#### add_request/get_request amount_COIN fields now return Decimals

`amount_BTC`, `amount_LTC`, `amount (BCH)`, etc. fields are now Decimals.

For convenience, `amount_field` attribute was added on coin objects:

```python
btc.amount_field # "amount_BTC"
```

#### Renamed some methods

`getrequest` was renamed to `get_request`
`addrequest` to `add_request`
`addinvoice` to `add_invoice`

To follow PEP8.

#### Changed callback function in pay_to/pay_to_many

Before fee callback function passed tx size and default fee (in satoshis) and expected to return btc amount.

Now it is expecting to return amount in satoshis for ease of use.

#### All errors are no longer based on ValueError

By adding a better exception system, and a major version change, we remove ValueError. `bitcart.errors.BaseError` is now a base error for all exceptions. `bitcart.errors.RequestError` is a base error for all errors returned from server. `bitcart.errors.UnknownError`, if spec is unavailable works the same as `ValueError` before

#### Flask app setup will no longer work

As internally all SDK code is now async, it is based on aiohttp server for webhooks. You should use aiohttp methods to set up custom servers if needed, flask is no longer a dependency.

#### webhook extra deleted

As aiohttp is now used for webhooks, there is no need to install extra dependencies. SDK 1.0 doesn't have webhook extra.

#### bitcart-async package deprecated

As async and sync versions are now part of one library, it will be in `bitcart` Pypi package. `bitcart-async` package's last version will be 0.9.1.

All future updates will be made in `bitcart` package.

#### Breaking changes in electrum format

They can be found in this PR [comment](https://github.com/bitcartcc/bitcart-sdk/pull/17#issuecomment-700143843)

## 0.9.1

Fixed async timeouts
Fixed timeout from 10 seconds to 5 minutes

## 0.9.0

To use proxy, install optional dependencies:

`pip install bitcart[proxy]` for sync version, `pip install bitcart-async[proxy]` for async version.

HTTP, SOCKS4 and SOCKS5 proxies supported.

To use, pass proxy url to coin constructor:

```python
btc = BTC(proxy="socks5://localhost:9050")
```

## 0.8.5

Version 0.8.5: completely remove aiohttp warnings

This version removes a nasty unclosed session and connector warning, finally!

## 0.8.4

Bitcoin Cash support & misc fixes

This version adds bitcoin cash support plus probably forever fixes unclosed session warning (:

## 0.8.3

Added BSTY coin

## 0.8.2

Added validate_key method

You can now use validate_key method to ensure that key you are going to use restore wallet is valid, without actually restoring it.

Examples:

```python
>>> c.validate_key("test")
False

>>> c.validate_key("your awesome electrum seed")
True

>>> c.validate_key("x/y/z pub/prv here")
True
```

## 0.8.1

Webhooks!

This update adds a new way of receiving updates, start a webhook and daemon will deliver updates to that webhook by itself.

To use that feature, `pip install bitcart[webhook]` for sync version(flask), async version has that built-in(aiohttp).

To use that instead of polling, just replace
`btc.poll_updates()`
with
`btc.start_webhook()`

## 0.8.0.post4

Remove async warning

This is a follow-up of previous release

## 0.8.0.post3

Automatic session closing in async!

That's it, no need to use async with or manual .close() anymore in async version!

## 0.8.0.post2

Added missing event and history() fixes

## 0.8.0.post1

This bugfix fixes xpub sending, and exception raising.

## 0.8.0

Structural improvements and more

**Structural improvements**

This version makes async version the default one used in the repo.

Pypi versions aren't changed, bitcart is sync version, bitcart-async is async.

But now there is a major difference, instead of maintaining both sync and async versions,
async version is in master, and sync version is generated using `sync_generator.py`, which basically removes async's and awaits.

It means less time spent, and instead of porting new features to sync/async versions, now I will have more time spend on new features!

The async branch will be deleted.

**Sending transactions improvements**

Also, the long awaited `pay_to_many` function to do batch transactions is there!
Both `pay_to` and `pay_to_many` now have optional `feerate`, which is sat/vbyte rate.

Minimum possible is 1 sat/vbyte.

With bitcart you can get minimal fees, with no third parties!

## 0.6.3

Added support for both args and kwargs, fixes
This version allows using SDK with both positional and by-name arguments.

## 0.6.2

Added missing pay_to_many

This release adds ability to create batch transactions, some examples:

```python
>>> btc.pay_to_many([{"address":"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt","amount":0.001}, {"address":"mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB","amount":0.0001}])
'60fa120d9f868a7bd03d6bbd1e225923cab0ba7a3a6b961861053c90365ed40a'

 >>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001),("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)])
'd80f14e20af2ceaa43a8b7e15402d420246d39e235d87874f929977fb0b1cab8'

>>> btc.pay_to_many([("mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt",0.001), ("mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB",0.0001)], broadcast=False)
{'hex': '0200000...', 'complete': True, 'final': False}
```

## 0.6.1

Fix for latest daemon

## 0.6.0

This version adds new coin: gzro to bitcart.
All APIs are the same, just import GZRO from bitcart.

## 0.5.1

Fee calculation func now recieves default fee as argument too

## 0.5.0

This version adds new coin: litecoin to bitcart.

This is where bitcart shows its features.

All APIs are the same, just import LTC from bitcart.

## 0.4.0

Full fee control and easy lightning.

Fee control:

Now you can pass fee parameter to pay_to function to specify manual fee, or
callback function like:

```python
def fee_calc(size):
    return size/4
btc.pay_to(address, amount, fee=fee_calc)
```

Getting size as argument and returning fee, it can be any function of your choice.

Another parameter, broadcast, was added. By default transaction is submitted to network, but if you set broadcast to False raw transaction will be returned. See API reference in docs for details.

**Easy lightning:**

Now lightning is part of btc daemon and BTC coin class, just launch the same daemon and use all lightning functions!

After upgrade, try for example, this:

```python
>>> btc.node_id
'030ff29580149a366bdddf148713fa808f0f4b934dccd5f7820f3d613e03c86e55'
```

Lightning is enabled in your daemon by default, disable it with BTC_LIGTNING=false environment variable.

If lightning is disabled, `bitcart.errors.LightningDisabledError` is raised.

## 0.3.0

This version adds new events-based API to get updates.

To register a callback function, use `add_event_handler(events, func)` function or `@on` decorator

Example:

```python
@btc.on("new_transaction")
def handler(event, tx):
    print(event)
    print(tx)
    print(btc.get_tx(tx))
btc.poll_updates()
```

The following code would print

```
new_transaction
some_tx_hash
dict of tx hash data
```

On each transaction in your wallet.
`btc.on` or `add_event_handler` can also accept a list of events, for example:

```python
def handler(event, **kwargs):
    print(event, kwargs)
```

Getting updates is the same, via `btc.poll_updates()`.

There are two kinds of events for now:

`new_block` which gets emitted on every new block, passing height argument to callback function

`new_transaction` which gets emitted on every new transaction passing tx argument as tx_hash of new transaction to callback_function.

Old `@btc.notify` api is removed.

## 0.2.5

Fix warning raising(no stacklevel)

## 0.2.4

Added ability to get fiat price in most currencies

Now `rate()` method accepts optional currency argument to get it in currency other than USD.

New method: `list_fiat()` to get list of all supported fiat currencies.

## 0.2.3

Add `btc.rate()` method to get USD price of bitcoin

## 0.2.2

Use requests.Session for better performance

## 0.2.1

This is a small bugfix to fix pip description rendering.

## 0.2.0

Version 0.2.0: Lightning update!

Lightning network support is now in bitcart as defined by [bitcartcc/bitcart#51](https://github.com/bitcartcc/bitcart/pull/51)

This adds in new LN class and related methods.

Also, now it is not needed to fill in all values, some defaults are used:

```
rpc_user="electrum"
rpc_pass="electrumz"
rpc_url="http://localhost:5000" for bitcoin daemon and "http://localhost:5001" for lightning daemon.
```

When xpub is not provided, a warning is created.

## 0.1.4

- Add type hints everywhere
- Code is checked with mypy and pylint
- Docs now available(check readme)
- Automatic deployment via circleci

And many more...

## 0.1

Initial release
