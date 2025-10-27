from typing import Generic, TypeVar, Optional, Literal
from collections.abc import Callable
import warnings

from ...auxiliary.utils import make_weak_callback

T = TypeVar("T")

class HookWithReactionMixin(Generic[T]):
    """
    Mixin for hook objects that can react to value changes.
    """

    def __init__(self, reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None) -> None:
        """
        Initialize the hook with a reaction.
        """
        self._reaction_callback = make_weak_callback(reaction_callback)

    def _react_to_value_change(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:
        """
        React to the value changed.

        ** This method is not thread-safe and should only be called by the _react_to_value_change method.

        It reacts to the current value of the hook.
        """
        if self._reaction_callback is not None:
            try:
                self._reaction_callback()
            except Exception as e:
                if raise_error_mode == "raise":
                    raise e
                elif raise_error_mode == "ignore":
                    pass
                elif raise_error_mode == "warn":
                    warnings.warn(f"Error in reaction callback: {e}", stacklevel=2)

    def _set_reaction_callback(self, reaction_callback: Callable[[], tuple[bool, str]]) -> None:
        """
        Set the reaction callback.

        ** This method is not thread-safe and should only be called by the _set_reaction_callback method.
        """
        self._reaction_callback = make_weak_callback(reaction_callback)

    def _get_reaction_callback(self) -> Optional[Callable[[], tuple[bool, str]]]:
        """
        Get the reaction callback.

        ** This method is not thread-safe and should only be called by the _get_reaction_callback method.
        """
        return self._reaction_callback

    def _remove_reaction_callback(self) -> None:
        """
        Remove the reaction callback.

        ** This method is not thread-safe and should only be called by the _remove_reaction_callback method.
        """
        self._reaction_callback = None
