from typing import Generic, TypeVar, Optional, Callable
from logging import Logger

from ..auxiliary.listening_base import ListeningBase
from ..nexus_system.nexus_manager import NexusManager
from ..nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

from .hook_bases.full_hook_base import FullHookBase
from .mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
from .mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol

T = TypeVar("T")

class FloatingHook(FullHookBase[T], HookWithIsolatedValidationProtocol[T], HookWithReactionProtocol, ListeningBase, Generic[T]):
    """
    A floating hook that can be used to store a value that is not owned by any observable.
    """

    def __init__(
        self,
        value: T,
        reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: "NexusManager" = DEFAULT_NEXUS_MANAGER
        ) -> None:
        
        self._reaction_callback = reaction_callback
        self._isolated_validation_callback = isolated_validation_callback

        ListeningBase.__init__(self, logger)
        FullHookBase.__init__( # type: ignore
            self,
            value=value,
            nexus_manager=nexus_manager,
            logger=logger
        )

    def react_to_value_changed(self) -> None:
        """React to the value changed."""
        if self._reaction_callback is not None:
            self._reaction_callback()

    def validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """Validate the value in isolation."""
        if self._isolated_validation_callback is not None:
            return self._isolated_validation_callback(value)
        else:
            return True, "No isolated validation callback provided"

    #########################################################
    # Debugging convenience methods
    #########################################################

    def __repr__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
    
    def __str__(self) -> str:
        """Get the string representation of this hook."""
        return f"FloatingHook(v={self.value}, id={id(self)})"
