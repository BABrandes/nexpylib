from typing import TypeVar, Any, Optional, Callable, Generic, Literal
from logging import Logger

from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

from nexpy.core.hooks.protocols.owned_hook_protocol import OwnedHookProtocol
from nexpy.core.hooks.protocols.reactive_hook_protocol import ReactiveHookProtocol
from ..foundation.hook_base import HookBase
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ..mixins.hook_with_reaction_mixin import HookWithReactionMixin
from ..mixins.hook_with_owner_mixin import HookWithOwnerMixin

T = TypeVar("T")
O = TypeVar("O", bound="CarriesSomeHooksProtocol[Any, Any]", covariant=True)


class OwnedReadOnlyHook(HookBase[T], OwnedHookProtocol[T, O], ReactiveHookProtocol[T], HookWithReactionMixin[T], HookWithOwnerMixin[O], Generic[T, O]):

    def __init__(
        self,
        owner: O,
        value: T,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:

        #-------------------------------- Initialization start --------------------------------

        #-------------------------------- Initialize base class --------------------------------

        HookBase.__init__( # type: ignore
            value_or_nexus=value,
            logger=logger,
            nexus_manager=nexus_manager)

        HookWithReactionMixin.__init__( # type: ignore
            self=self,
            reaction_callback=None)

        HookWithOwnerMixin.__init__( # type: ignore
            self=self,
            owner=owner)

        #-------------------------------- Initialization complete --------------------------------

    #########################################################
    # OwnedHookProtocol methods
    #########################################################

    @property
    def owner(self) -> O:
        """
        Get the owner of this hook.

        ** Thread-safe **
        """
        with self._lock:
            return self._owner

    def get_owner(self) -> O:
        """
        Get the owner of this hook.

        ** Thread-safe **
        """
        with self._lock:
            return self._owner

    #########################################################
    # ReactiveHookProtocol methods
    #########################################################

    def _react_to_value_change(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:
        """
        React to the value change.
        
        ** This method is not thread-safe and should only be called by the _react_to_value_change method.
        """
        HookWithReactionMixin._react_to_value_change(self, raise_error_mode) # type: ignore

    def set_reaction_callback(self, reaction_callback: Callable[[], tuple[bool, str]]) -> None:
        """
        Set the reaction callback.

        ** Thread-safe **
        """
        with self._lock:
            self._set_reaction_callback(reaction_callback)

    def get_reaction_callback(self) -> Optional[Callable[[], tuple[bool, str]]]:
        """
        Get the reaction callback.

        ** Thread-safe **
        """
        with self._lock:
            return self._get_reaction_callback()

    def remove_reaction_callback(self) -> None:
        """
        Remove the reaction callback.

        ** Thread-safe **
        """
        with self._lock:
            self._remove_reaction_callback()