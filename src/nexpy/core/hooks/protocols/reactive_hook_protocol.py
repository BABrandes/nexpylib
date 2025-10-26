from typing import Protocol, TypeVar, Callable, Optional, runtime_checkable

T = TypeVar("T", covariant=True)

@runtime_checkable
class ReactiveHookProtocol(Protocol[T]):
    """
    Protocol for reactive hook objects.
    """

    def react_to_value_change(self) -> None:
        """
        React to the value change.

        ** Thread-safe **
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