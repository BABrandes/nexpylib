from typing import Protocol, runtime_checkable, TypeVar
from threading import RLock

from ..hook_protocols.managed_hook_protocol import ManagedHookProtocol

T = TypeVar("T")

@runtime_checkable
class ReadOnlyHookProtocol(ManagedHookProtocol[T], Protocol[T]):
    """
    Protocol for read-only hook objects.
    """

    @property
    def lock(self) -> RLock:
        """
        Get the lock for thread safety.
        """
        ...