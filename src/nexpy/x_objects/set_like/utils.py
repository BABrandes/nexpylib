from typing import TypeVar
from collections.abc import Iterator, Iterable

T = TypeVar("T")

def likely_settable(value: Iterable[T]) -> bool:
    
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)): # type: ignore
        return False

    iter_value: Iterator[T] = iter(value)
    try:
        first = next(iter_value)
    except StopIteration:
        return True  # empty iterable is fine
    return hasattr(first, "__hash__") and first.__hash__ is not None