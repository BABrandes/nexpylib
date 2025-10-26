from typing import Protocol, TypeVar, Optional, runtime_checkable
from logging import Logger
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol

T = TypeVar("T")

@runtime_checkable
class XSingleValueProtocol(Protocol[T]):
    """
    Protocol for single-value objects.
    """

    #-------------------------------- value --------------------------------

    @property
    def value_hook(self) -> HookProtocol[T]:
        """
        Get the hook for the single-value object.
        """
        ...

    @property
    def value(self) -> T:
        """
        Get the value of the single-value object.
        """
        ...

    @value.setter
    def value(self, value: T) -> None:
        """
        Set the value of the single-value object.
        """
        ...

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value of the single-value object.
        """
        ...