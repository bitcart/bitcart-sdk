APIManager
----------

APIManager provides an easy-to-use interface to manage multiple wallets/currencies.

Setup
*****

Create APIManager like so:

.. code-block:: python

    manager = APIManager({"BTC": ["xpub1", "xpub2"], "currency2": ["xpub1", "xpub3"]})


This will load all specified wallets to the manager.

Accessing wallets
*****************

You can access wallets in a manager like so:

.. code-block:: python

    manager.BTC.xpub1 # access wallet <=> BTC(xpub="xpub1")
    # or
    manager["BTC"]["xpub1"] # same wallet, but via dict-like interface
    manager["currency2"]["xpub3"] # <=> currency2(xpub="xpub3")
    manager.BTC[xpub].balance() # <=> BTC(xpub=xpub).balance()

Adding new wallets to existing manager
**************************************

.. code-block:: python

    manager.add_wallet("BTC", "xpub3") # adds wallet to currency BTC with xpub="xpub3"
    manager.add_wallets("currency2", ["xpub1", "xpub2"]) # batch add

Coin objects creation utilities
*******************************

.. code-block:: python

    manager.load_wallet("currency", "xpub") # returns currency(xpub=xpub)
    manager.load_wallets("currency", ["xpub1", "xpub2"]) # returns a dict of xpub-currency(xpub=xpub)

Listening for updates on all wallets in a manager
*************************************************

You can register event handlers like you did before, on individual coin instances, or globally on manager object.

.. code-block:: python

    @manager.on("new_transaction")
    def handler(instance, event, tx):
        pass # instance is coin instance currently processing the event

To start a webhook, run:

.. code-block:: python

    manager.start_webhook()

Note: all webhook customization functions, as in regular coin instances, are available.