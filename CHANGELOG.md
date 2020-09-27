# Release Notes

## Latest changes

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