from typing import TypeVar, Generic, Optional, Callable

from ...auxiliary.utils import make_weak_callback

T = TypeVar("T", contravariant=True)

class HookWithIsolatedValidationMixin(Generic[T]):
    """
    Mixin for hook objects that have isolated validation.
    """

    def __init__(self, isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]]) -> None:
        """
        Initialize the hook with an isolated validation callback.
        """
        self._isolated_validation_callback = make_weak_callback(isolated_validation_callback)

    def _validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation.

        ** This method is not thread-safe and should only be called by the _validate_value_in_isolation method.
        """
        if self._isolated_validation_callback is not None:
            return self._isolated_validation_callback(value)
        else:
            return True, "No isolated validation callback provided"