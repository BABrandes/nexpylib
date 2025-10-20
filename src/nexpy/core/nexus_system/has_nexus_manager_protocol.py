from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .nexus_manager import NexusManager

class HasNexusManagerProtocol(Protocol):

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this object belongs to.

        ** This method is not thread-safe and should only be called by the get_nexus_manager method.
        """
        ...