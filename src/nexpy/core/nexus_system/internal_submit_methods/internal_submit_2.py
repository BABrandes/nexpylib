from typing import Any, Literal, Mapping, Optional, TYPE_CHECKING
from types import MappingProxyType
from logging import Logger

from ..nexus import Nexus 
from ...hooks.hook_aliases import Hook
from ...nexus_system.update_function_values import UpdateFunctionValues
from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ...auxiliary.listening_protocol import ListeningProtocol
from ...utils import log
from .helper_methods import convert_value_for_storage, filter_nexus_and_values_for_owner, complete_nexus_and_values_for_owner

if TYPE_CHECKING:
    from ..nexus_manager import NexusManager

def internal_submit_values(
    nexus_manager: "NexusManager",
    nexus_and_values: Mapping["Nexus[Any]", Any],
    mode: Literal["Normal submission", "Forced submission", "Check values"],
    logger: Optional[Logger] = None
    ) -> tuple[bool, str]:
    """
    Alternative implementation of _internal_submit_values with optimizations.
    """

    # Phase 1: Value conversion and early filtering
    processed_nexus_and_values: dict["Nexus[Any]", Any] = {}
    
    for nexus, value in nexus_and_values.items():
        # Convert value for storage
        error_msg, value_for_storage = convert_value_for_storage(nexus_manager, value)
        if error_msg is not None:
            return False, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
        
        # Early filtering for normal submission mode
        if mode == "Normal submission":
            if not nexus_manager.is_equal(nexus._stored_value, value_for_storage):  # type: ignore
                processed_nexus_and_values[nexus] = value_for_storage
        else:
            processed_nexus_and_values[nexus] = value_for_storage
    
    # Early exit if no values need processing
    if mode == "Normal submission" and not processed_nexus_and_values:
        return True, "Values are the same as the current values. No submission needed."
    
    # Validate mode
    if mode not in ["Normal submission", "Forced submission", "Check values"]:
        raise ValueError(f"Invalid mode: {mode}")
    
    log(nexus_manager, "NexusManager._internal_submit_values_alternative", logger, True, 
        f"Processing {len(processed_nexus_and_values)} nexus and values (mode: {mode})")

    # Phase 2: Value completion with optimized iteration
    complete_nexus_and_values = processed_nexus_and_values.copy()
    success, msg = _complete_nexus_and_values_dict_optimized(nexus_manager, complete_nexus_and_values)
    if not success:
        return False, msg

    # Phase 3: Efficient collection of affected components
    affected_components = _collect_affected_components_optimized(nexus_manager, complete_nexus_and_values)
    
    # Phase 4: Batch validation with early exit
    success, msg = _validate_values_batch(nexus_manager, affected_components, complete_nexus_and_values)
    if not success:
        return False, msg

    # Phase 5: Value update (skip for check mode)
    if mode == "Check values":
        return True, "Values are valid"

    # Phase 6: Atomic value update
    _update_nexus_values_atomic(nexus_manager, complete_nexus_and_values)

    # Phase 7: Batch notification and reaction
    _execute_notifications_batch(nexus_manager, affected_components, complete_nexus_and_values, logger)

    return True, "Values are submitted"

def _complete_nexus_and_values_dict_optimized(nexus_manager: "NexusManager", nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[bool, str]:
    """
    Optimized version of value completion with reduced allocations and better iteration.
    """
    from ...hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
    
    # Use lists for owners since they may not be hashable
    processed_owners: list["CarriesSomeHooksProtocol[Any, Any]"] = []
    iteration_count = 0
    max_iterations = 100  # Prevent infinite loops

    while iteration_count < max_iterations:
        iteration_count += 1
        new_values_added = False

        # Collect owners more efficiently
        current_owners: list["CarriesSomeHooksProtocol[Any, Any]"] = []
        for nexus in nexus_and_values:
            for hook in nexus.hooks:
                if isinstance(hook, HookWithOwnerProtocol) and hook.owner not in processed_owners:
                    current_owners.append(hook.owner)
        
        # Process each owner only once per iteration
        for owner in current_owners:
            success, msg, added_count = _process_owner_completion(nexus_manager, owner, nexus_and_values)
            if not success:
                return False, msg
            if added_count > 0:
                new_values_added = True
                processed_owners.append(owner)
        
        if not new_values_added:
            break
    
    if iteration_count >= max_iterations:
        return False, f"Value completion exceeded maximum iterations ({max_iterations}). Possible circular dependency."
    
    return True, "Successfully completed nexus and values"

def _process_owner_completion(nexus_manager: "NexusManager", owner: "CarriesSomeHooksProtocol[Any, Any]", nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[bool, str, int]:
    """
    Process completion for a single owner with optimized error handling.
    """
    try:
        # Filter values for this owner
        value_dict, _ = filter_nexus_and_values_for_owner(nexus_and_values, owner)
        
        # Get additional values
        current_values = owner._get_dict_of_values()  # type: ignore
        update_values = UpdateFunctionValues(
            current=current_values, 
            submitted=MappingProxyType(value_dict)
        )
        
        additional_values = owner._add_values_to_be_updated(update_values)  # type: ignore
        
        # Process additional values
        added_count = 0
        for hook_key, value in additional_values.items():
            error_msg, value_for_storage = convert_value_for_storage(nexus_manager, value)
            if error_msg is not None:
                return False, f"Value conversion error for {hook_key}: {error_msg}", 0
            
            hook = owner._get_hook_by_key(hook_key)  # type: ignore
            nexus = hook._get_nexus()  # type: ignore
            
            # Check for conflicts
            if nexus in nexus_and_values:
                if not nexus_manager.is_equal(nexus_and_values[nexus], value_for_storage):
                    return False, f"Nexus conflict: {nexus_and_values[nexus]} != {value_for_storage}", 0
            
            nexus_and_values[nexus] = value_for_storage
            added_count += 1
        
        return True, "Success", added_count
        
    except Exception as e:
        return False, f"Error processing owner {owner}: {e}", 0

def _collect_affected_components_optimized(nexus_manager: "NexusManager", nexus_and_values: dict["Nexus[Any]", Any]) -> dict[str, Any]:
    """
    Efficiently collect all affected components in a single pass.
    """
    from ...hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
    from ...hooks.mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
    from ...hooks.mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol
    
    components: dict[str, Any] = {
        'owners': [],
        'hooks_with_validation': set(),
        'hooks_with_reaction': set(),
        'publishers': set(),
        'all_hooks': set()
    }
    
    for nexus in nexus_and_values:
        for hook in nexus.hooks:
            components['all_hooks'].add(hook)
            
            if isinstance(hook, HookWithReactionProtocol):
                components['hooks_with_reaction'].add(hook)
            
            if isinstance(hook, HookWithIsolatedValidationProtocol):
                if not isinstance(hook, HookWithOwnerProtocol):
                    components['hooks_with_validation'].add(hook)
            
            if isinstance(hook, HookWithOwnerProtocol):
                if hook.owner not in components['owners']:
                    components['owners'].append(hook.owner)
                if hasattr(hook.owner, 'publish'):
                    components['publishers'].add(hook.owner)
            
            if hasattr(hook, 'publish'):
                components['publishers'].add(hook)
    
    return components

def _validate_values_batch(nexus_manager: "NexusManager", components: dict[str, Any], nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[bool, str]:
    """
    Batch validation with early exit on first failure.
    """

    # Validate owners
    for owner in components['owners']:
        try:
            value_dict, _ = filter_nexus_and_values_for_owner(nexus_and_values, owner)
            complete_nexus_and_values_for_owner(value_dict, owner, as_reference_values=True)
            
            success, msg = owner._validate_complete_values_in_isolation(value_dict)
            if not success:
                return False, f"Owner validation failed: {msg}"
                
        except Exception as e:
            return False, f"Owner validation error: {e}"
    
    # Validate floating hooks
    for hook in components['hooks_with_validation']:
        try:
            nexus = hook._get_nexus()
            value = nexus_and_values[nexus]
            success, msg = hook.validate_value_in_isolation(value)
            if not success:
                return False, f"Hook validation failed: {msg}"
                
        except Exception as e:
            return False, f"Hook validation error: {e}"
    
    return True, "Values are valid"

def _update_nexus_values_atomic(nexus_manager: "NexusManager", nexus_and_values: dict["Nexus[Any]", Any]) -> None:
    """
    Atomically update all nexus values.
    """
    for nexus, value in nexus_and_values.items():
        nexus._previous_stored_value = nexus._stored_value  # type: ignore
        nexus._stored_value = value  # type: ignore

def _execute_notifications_batch(nexus_manager: "NexusManager", components: dict[str, Any], _nexus_and_values: dict["Nexus[Any]", Any], logger: Optional[Logger] = None) -> None:
    """
    Execute all notifications in optimized batches.
    """
    
    # Phase 1: Invalidation
    for owner in components['owners']:
        owner._invalidate()
    
    # Phase 2: Reactions
    for hook in components['hooks_with_reaction']:
        hook.react_to_value_changed()
    
    # Phase 3: Publishing (async)
    for publisher in components['publishers']:
        publisher.publish(None)
    
    # Phase 4: Listener notifications
    _notify_listeners_batch(nexus_manager, components, _nexus_and_values, logger)

def _notify_listeners_batch(nexus_manager: "NexusManager", components: dict[str, Any], _nexus_and_values: dict["Nexus[Any]", Any], logger: Optional[Logger] = None) -> None:
    """
    Batch listener notifications with error handling.
    """
    from ...auxiliary.listening_protocol import ListeningProtocol
    
    def safe_notify(obj: "ListeningProtocol | Hook[Any]", context: str) -> None:
        try:
            obj._notify_listeners()  # type: ignore
        except RuntimeError:
            raise  # Re-raise RuntimeError (programming errors)
        except Exception as e:
            if logger:
                logger.error(f"Error in {context} listener callback: {e}")
    
    # Notify owners first
    for owner in components['owners']:
        if isinstance(owner, ListeningProtocol):
            safe_notify(owner, "owner")
    
    # Notify hooks (avoid duplicates)
    notified_hooks = set[Any]()
    for owner in components['owners']:
        for hook in owner._get_dict_of_hooks().values():
            if hook in components['all_hooks'] and hook not in notified_hooks:
                safe_notify(hook, "owned_hook")
                notified_hooks.add(hook)
    
    # Notify remaining floating hooks
    for hook in components['all_hooks']:
        if hook not in notified_hooks:
            safe_notify(hook, "floating_hook")
