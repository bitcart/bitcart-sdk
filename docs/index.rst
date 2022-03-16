.. BitcartCC SDK documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:11:54 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to BitcartCC SDK's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   events
   apimanager
   api

BitcartCC is a platform to simplify cryptocurrencies adaptation.
This SDK is part of BitcartCC.
Using this SDK you can easily connect to BitcartCC daemon
and code scripts around it easily.

Behold, the power of BitcartCC:

.. code-block:: python

    from bitcart import BTC

    btc = BTC(xpub="your (x/y/z)pub or (x/y/z)prv or electrum seed")


    @btc.on("new_transaction")
    def callback_func(event, tx):
        print(event)
        print(tx)


    btc.poll_updates()

This simple script will listen for any new transaction on your
wallet's addresses and print information about them like so:

.. image:: images/1.png

And if you add ``print(btc.get_tx(tx))`` it would print
full information about every transaction, too!

To run this script, refer to :doc:`installation <installation>` section.
For examples of usage, check examples directory in github repository.

Supported coins list(⚡ means lightning is supported):

- Bitcoin (⚡)
- Bitcoin Cash
- Ethereum
- Ergon
- Litecoin (⚡)
- Globalboost (⚡)

To use proxy, install optional dependencies:

``pip install bitcart[proxy]``
HTTP, SOCKS4 and SOCKS5 proxies supported.

To use, pass proxy url to coin constructor:

.. code-block:: python

    btc = BTC(proxy="socks5://localhost:9050")
