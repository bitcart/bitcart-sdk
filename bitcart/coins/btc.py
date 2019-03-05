# pylint: disable=import-error, invalid-sequence-index
import sys
sys.path.append("..")
try:
    from ..coin import Coin
except (ValueError,ImportError):
    from coin import Coin

class BTC(Coin):
    coin_name="BTC"
    friendly_name="Bitcoin"
    providers=["jsonrpcrequests"]

    def __init__(self,rpc_url,rpc_user=None,rpc_pass=None,xpub=None):
        super().__init__()
        self.rpc_url = rpc_url
        self.rpc_user = rpc_user
        self.rpc_pass = rpc_pass
        self.xpub=xpub
        self.server = self.providers["jsonrpcrequests"].RPCProxy(self.rpc_url,self.rpc_user,self.rpc_pass,self.xpub)

    def get_tx(self, tx: str) -> dict:
        out=self.server.get_transaction(tx)
        try:
            out["input"]=out["inputs"][0]["address"]
        except (KeyError,IndexError):
            out["input"]=None
        return out

    def get_address(self, address: str) -> list:
        out = self.server.getaddresshistory(address)
        for i in out:
            i["tx"] = self.get_tx(i["tx_hash"])
        return out

    def balance(self) -> dict:
        data = self.server.getbalance()
        return {"confirmed": data.get("confirmed"),
            "unconfirmed": data.get("unconfirmed"),
            "unmatured": data.get("unmatured")}

    def addrequest(self, amount, description="", expire=15) -> dict:
        return self.server.addrequest(amount=amount, memo=description, expiration=60*expire, force=True)
        
    def getrequest(self, address: str) -> dict:
        return self.server.getrequest(address)

    def history(self) -> list:
        return self.server.history()
