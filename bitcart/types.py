from collections import UserDict, defaultdict
from decimal import Decimal
from typing import Any, Union

AmountType = Union[int, str, Decimal]


class ExtendedDictMixin:
    def __getattr__(self, name: str) -> Any:
        return self.__getitem__(name)


class ExtendedDict(ExtendedDictMixin, UserDict):
    pass


class ExtendedDefaultDict(ExtendedDictMixin, defaultdict):
    pass
