from typing import Generic, Optional, TypeVar, Any
from logging import Logger

from .hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol

from ..auxiliary.listening_base import ListeningBase
from ..nexus_system.nexus_manager import NexusManager
from ..nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from ...x_objects_base.carries_some_hooks_protocol import CarriesSomeHooksProtocol

from .hook_bases.full_hook_base import FullHookBase

T = TypeVar("T")

class OwnedHook(FullHookBase[T], OwnedFullHookProtocol[T], ListeningBase, Generic[T]):
    """
    A owned hook that provides value access and basic capabilities.
    
    This class focuses on:
    - Value access via callbacks
    - Basic capabilities (sending/receiving)
    - Owner reference and auxiliary information
    
    Complex binding logic is delegated to the BindingSystem class.
    """

    def __init__(
            self,
            owner: CarriesSomeHooksProtocol[Any, Any],
            initial_value: T,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
            ) -> None:

        ListeningBase.__init__(self, logger)
        FullHookBase.__init__( # type: ignore
            self,
            value=initial_value,
            nexus_manager=nexus_manager,
            logger=logger
        )

        self._owner = owner

    @property
    def owner(self) -> CarriesSomeHooksProtocol[Any, T]:
        """Get the owner of this hook."""
        return self._owner

    def _get_owner(self) -> CarriesSomeHooksProtocol[Any, T]:
        """Get the owner of this hook."""

        with self._lock:
            owner = self._owner
            return owner

    def invalidate_owner(self) -> None:
        """Invalidate the owner of this hook."""
        self.owner._invalidate() # type: ignore

    def is_valid(self, value: T) -> bool:
        """Check if the hook is valid."""

        hook_key = self.owner._get_hook_key(self) # type: ignore
        success, _ = self.owner._validate_value(hook_key, value) # type: ignore
        return success

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedHook(v={self.value}, id={id(self)})"