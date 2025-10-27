from typing import TypeVar, Optional, runtime_checkable, Protocol
from logging import Logger

from .hook_protocol import HookProtocol

T = TypeVar("T")

@runtime_checkable
class WritableHookProtocol(HookProtocol[T], Protocol[T]):
    """
    Protocol for writable hook objects.
    
    This protocol extends HookProtocol to add write capability via change_value().
    Note: The value property setter is not defined here as protocols cannot properly
    express property setters. Implementations should provide both getter (from HookProtocol)
    and setter for the value property.
    """

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value behind this hook.

        ** Thread-safe **
        """
        ...