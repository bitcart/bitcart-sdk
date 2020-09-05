import functools


class BaseError(Exception):
    """Base error for all errors raised"""


class InvalidEventError(BaseError):
    """Daemon returned unsupported event"""


class LightningDisabledError(BaseError):
    """Lightning is disabled in daemon"""


class WebhookUnsupportedError(BaseError):
    """Webhook support not installed"""


class ConnectionFailedError(BaseError):
    """Error connecting to the daemon"""


class RequestError(BaseError):
    """Base error for all errors returned from server"""


class UnknownError(RequestError):
    """Unknown error code returned from server"""


@functools.lru_cache()
def generate_exception(exc_name: str) -> type:
    return type(exc_name, (RequestError,), {})


class Errors:
    def __getattr__(self, key: str) -> type:
        return generate_exception(key)


errors = Errors()
