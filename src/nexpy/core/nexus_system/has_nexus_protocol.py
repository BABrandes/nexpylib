from typing import Protocol, TypeVar
from .nexus import Nexus

T = TypeVar("T")

class HasNexusProtocol(Protocol[T]):
    """
    Protocol for objects that have a nexus.
    """

    def _get_nexus(self) -> Nexus[T]:
        """
        Get the nexus that this object belongs to.

        ** This method is not thread-safe and should only be called by the get_nexus method.
        """
        ...