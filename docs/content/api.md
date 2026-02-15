# API Reference

## Implemented coins

### BTC

BTC class supports lightning out of the box.
For lightning methods to work, it must be enabled from the daemon
(enabled by default and edited by `BTC_LIGHTNING` environment variable).
If lightning is disabled, `LightningDisabledError` is raised when
calling lightning methods.

::: bitcart.coins.btc.BTC

### BCH

BCH supports Schnorr signatures, they are enabled out of the box

::: bitcart.coins.bch.BCH

### XMR

XMR support is based on our custom daemon implementation which tries to follow electrum APIs as closely as possible

::: bitcart.coins.xmr.XMR

### ETH

ETH support is based on our custom daemon implementation which tries to follow electrum APIs as closely as possible

::: bitcart.coins.eth.ETH

### BNB

BNB support is based on our custom daemon implementation which tries to follow electrum APIs as closely as possible

::: bitcart.coins.bnb.BNB

### Polygon (MATIC)

Polygon (MATIC) support is based on our custom daemon implementation which tries to follow electrum APIs as closely as possible

::: bitcart.coins.matic.MATIC

### TRON (TRX)

TRON (TRX) support is based on our custom daemon implementation which tries to follow electrum APIs as closely as possible

::: bitcart.coins.trx.TRX

### XRG

XRG supports Schnorr signatures, they are enabled out of the box

::: bitcart.coins.xrg.XRG

### LTC

LTC class supports lightning out of the box.
For lightning methods to work, it must be enabled from the daemon
(enabled by default and edited by `LTC_LIGHTNING` environment variable).
If lightning is disabled, `LightningDisabledError` is raised when
calling lightning methods.

::: bitcart.coins.ltc.LTC

### GRS

GRS class supports lightning out of the box.
For lightning methods to work, it must be enabled from the daemon
(enabled by default and edited by `GRS_LIGHTNING` environment variable).
If lightning is disabled, `LightningDisabledError` is raised when
calling lightning methods.

::: bitcart.coins.grs.GRS

## Utilities

::: bitcart.utils
