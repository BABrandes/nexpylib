"""
Original implementation of _internal_submit_values.

This is the original implementation that was moved from nexus_manager.py
to preserve it for comparison and reference.
"""

from typing import Any, Literal, Mapping, Optional, TYPE_CHECKING
from logging import Logger

from ..nexus import Nexus
from ...hooks.protocols.hook_protocol import HookProtocol
from ...auxiliary.listenable_protocol import ListenableProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from .helper_methods import convert_value_for_storage, filter_nexus_and_values_for_owner, complete_nexus_and_values_for_owner, complete_nexus_and_values_dict

if TYPE_CHECKING:
    from ..nexus_manager import NexusManager


def internal_submit_values(
    nexus_manager: "NexusManager",
    nexus_and_values: Mapping["Nexus[Any]", Any], 
    mode: Literal["Normal submission", "Forced submission", "Check values"], 
    logger: Optional[Logger] = None
) -> tuple[bool, str]:
    """
    Original internal implementation of submit_values.

    This method is not thread-safe and should only be called by the submit_values method.
    
    This method is a crucial part of the hook connection process:
    1. Get the two nexuses from the hooks to connect
    2. Submit one of the hooks' value to the other nexus (this method)
    3. If successful, both nexus must now have the same value
    4. Merge the nexuses to one -> Connection established!
    
    Parameters
    ----------
    mode : Literal["Normal submission", "Forced submission", "Check values"]
        Controls the submission behavior:
        - "Normal submission": Only submits values that differ from current values
        - "Forced submission": Submits all values regardless of equality
        - "Check values": Only validates without updating
    """

    from ...hooks.protocols.isolated_validatable_hook_protocol import IsolatedValidatableHookProtocol
    from ...hooks.protocols.reactive_hook_protocol import ReactiveHookProtocol
    from ...hooks.protocols.owned_hook_protocol import OwnedHookProtocol

    #########################################################
    # Check if the values are immutable
    #########################################################

    _nexus_and_values: dict["Nexus[Any]", Any] = {}
    for nexus, value in nexus_and_values.items():
        error_msg, value_for_storage = convert_value_for_storage(nexus_manager, value)
        if error_msg is not None:
            return False, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
        _nexus_and_values[nexus] = value_for_storage

    #########################################################
    # Check if the values are even different from the current values
    #########################################################

    match mode:
        case "Normal submission":
            # Filter to only values that differ from current (using immutable versions)
            filtered_nexus_and_values: dict["Nexus[Any]", Any] = {}
            for nexus, value in _nexus_and_values.items():
                if not nexus_manager.is_equal(nexus._stored_value, value): # type: ignore
                    filtered_nexus_and_values[nexus] = value
            
            _nexus_and_values = filtered_nexus_and_values

            if len(_nexus_and_values) == 0:
                return True, "Values are the same as the current values. No submission needed."

        case "Forced submission":
            # Use all immutable values
            pass

        case "Check values":
            # Use all immutable values
            pass

        case _: # type: ignore
            raise ValueError(f"Invalid mode: {mode}")

    #########################################################
    # Value Completion
    #########################################################

    # Step 1: Update the nexus and values
    complete_nexus_and_values: dict["Nexus[Any]", Any] = {}
    complete_nexus_and_values.update(_nexus_and_values)
    success, msg = complete_nexus_and_values_dict(nexus_manager, complete_nexus_and_values)
    if success == False:
        return False, msg

    # Step 2: Collect the owners and floating hooks to validate, react to, and notify
    affected_hooks: set[HookProtocol[Any]] = set()
    affected_owners: set["CarriesSomeHooksProtocol[Any, Any]"] = set()
    for nexus, value in complete_nexus_and_values.items():
        for hook in nexus.hooks:
            affected_hooks.add(hook)
            if isinstance(hook, OwnedHookProtocol):
                owner: "CarriesSomeHooksProtocol[Any, Any]" = hook.get_owner() # type: ignore
                affected_owners.add(owner) # type: ignore

    #########################################################
    # Value Validation
    #########################################################

    # Step 3: Validate the values
    for owner in affected_owners:
        value_dict, _ = filter_nexus_and_values_for_owner(complete_nexus_and_values, owner)
        complete_nexus_and_values_for_owner(value_dict, owner, as_reference_values=True)
        try:
            success, msg = owner._validate_complete_values_in_isolation(value_dict) # type: ignore
        except Exception as e:
            return False, f"Error in '_validate_complete_values_in_isolation' of owner '{owner}': {e} (value_dict: {value_dict})"
        if success == False:    
            return False, msg
    for isolated_validatable_hook in affected_hooks:
        assert isinstance(isolated_validatable_hook, IsolatedValidatableHookProtocol)
        try:
            success, msg = isolated_validatable_hook._validate_value_in_isolation(complete_nexus_and_values[isolated_validatable_hook._get_nexus()]) # type: ignore
        except Exception as e:
            return False, f"Error in 'validate_value_in_isolation' of isolated validatable hook '{isolated_validatable_hook}': {e} (complete_nexus_and_values: {complete_nexus_and_values})"
        if success == False:
            return False, msg

    #########################################################
    # Value Update
    #########################################################

    if mode == "Check values":
        return True, "Values are valid"

    # Step 4: Update each nexus with the new value
    for nexus, value in complete_nexus_and_values.items():
        nexus._previous_stored_value = nexus._stored_value # type: ignore
        nexus._stored_value = value # type: ignore

    #########################################################
    # Invalidation, Reaction, and Notification
    #########################################################

    # --------- Take care of the affected hooks ---------

    for hook in affected_hooks:
        # Reaction
        if isinstance(hook, ReactiveHookProtocol):
            hook._react_to_value_change(raise_error_mode="warn") # type: ignore
        # Publication
        if isinstance(hook, PublisherProtocol): # type: ignore
            hook.publish(None, raise_error_mode="warn")
        # Listener notification
        if isinstance(hook, ListenableProtocol): # type: ignore
            hook._notify_listeners(raise_error_mode="warn") # type: ignore

    # --------- Take care of the affected owners ---------

    # Step 5a: Invalidate the affected owners
    for owner in affected_owners:
        # Invalidation
        owner._invalidate(raise_error_mode="warn") # type: ignore
        # Publication
        if isinstance(owner, PublisherProtocol):
            owner.publish(None, raise_error_mode="warn")
        # Listener notification
        if isinstance(owner, ListeningProtocol): # type: ignore
            owner._notify_listeners(raise_error_mode="warn") # type: ignore

    #########################################################

    return True, "Values are submitted"
