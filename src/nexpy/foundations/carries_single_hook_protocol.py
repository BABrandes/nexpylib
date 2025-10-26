from typing import Optional, Protocol, TypeVar, runtime_checkable, Any, Literal, Self
from logging import Logger

from ..core.hooks import HookProtocol, OwnedHookProtocol
from .carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ..core.nexus_system.nexus import Nexus

T = TypeVar("T")

@runtime_checkable
class CarriesSingleHookProtocol(CarriesSomeHooksProtocol[Any, T], Protocol[T]):
    """
    Protocol for objects that carry a single hook.
    
    
    Generic type parameters:
        T: The type of the value
    """

    def _get_nexus(self) -> Nexus[T]:
        """
        Get the nexus that this single value hook belongs to.
        """
        ...

    def _get_single_hook(self) -> OwnedHookProtocol[T, Self]:
        """
        Get the hook for the single value.

        ** This method is not thread-safe and should only be called by the get_single_value_hook method.

        Returns:
            The hook for the single value
        """
        ...

    def _get_single_value(self) -> T:
        """
        Get the value of the single hook.

        ** This method is not thread-safe and should only be called by the get_single_value method.

        Returns:
            The value of the single hook
        """
        ...

    def join(self, target_hook: "HookProtocol[T] | CarriesSingleHookProtocol[T]", sync_mode: Literal["use_caller_value", "use_target_value"] = "use_caller_value") -> None:
        """
        Join the single hook to the target hook.

        Args:
            target_hook: The hook to join to
            sync_mode: The sync mode to use
        """
        ...

    def isolate(self) -> None:
        """
        Isolate the single hook.

        ** Thread-safe **
        """
        ...

    def is_joined_with(self, hook: "HookProtocol[T] | CarriesSingleHookProtocol[T]") -> bool:
        """
        Check if the single hook is joined with the target hook.

        ** Thread-safe **
        """
        ...

    def validate_value(self, value: T, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        This method checks if the provided value would be valid for submission. 

        ** Thread-safe **

        Args:
            value: The value to submit
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails

        Returns:
            A tuple of (success: bool, message: str)
        """
        ...

    def submit_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        This method submits a value.

        ** Thread-safe **

        Args:
            key: The key of the hook to submit the value to
            value: The value to submit
            raise_submission_error_flag: Whether to raise a SubmissionError if the submission fails

        Returns:
            A tuple of (success: bool, message: str)
        """
        ...