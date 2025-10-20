from typing import Protocol, runtime_checkable

@runtime_checkable
class HookWithReactionProtocol(Protocol):
    """
    Protocol for hook objects that can react to value changes.
    """

    def react_to_value_changed(self) -> None:
        """
        React to the value changed.

        It reacts to the current value of the hook.
        """
        ...