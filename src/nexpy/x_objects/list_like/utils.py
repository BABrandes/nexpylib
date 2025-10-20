from typing import TypeVar
from collections.abc import Iterable
from itertools import islice

T = TypeVar("T")

def can_be_list(value: Iterable[T]) -> bool:
    if not isinstance(value, Iterable): # type: ignore
        return False
    try:
        next(islice(iter(value), 0, 1), None)
        return True
    except Exception:
        return False