from typing import Generic, Optional, TypeVar, Any
from logging import Logger

from ..auxiliary.listening_base import ListeningBase
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER as DEFAULT_NEXUS_MANAGER
from ...x_objects_base.carries_some_hooks_protocol import CarriesSomeHooksProtocol

from .hook_bases.managed_hook_base import ManagedHookBase
from .hook_protocols.owned_read_only_hook_protocol import OwnedReadOnlyHookProtocol

T = TypeVar("T")

class OwnedReadOnlyHook(ManagedHookBase[T], OwnedReadOnlyHookProtocol[T], ListeningBase, Generic[T]):
    """
    An owned read-only hook that provides value access and basic capabilities without submission.
    
    This class focuses on:
    - Value access via callbacks
    - Basic capabilities (sending/receiving)
    - Owner reference and auxiliary information
    - Read-only access (no submit_value method)
    
    Complex binding logic is delegated to the BindingSystem class.
    This is particularly useful for secondary hook keys in observables where
    the hook should only be read, not modified directly.
    """

    def __init__(
            self,
            owner: CarriesSomeHooksProtocol[Any, Any],
            initial_value: T,
            logger: Optional[Logger] = None,
            nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
            ) -> None:

        ListeningBase.__init__(self, logger)
        ManagedHookBase.__init__( # type: ignore
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

        hook_key = self.owner.get_hook_key(self)  # type: ignore
        success, _ = self.owner._validate_value(hook_key, value) # type: ignore
        return success

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedReadOnlyHook(v={self.value}, id={id(self)})"

    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"OwnedReadOnlyHook(v={self.value}, id={id(self)})"
