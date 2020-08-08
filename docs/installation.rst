Installing BitcartCC SDK
========================

Simply run

.. code-block:: sh

    pip install bitcart

to install the library.

Or, run

.. code-block:: sh

    pip install bitcart-async

To install async version of the library.

You can't install both.

Async version of the library has the same API, but is intended to be used in asyncio application.
All is the same, just use async/await.

But to initialize bitcoin instance you will need
``rpc_url``, ``rpc_login`` and ``rpc_password`` (not required, defaults
work with default ports and authentification).
For that you'll need BitcartCC daemon, so:

.. code-block:: sh

    git clone https://github.com/MrNaif2018/bitcart
    cd bitcart
    pip install -r requirements/base.txt
    pip install -r requirements/daemons/btc.txt

Everywhere here ``coin_name`` refers to coin you're going to run or use,
``COIN_NAME`` is the same name but in caps.
For example if you run bitcoin, ``coin_name=btc, COIN_NAME=BTC``, for litecoin ``coin_name=ltc, COIN_NAME=LTC``.

Run ``pip install -r requirements/daemons/coin_name.txt`` to install
requirements for daemon of ``coin_name``.

This will clone main BitcartCC repo and install dependencies,
we recommend using virtualenv for consistency.(some daemons conflict one
with another, so using one virtualenv per daemon is fine).

To run daemon, just start it:

.. code-block:: sh

    python daemons/btc.py

Or, to run it in background(linux only)

.. code-block:: sh

    python daemons/btc.py &

Note, to run a few daemons, use
``python daemons/coin_name.py`` for each ``coin_name``.

Default user is electrum and password is electrumz, it runs on http://localhost:5000.
To run daemon in testnet, set ``COIN_NAME_TESTNET`` variable to true.
By default, if coin supports it, lightning network is enabled.
To disable it, set ``COIN_NAME_LIGHTNING`` to false.
For each daemon port is different.
General scheme to get your daemon url is
http://localhost:port
Where port is the port your daemon uses.
You can change port and host by using ``COIN_NAME_HOST`` and ``COIN_NAME_PORT``
env variables.
Default ports are starting from 5000 and increase for each daemon by 1
(in order how they were added to BitcartCC).
Refer to main docs for ports information.
Bitcoin port is 5000, litecoin is 5001, etc.
So, to initialize your BitcartCC instance right now,
import it and use those settings:

.. code-block:: python

    from bitcart import BTC
    btc = BTC(xpub="your (x/y/z)pub or (x/y/z)prv or electrum seed")

All the variables are actually optional, so you can just do
``btc = BTC()``
and use it, but without a wallet.
To use a wallet, pass xpub like so:
``btc = BTC(xpub="your x/y/zpub or x/y/zprv or electrum seed")``
Xpub, xprv or electrum seed is the thing that represents your wallet.
You can get it from your wallet provider, or, for testing or not,
from `here <https://iancoleman.io/bip39/>`_.

You can configure default user and password in ``conf/.env``
file of cloned bitcart repo, like so:

.. code-block:: sh

    COIN_NAME_USER=myuser
    COIN_NAME_PASS=mypassword

After that you can freely use bitcart methods,
refer to :doc:`API docs <api>` for more information.
