from typing import TypeVar, Optional, runtime_checkable, Protocol
from logging import Logger

from .hook_protocol import HookProtocol

T = TypeVar("T")

@runtime_checkable
class WritableHookProtocol(HookProtocol[T], Protocol[T]):
    """
    Protocol for writable hook objects.
    """

    #-------------------------------- value --------------------------------

    @value.setter # type: ignore
    def value(self, value: T) -> None: # type: ignore
        """
        Set the value behind this hook.

        ** Thread-safe **
        """
        ...

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value behind this hook.

        ** Thread-safe **
        """
        ...