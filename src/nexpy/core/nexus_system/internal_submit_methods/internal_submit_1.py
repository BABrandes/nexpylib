"""
Original implementation of _internal_submit_values.

This is the original implementation that was moved from nexus_manager.py
to preserve it for comparison and reference.
"""

from typing import Any, Literal, Mapping, Optional, TYPE_CHECKING
from logging import Logger

from ..nexus import Nexus
from ...hooks.hook_aliases import Hook
from ...auxiliary.listening_protocol import ListeningProtocol
from ...publisher_subscriber.publisher_protocol import PublisherProtocol
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ...utils import log
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

    from ...hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
    from ...hooks.mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
    from ...hooks.mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol
    from ...hooks.mixin_protocols.hook_with_connection_protocol import HookWithConnectionProtocol

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

            log(nexus_manager, "NexusManager._internal_submit_values", logger, True, f"Initially {len(nexus_and_values)} nexus and values submitted, after checking for equality {len(_nexus_and_values)}")

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
    owners_that_are_affected: list["CarriesSomeHooksProtocol[Any, Any]"] = []
    hooks_with_validation: set[HookWithIsolatedValidationProtocol[Any]] = set()
    hooks_with_reaction: set[HookWithReactionProtocol] = set()
    publishers: set[PublisherProtocol] = set()
    for nexus, value in complete_nexus_and_values.items():
        for hook in nexus.hooks:
            if isinstance(hook, HookWithReactionProtocol):
                hooks_with_reaction.add(hook)
            if isinstance(hook, HookWithIsolatedValidationProtocol):
                # Hooks that are owned by an observable are validated by the observable. They do not need to be validated in isolation.
                if not isinstance(hook, HookWithOwnerProtocol):
                    hooks_with_validation.add(hook)
            if isinstance(hook, HookWithOwnerProtocol):
                if hook.owner not in owners_that_are_affected:
                    owners_that_are_affected.append(hook.owner)
                if isinstance(hook.owner, PublisherProtocol):
                    publishers.add(hook.owner)
            publishers.add(hook) # type: ignore

    #########################################################
    # Value Validation
    #########################################################

    # Step 3: Validate the values
    for owner in owners_that_are_affected:
        value_dict, _ = filter_nexus_and_values_for_owner(complete_nexus_and_values, owner)
        complete_nexus_and_values_for_owner(value_dict, owner, as_reference_values=True)
        try:
            success, msg = owner._validate_complete_values_in_isolation(value_dict) # type: ignore
        except Exception as e:
            return False, f"Error in '_validate_complete_values_in_isolation' of owner '{owner}': {e} (value_dict: {value_dict})"
        if success == False:    
            return False, msg
    for floating_hook in hooks_with_validation:
        assert isinstance(floating_hook, HookWithConnectionProtocol)
        try:
            success, msg = floating_hook.validate_value_in_isolation(complete_nexus_and_values[floating_hook._get_nexus()]) # type: ignore
        except Exception as e:
            return False, f"Error in 'validate_value_in_isolation' of floating hook '{floating_hook}': {e} (complete_nexus_and_values: {complete_nexus_and_values})"
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

    # Step 5a: Invalidate the affected owners and hooks
    for owner in owners_that_are_affected:
        owner._invalidate() # type: ignore

    # Step 5b: React to the value changes
    for hook in hooks_with_reaction:
        hook.react_to_value_changed()

    # Step 5c: Publish the value changes
    for publisher in publishers:
        publisher.publish(None)

    # Step 5d: Notify the listeners

    # Optimize: Only notify hooks that are actually affected by the value changes
    hooks_to_be_notified: set[Hook[Any]] = set()
    for nexus, value in complete_nexus_and_values.items():
        hooks_of_nexus: set[Hook[Any]] = set(nexus.hooks) # type: ignore
        hooks_to_be_notified.update(hooks_of_nexus)

    def notify_listeners(obj: "ListeningProtocol | Hook[Any]"):
        """
        This method notifies the listeners of an object.
        """

        try:
            obj._notify_listeners() # type: ignore
        except RuntimeError:
            # RuntimeError indicates a programming error (like recursive submit_values)
            # that should not be silently caught - re-raise it immediately
            raise
        except Exception as e:
            if logger is not None:
                logger.error(f"Error in listener callback: {e}")

    # Notify owners and hooks that are owned        
    for owner in owners_that_are_affected:
        if isinstance(owner, ListeningProtocol):
            notify_listeners(owner)
        # Only notify hooks that are actually affected
        for hook in owner._get_dict_of_hooks().values(): # type: ignore
            if hook in hooks_to_be_notified:
                hooks_to_be_notified.remove(hook)
                notify_listeners(hook)

    # Notify the remaining hooks
    for hook in hooks_to_be_notified:
        notify_listeners(hook)

    return True, "Values are submitted"
