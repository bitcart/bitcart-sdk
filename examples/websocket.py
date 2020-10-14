from bitcart import BTC

btc = BTC(xpub="paste your x/y/z pub/prv or electrum seed here")


@btc.on(["new_block", "new_transaction"])
def handler(event, height=None, tx=None):
    print(event)
    print(height)
    print(tx)


btc.start_websocket()  # for websocket
# btc.poll_updates() for polling
