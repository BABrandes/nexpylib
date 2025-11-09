from typing import TypeVar, Optional, Callable, Generic, Literal
from logging import Logger

from ...nexus_system.submission_error import SubmissionError
from ..foundation.hook_base import HookBase
from ..protocols.writable_hook_protocol import WritableHookProtocol
from ..protocols.reactive_hook_protocol import ReactiveHookProtocol
from ..mixins.hook_with_setter_mixin import HookWithSetterMixin
from ..mixins.hook_with_reaction_mixin import HookWithReactionMixin
from ..mixins.hook_with_isolated_validation_mixin import HookWithIsolatedValidationMixin
from ..protocols.isolated_validatable_hook_protocol import IsolatedValidatableHookProtocol
from nexpy.core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from nexpy.core.nexus_system.nexus_manager import NexusManager

T = TypeVar("T")

class FloatingHook(
    HookBase[T],
    WritableHookProtocol[T],
    ReactiveHookProtocol[T],
    IsolatedValidatableHookProtocol[T],
    HookWithSetterMixin[T],
    HookWithReactionMixin[T],
    HookWithIsolatedValidationMixin[T],
    Generic[T]
):

    def __init__(
        self,
        value: T,
        *,
        reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "async",
        ) -> None:

        #-------------------------------- Initialization start --------------------------------

        #-------------------------------- Initialize base class --------------------------------

        HookBase.__init__( # type: ignore
            self=self,
            value_or_nexus=value,
            logger=logger,
            nexus_manager=nexus_manager,
            preferred_publish_mode=preferred_publish_mode)

        HookWithSetterMixin.__init__( # type: ignore
            self=self)

        HookWithReactionMixin.__init__( # type: ignore
            self=self,
            reaction_callback=reaction_callback)

        HookWithIsolatedValidationMixin.__init__( # type: ignore
            self=self,
            isolated_validation_callback=isolated_validation_callback)

        #-------------------------------- Initialization complete --------------------------------

    #########################################################
    # WritableHookProtocol methods
    #########################################################

    @property
    def value(self) -> T:
        """Get the value (inherited from HookBase but redeclared for setter)."""
        return super().value
    
    @value.setter
    def value(self, value: T) -> None:
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

    #########################################################
    # HasIsolatedValidationHookProtocol methods
    #########################################################

    def _validate_value_in_isolation(self, value: T) -> tuple[bool, str]:
        """
        Validate the value in isolation.

        ** This method is not thread-safe and should only be called by the _validate_value_in_isolation method.
        """
        # Delegate to the mixin's implementation
        return HookWithIsolatedValidationMixin._validate_value_in_isolation(self, value) # type: ignore

    #########################################################
    # Str and repr methods
    #########################################################

    def __str__(self) -> str:
        """
        Return a string representation of the hook.
        """
        return f"FloatingHook(value={self.value})"

    def __repr__(self) -> str:
        """
        Return a string representation of the hook.
        """
        return f"FloatingHook(value={self.value})"