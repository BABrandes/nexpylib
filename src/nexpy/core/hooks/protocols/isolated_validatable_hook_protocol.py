from typing import TypeVar, Protocol, runtime_checkable

T = TypeVar("T", contravariant=True)

@runtime_checkable
class IsolatedValidatableHookProtocol(Protocol[T]):
    """
    Protocol for hook objects that are isolated validatable.
    """

    def _validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation.

        ** This method is not thread-safe and should only be called by the _validate_value_in_isolation method.

        Args:
            value: The value to validate

        Returns:
            Tuple of (success: bool, message: str)
        """
        ...