from typing import TypeVar, Any, Optional, Callable
from logging import Logger
from threading import RLock

from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

from nexpy.core import SubmissionError
from nexpy.core.hooks.protocols.owned_hook_protocol import OwnedHookProtocol
from nexpy.core.hooks.protocols.writable_hook_protocol import WritableHookProtocol
from nexpy.core.hooks.protocols.reactive_hook_protocol import ReactiveHookProtocol
from ..foundation.hook_base import HookBase
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ..mixins.hook_with_setter_mixin import HookWithSetterMixin
from ..mixins.hook_with_reaction_mixin import HookWithReactionMixin
from ..mixins.hook_with_owner_mixin import HookWithOwnerMixin

T = TypeVar("T")
O = TypeVar("O", bound="CarriesSomeHooksProtocol[Any, Any]", covariant=True)


class OwnedWritableHook(HookBase[T], OwnedHookProtocol[T, O], WritableHookProtocol[T], ReactiveHookProtocol[T], HookWithSetterMixin[T], HookWithReactionMixin[T], HookWithOwnerMixin[O]):  

    def __init__(
        self,
        owner: O,
        value: T,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:

        #-------------------------------- Initialization start --------------------------------

        self._owner = owner
        self._lock = RLock()

        #-------------------------------- Initialize base class --------------------------------

        HookBase.__init__( # type: ignore
            self=self,
            value_or_nexus=value,
            logger=logger,
            nexus_manager=nexus_manager)

        HookWithSetterMixin.__init__( # type: ignore
            self=self)

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
    # WritableHookProtocol methods
    #########################################################

    @value.setter # type: ignore
    def value(self, value: T) -> None: # type: ignore
        """
        Set the value behind this hook.

        ** Thread-safe **
        """
        with self._lock:
            nexus_manager = self._get_nexus_manager()
            success, msg = nexus_manager.submit_values({self._get_nexus(): value}, mode="Normal submission")
            if not success:
                raise SubmissionError(msg, value)

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value behind this hook.

        ** Thread-safe **
        """
        with self._lock:
            success, msg = self._change_value(value, logger=logger)
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, value)
            return success, msg

    #########################################################
    # ReactiveHookProtocol methods
    #########################################################

    def react_to_value_change(self) -> None:
        """
        React to the value change.

        ** Thread-safe **
        """
        with self._lock:
            self._react_to_value_change()

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

    