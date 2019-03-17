# *-* coding:utf-8 *-*
'''Author: Alexey Drozdov(MrNaif)
Company name: Naif Studios
Email: chuff184@gmail.com'''
__author__="Alexey Drozdov(MrNaif)"
__company__="Naif Studios"
__email__="chuff184@gmail.com"
__copyright__=True
try:
    import requests
except ImportError:
    raise ImportError("You must install requests library first!")
try:
    from simplejson import loads as json_loads
except (ImportError,ValueError):
    from json import loads as json_loads
import warnings

class RPCProxy:
    def __init__(self,url,username=None,password=None,xpub=None,verify=True):
        self.url=url
        self.username=username
        self.password=password
        self.xpub=xpub
        self.verify=verify

    def _send_request(self,method,*args,**kwargs):
        if not self.username or not self.password:
            auth=None
        else:
            auth=(self.username,self.password)
        if args:
            arg=args
        elif kwargs:
            arg=kwargs
        else:
            arg=[]
        dict_to_send={"id": 0,"method":method,"params":arg}
        if self.xpub:
            dict_to_send["xpub"]=self.xpub
        response=requests.post(self.url,headers={'content-type': 'application/json'},json=dict_to_send,auth=auth,verify=self.verify)
        response.raise_for_status()
        json=response.json()
        if json["error"]:
            raise ValueError("Error from server: {}".format(json["error"]))
        if json["id"] != 0:
            warnings.warn("ID mismatch!")
        result=json.get("result",{})
        if type(result) == str:
            result=json_loads(result)
        return result

    def __getattr__(self,method,*args,**kwargs):
        def wrapper(*args,**kwargs):
            return self._send_request(method,*args,**kwargs)
        return wrapper
