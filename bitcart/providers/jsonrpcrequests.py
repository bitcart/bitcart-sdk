'''Author: MrNaif2018
Email: chuff184@gmail.com'''
__author__ = "MrNaif2018"
__email__ = "chuff184@gmail.com"
try:
    import requests
except ImportError:
    raise ImportError("You must install requests library first!")
try:
    from simplejson import loads as json_loads
except (ImportError, ValueError):
    from json import loads as json_loads
import warnings
from typing import Any, Optional, Union, Callable


class RPCProxy:
    def __init__(
            self: 'RPCProxy',
            url: str,
            username: Optional[str] = None,
            password: Optional[str] = None,
            xpub: Optional[str] = None,
            session: Optional[requests.Session] = None,
            verify: Optional[bool] = True):
        self.url = url
        self.username = username
        self.password = password
        self.xpub = xpub
        self.verify = verify
        self.session = session or requests.Session()

    def _send_request(
            self: 'RPCProxy',
            method: str,
            *args: Any,
            **kwargs: Any) -> Any:
        if not self.username or not self.password:
            auth = None
        else:
            auth = (self.username, self.password)
        arg: Union[dict, tuple]
        if args:
            arg = args
        elif kwargs:
            arg = kwargs
        else:
            arg = ()
        dict_to_send = {"id": 0, "method": method, "params": arg}
        if self.xpub:
            dict_to_send["xpub"] = self.xpub
        response = self.session.post(
            self.url,
            headers={
                'content-type': 'application/json'},
            json=dict_to_send,
            auth=auth,
            verify=self.verify)
        response.raise_for_status()
        json = response.json()
        if json["error"]:
            raise ValueError("Error from server: {}".format(json["error"]))
        if json["id"] != 0:
            warnings.warn("ID mismatch!")
        result = json.get("result", {})
        if isinstance(result, str):
            try:
                result = json_loads(result)
            except Exception:
                pass
        return result

    def __getattr__(
            self: 'RPCProxy',
            method: str,
            *args: Any,
            **kwargs: Any) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._send_request(method, *args, **kwargs)
        return wrapper
