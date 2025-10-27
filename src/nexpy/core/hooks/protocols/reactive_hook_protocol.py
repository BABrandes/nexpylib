from typing import Protocol, TypeVar, Callable, Optional, runtime_checkable, Literal

T = TypeVar("T", covariant=True)

@runtime_checkable
class ReactiveHookProtocol(Protocol[T]):
    """
    Protocol for reactive hook objects.
    """

    def _react_to_value_change(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:
        """
        React to the value change.

        ** This method is not thread-safe and should only be called by the _react_to_value_change method.
        """
        ...

    def set_reaction_callback(self, reaction_callback: Callable[[], tuple[bool, str]]) -> None:
        """
        Set the reaction callback.

        ** Thread-safe **
        """
        ...

    def get_reaction_callback(self) -> Optional[Callable[[], tuple[bool, str]]]:
        """
        Get the reaction callback.
        """
        ...

    def remove_reaction_callback(self) -> None:
        """
        Remove the reaction callback.

        ** Thread-safe **
        """
        ...