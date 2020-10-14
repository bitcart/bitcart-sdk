BitcartCC SDK Events System
---------------------------

Introduction
************

To be able to listen for incoming payments, transactions, new blocks or more, you should use events system.

In SDK, each event may have one handler.

One handler may handle multiple events at once

Using event system requires wallet.

Event handler signature is the following:

.. code-block:: python

    def handler(event, arg1, arg2):
        pass # process event

Where ``event`` is the only required argument everywhere.

Depending on the event being handled, it may provide additional arguments. All arguments must be named exactly as event is specifying.

If using event system from APIManager, then additional required argument ``instance`` is passed:

.. code-block:: python

    def handler(instance, event, arg1, arg2):
        pass # process event

Also, async handlers are supported too, like so:

.. code-block:: python

    async def handler(event, arg1, arg2):
        pass # process event, you can await here

Registering event handlers
**************************

To register an event handler, use ``on`` decorator:

.. code-block:: python

    @coin.on("event")
    def handler(event, arg1, arg2):
        pass

You can also register a handler for multiple events, then you should mark all arguments, except for ``event`` and ``instance`` (if provided) optional, like so:

.. code-block:: python

    @coin.on(["event1", "event2"])
    def handler(event, arg1=None, arg2=None, arg3=None):
        pass # event argument can be used to get what event is currently being processed


Or you can use ``add_event_handler`` method instead:

.. code-block:: python

    def handler(event, arg1, arg2):
        pass

    coin.add_event_handler("event", handler)

They work identically.

Events list
***********

new_block
=========

Called when a new block is mined

Additional data:

- height (int): height of this block

new_transaction
===============

Called when a new transaction on this wallet has appeared

Additional data:

- tx (str): tx hash of this transaction

new_payment
===========

Called when status of payment request has changed. (See ``get_request``/``add_request``)

Additional data:

- address (str): address related to this payment request
- status (int): new status code
- status_str (str): string version of new status code

Listening for updates
*********************

To receive updates, you should use one of the available event delivery methods: polling or websocket

Polling
=======

Polling is good for quick testing, but not very good for production.

In this method SDK calls ``get_updates`` daemon method constantly, processing any new updates received.

To use it, run:

.. code-block:: python

    coin.poll_updates()

It will start an infinite loop.

Websocket
=======

Websocket is a bit harder to set up sometimes, but works better.

Instead of constantly calling daemon method to get updates, daemon will send updates when they are available via an estabilished connection.

That way, you don't need to know your URL, you should only know daemon URL, and a channel between SDK and daemon will be set up.

To use it, run:

.. code-block:: python

    coin.start_websocket()

It will connect to your daemon's ``/ws`` endpoint, with auto-reconnecting in case of unexpected websocket close.

There may be unlimited number of websockets per wallet or not.

Under the hood, if using APIManager, daemon will send all it's updates to SDK, and SDK will filter only the one you need.

If using coin object, daemon will only send updates about this wallet.


Manual updates processing
=========================

If you need complete control over updates delivery, you can pass updates to coin's method directly:

.. code-block:: python

    coin.process_updates(updates_list)

Where ``updates_list`` is a list of dictionaries.

Each dictionary must contain event key, and additional keys for data required for this event.


Processing updates for multiple wallets/currencies
**************************************************

If you need to process updates for multiple wallets/currencies, take a look at :doc:`APIManager documentation <apimanager>`