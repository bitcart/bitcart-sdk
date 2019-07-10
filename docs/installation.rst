Installing Bitcart SDK
======================

Simply run

.. code-block:: sh

    pip install bitcart

to install the library.

But to initialize bitcoin instance you will need
rpc_url, rpc_login and rpc_password.
For that you'll need bitcart daemon, so:

.. code-block:: sh

    git clone https://github.com/MrNaif2018/bitcart
    cd bitcart
    wget https://raw.githubusercontent.com/MrNaif2018/bitcart-docker/master/scripts/electrum_version.py && python electrum_version.py

This will clone main bitcart repo and install dependencies,
we recommend using virtualenv for consistency.

To run daemon, just start it:

.. code-block:: sh

    python daemon.py

Or, to run it in background(linux only)

.. code-block:: sh

    python daemon.py &

Default user is electrum and password is electrumz, it runs on http://localhost:5000.
So, to initialize your bitcart instance right now,
import it and use those settings:

.. code-block:: python

    from bitcart.coins.btc import BTC
    btc = BTC("http://localhost:5000", xpub="your x/y/zpub or x/y/zprv",
            rpc_user="electrum", rpc_pass="electrumz")

Xpub(or xprv) is the thing that represents your wallet.
You can get it from your wallet provider, or, for testing or not,
from `here <https://iancoleman.io/bip39/>`_.

You can configure default user and password in ``conf/.env``
file of cloned bitcart repo, like so:

.. code-block:: sh

    RPC_USER=myuser
    RPC_PASS=mypassword

After that you can freely use bitcart methods,
refer to :doc:`API docs <api>` for more information.
