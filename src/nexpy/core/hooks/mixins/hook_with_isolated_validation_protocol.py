from typing import TypeVar, Protocol, runtime_checkable, final, Optional, Mapping, Any, TYPE_CHECKING
from logging import Logger

if TYPE_CHECKING:
    from logging import Logger
    from nexpy.core.nexus_system.nexus import Nexus
    from nexpy.core.nexus_system.nexus_manager import NexusManager

T = TypeVar("T", contravariant=True)

@runtime_checkable
class HookWithIsolatedValidationProtocol(Protocol[T]):
    """
    Protocol for hook objects that can validate values in isolation (independent of other hooks in the same nexus).
    """

    def _validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation. This is used to validate the value of a hook
        in isolation, without considering the value of other hooks in the same nexus.

        Args:
            value: The value to validate

        Returns:
            Tuple of (success: bool, message: str)
        """
        ...