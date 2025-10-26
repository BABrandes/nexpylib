from typing import TypeVar, Optional, Callable
from logging import Logger
from threading import RLock

from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...auxiliary.utils import make_weak_callback

from nexpy.core import SubmissionError
from ..foundation.hook_base import HookBase
from ..protocols.writable_hook_protocol import WritableHookProtocol
from ..protocols.reactive_hook_protocol import ReactiveHookProtocol
from ..mixins.hook_with_setter_mixin import HookWithSetterMixin
from ..mixins.hook_with_reaction_mixin import HookWithReactionMixin

T = TypeVar("T")

class FloatingHook(HookBase[T], WritableHookProtocol[T], ReactiveHookProtocol[T], HookWithSetterMixin[T], HookWithReactionMixin[T]):

    def __init__(
        self,
        value: T,
        *,
        reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
        ) -> None:

        #-------------------------------- Initialization start --------------------------------

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
            reaction_callback=reaction_callback)

        #-------------------------------- Initialization complete --------------------------------

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