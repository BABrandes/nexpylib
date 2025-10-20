

from typing import Generic, Mapping, TypeVar
from dataclasses import dataclass

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


@dataclass(frozen=True, slots=True)
class FunctionValues(Generic[K, V]):

    submitted: Mapping[K, V]
    current: Mapping[K, V]
    
    def __repr__(self) -> str:
        """Return a readable representation."""
        return f"FunctionValues(submitted={dict(self.submitted)}, current={dict(self.current)})"

