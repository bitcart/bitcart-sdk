from bitcart import BTC, errors

SHOW_UPDATES = True  # if you want this demo to run forever printing out updates
DONATE_TO_AUTHOR = False  # if you really want to execute pay_to commands on your wallet

btc = BTC()


# Information about used coin #
print(btc.coin_name)  # like BTC
print(btc.friendly_name)  # like Bitcoin
print(btc.RPC_URL)  # default rpc url
print(btc.RPC_USER)  # default rpc user
print(btc.RPC_PASS)  # default rpc password

# Methods used without wallet #
print(btc.help())  # List of low level electrum methods
print(btc.server.validateaddress("x"))  # Example of calling lowlevel electrum method
print(btc.get_tx("d0e9433f41e17ef74547aa5e1873cd3ad12f1402b488eb93e1c8e3dda971ef53"))  # Get transaction info
print(btc.set_config("x", 1))  # Set a key in electrum config, also some type of a temporary storage
print(btc.get_config("x"))  # -> 1 Get config key
print(btc.get_address("1MBbj9ENeEdSeJwJFReWNgrDJrSMMqWqH4"))  # Address history
try:
    print(btc.server.create(wallet_path="tmp"))  # create new wallet
except errors.WalletExistsError:
    pass  # already exists
btc2 = BTC(xpub="paste your x/y/z pub/prv or electrum seed here for it to work")
# Wallet methods #
print(btc2.balance())
print(btc2.history())  # history of all transactions and summary
### Payment requests ###
data = btc2.add_request(0.5)
print(data)
print(btc2.add_request(0.5, "Any description"))  # Request specified amount in BTC
print(btc2.get_request(data["address"]))  # Check request status
### Sending ###
if DONATE_TO_AUTHOR:
    print(btc2.pay_to("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1))  # tx hash returned
    # raw hash returned, not broadcasted to network
    print(btc2.pay_to("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1, broadcast=False))
    print(btc2.pay_to("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1, fee=0.00000001))  # custom fee

    def fee_func(size, default_fee):
        return size / 4  # just a random calculation

    print(btc2.pay_to("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1, fee=fee_func))  # Dynamic fee calculation

    ### Bulk payments, specify in one of two formats, same return values and parameters as in pay_to ###
    btc2.pay_to_many([("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1), ("1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", 0.1)])
    btc2.pay_to_many(
        [
            {"address": "1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", "amount": 0.1},
            {"address": "1A6jnc6xQwmhsChNLcyKAQNWPcWsVYqCqJ", "amount": 0.1},
        ]
    )

# Lightning(requires wallet) #
print(btc2.node_id)  # your lightning node id(lightning daemon is bitcart daemon itself)
print(btc2.add_invoice(0.5, "Description"))  # create lightning invoice
# print(btc2.connect("some connection string"))  # add new lightning peer, connect
# print(btc2.open_channel("some node id", 0.5))  # open lightning channel with node
print(btc2.list_peers())  # list of lightning peers
print(btc2.list_channels())  # List of lightning channels
# print(btc2.close_channel("channel id"))  # Close channel by channel id, set force to True to do force-close
# print(btc2.lnpay("lightning invoice here"))  # pay a lightning invoice

# Notification API(requires wallet)


@btc2.on("new_block")
def new_block(event, height):
    print(event)
    print(height)  # block height


@btc2.on("new_transaction")
def new_tx(event, tx):
    print(event)
    print(tx)  # tx hash


### Or register a function under multiple events ###
# @btc2.on(["new_block","new_transaction"])
# def handler(event, tx=None, height=None):
#    print(event)
#    if event == "new_block":
#        print(f"New block: {height}")
#    elif event == "new_transaction":
#        print(f"New transaction: {tx}")


if SHOW_UPDATES:
    btc2.poll_updates()  # start receiving updates
