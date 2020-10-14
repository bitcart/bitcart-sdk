from bitcart import APIManager

REAL_XPUB = "paste your x/y/z pub/prv or electrum seed here"

manager = APIManager(
    {
        "BTC": [REAL_XPUB, "xpub2"],
        "LTC": [REAL_XPUB, "xpub1", "xpub2"],
        "GZRO": [REAL_XPUB, "xpub1", "xpub2"],
        "BCH": [REAL_XPUB, "xpub1", "xpub2"],
    }
)
manager.add_wallet("BSTY", "xpub3")
manager.add_wallets("BTC", ["xpub4", "xpub5"])

print(APIManager.load_wallet("BTC", "xpub"))  # shortcut to from bitcart import BTC; return BTC(xpub=xpub)
print(APIManager.load_wallets("BTC", ["xpub1", "xpub2"]))  # returns a dict, where key is xpub, value is coin object

print(manager["BTC"][REAL_XPUB].balance())
print(manager["BTC"]["xpub2"].balance())
print(manager["LTC"]["xpub2"].balance())
# or
print(manager.BTC.xpub2.balance())
print(manager.LTC.xpub2.balance())


@manager.on("new_block")
def handler(instance, event, height):
    print(instance, event, height)


manager.start_websocket()
