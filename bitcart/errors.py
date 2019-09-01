class BaseError(Exception):
    """Base error for all errors raised"""

    pass


class InvalidEventError(BaseError):
    """Daemon returned unsupported event"""

    pass


class LightningDisabledError(BaseError):
    """Lightning is disabled in daemon"""

    pass
