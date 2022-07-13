import functools
from typing import Any, Optional


class BaseError(Exception):
    """Base error for all errors raised"""

    def __init__(self, msg: Optional[str] = None, *args: Any):
        super().__init__(msg or self.__doc__, *args)


class NoCurrenciesRegisteredError(BaseError):
    """APIManager has no currencies enabled"""


class CurrencyUnsupportedError(BaseError):
    """This coin is not supported by SDK"""


class LightningDisabledError(BaseError):
    """Lightning is disabled in daemon"""


class ConnectionFailedError(BaseError):
    """Error connecting to the daemon"""


class RequestError(BaseError):
    """Base error for all errors returned from server"""


class UnknownError(RequestError):
    """Unknown error code returned from server"""


class NotImplementedError(RequestError):
    """Not implemented"""


@functools.lru_cache
def generate_exception(exc_name: str) -> type:
    return type(exc_name, (RequestError,), {})


class Errors:
    def __getattr__(self, key: str) -> type:
        return generate_exception(key)


errors = Errors()
