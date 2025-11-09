from typing import TYPE_CHECKING, TypeVar, Optional, Mapping, Protocol, Literal, Self
from logging import Logger
from collections.abc import Hashable

from ..core.nexus_system.update_function_values import UpdateFunctionValues
from ..core.nexus_system.nexus import Nexus

if TYPE_CHECKING:
    from .carries_single_hook_protocol import CarriesSingleHookProtocol
    from ..core.nexus_system.nexus_manager import NexusManager
    from ..core.hooks import OwnedHookProtocol, HookProtocol

HK = TypeVar("HK")
HV = TypeVar("HV")

class CarriesSomeHooksProtocol(Hashable, Protocol[HK, HV]):
    """
    Protocol for objects that carry a set of hooks.

    Generic type parameters:
        HK: The type of the hook keys
        HV: The type of the hook values
    """

    #########################################################################
    # Methods to get hooks and values
    #########################################################################

    def _get_hook_by_key(self, key: HK) -> "OwnedHookProtocol[HV, Self]":
        """
        Get a hook by its key.
        """
        ...
    
    def _get_hook_keys(self) -> set[HK]:
        """
        Get all keys of the hooks.
        """
        ...

    def _get_key_by_hook_or_nexus(self, hook_or_nexus: "OwnedHookProtocol[HV, Self]|Nexus[HV]") -> HK:
        """
        Get the key of a hook or nexus.
        """
        ...

    def _get_value_by_key(self, key: HK) -> HV:
        """
        Get a value as a copy by its key.

        ** The returned value is a copy, so modifying it will not modify the observable.
        """
        ...

    def _get_dict_of_hooks(self) ->  "Mapping[HK, OwnedHookProtocol[HV, Self]]":
        """
        Get a dictionary of hooks.
        """
        ...

    def _get_dict_of_values(self) -> Mapping[HK, HV]:
        """
        Get a dictionary of values.

        ** The returned values are copies, so modifying them will not modify the observable.

        Returns:
            A dictionary of keys to values
        """
        ...

    #########################################################################
    # Methods to invalidate and validate
    #########################################################################

    def _get_nexus_manager(self) -> "NexusManager":
        """
        Get the nexus manager that this observable belongs to.
        """
        ...

    def _invalidate(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> tuple[bool, str]:
        """
        Invalidate all hooks.
        """
        ...

    def _validate_complete_values_in_isolation(self, values: Mapping[HK, HV]) -> tuple[bool, str]:
        """
        Check if the values are valid as part of the owner.
        
        Values are provided for all hooks according to get_hook_keys().
        """
        ...

    def _validate_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Check if a value is valid.

        ** This method is not thread-safe and should only be called by the validate_value method.
        """
        ...

    def _submit_value(self, key: HK, value: HV, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """
        Submit a value to the observable.

        ** This method is not thread-safe and should only be called by the validate_value method.
        """
        ...

    #########################################################################
    # Methods to connect and disconnect hooks
    #########################################################################

    def _join(self, source_hook_key: HK, target_hook: "HookProtocol[HV]|CarriesSingleHookProtocol[HV]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a hook to the observable.

        Args:
            source_hook_key: The key of the hook to connect
            target_hook: The hook to connect
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the source hook key is not found in component_hooks or secondary_hooks
        """
        ...

    def _join_many(self, hooks: "Mapping[HK, HookProtocol[HV]]", initial_sync_mode: Literal["use_caller_value", "use_target_value"]) -> None:
        """
        Connect a list of hooks to the observable.

        Args:
            hooks: A mapping of keys to hooks
            initial_sync_mode: The initial synchronization mode

        Raises:
            ValueError: If the key is not found in component_hooks or secondary_hooks
        """
        ...

    def _isolate(self, key: Optional[HK]) -> None:
        """
        Isolate a hook by its key.

        Args:
            key: The key of the hook to isolate. If None, all hooks will be isolated.
        """
        ...

    def _destroy(self) -> None:
        """
        Destroy the observable by disconnecting all hooks, removing listeners, and invalidating.
        
        This method should be called before the observable is deleted to ensure proper
        memory cleanup and prevent memory leaks. After calling this method, the observable
        should not be used anymore as it will be in an invalid state.
        
        Example:
            >>> obs = XValue("test")
            >>> obs.cleanup()  # Properly clean up before deletion
            >>> del obs
        """
        ...

    #########################################################################
    # Main sync system methods
    #########################################################################

    def _add_values_to_be_updated(self, values: UpdateFunctionValues[HK, HV]) -> Mapping[HK, HV]:
        """
        Add values to be updated.
        
        Args:
            values: UpdateFunctionValues containing current (complete state) and submitted (being updated) values
            
        Returns:
            Mapping of additional hook keys to values that should be updated
        """
        ...