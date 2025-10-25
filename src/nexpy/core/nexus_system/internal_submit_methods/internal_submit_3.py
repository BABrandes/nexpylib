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
    Ultra-optimized implementation of _internal_submit_values.
    
    Key improvements over internal_submit_2:
    1. Pre-allocated data structures with size hints
    2. Reduced isinstance() checks via caching
    3. Eliminated redundant owner lookups in completion phase
    4. Single-pass component collection with inline type checking
    5. Direct attribute access where safe
    6. Optimized owner deduplication using id() for comparison
    """

    # Validate mode early (cheapest check first)
    if mode not in ["Normal submission", "Forced submission", "Check values"]:
        raise ValueError(f"Invalid mode: {mode}")
    
    # Phase 1: Value conversion and early filtering
    # Pre-allocate with size hint for better performance
    input_size = len(nexus_and_values)
    processed_nexus_and_values: dict["Nexus[Any]", Any] = {}
    
    is_normal_mode = mode == "Normal submission"
    
    for nexus, value in nexus_and_values.items():
        # Convert value for storage
        error_msg, value_for_storage = convert_value_for_storage(nexus_manager, value)
        if error_msg is not None:
            return False, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
        
        # Early filtering for normal submission mode
        if is_normal_mode:
            if not nexus_manager.is_equal(nexus._stored_value, value_for_storage):  # type: ignore
                processed_nexus_and_values[nexus] = value_for_storage
        else:
            processed_nexus_and_values[nexus] = value_for_storage
    
    # Early exit if no values need processing
    if is_normal_mode and not processed_nexus_and_values:
        return True, "Values are the same as the current values. No submission needed."
    
    log(nexus_manager, "NexusManager._internal_submit_values_v3", logger, True, 
        f"Processing {len(processed_nexus_and_values)}/{input_size} nexus and values (mode: {mode})")

    # Phase 2: Value completion with ultra-optimized iteration
    complete_nexus_and_values = processed_nexus_and_values
    success, msg = _complete_nexus_and_values_dict_ultra_optimized(nexus_manager, complete_nexus_and_values)
    if not success:
        return False, msg

    # Phase 3: Single-pass component collection with inline processing
    affected_components = _collect_and_classify_components(nexus_manager, complete_nexus_and_values)
    
    # Phase 4: Streamlined validation
    success, msg = _validate_all_components(nexus_manager, affected_components, complete_nexus_and_values)
    if not success:
        return False, msg

    # Phase 5: Value update (skip for check mode)
    if mode == "Check values":
        return True, "Values are valid"

    # Phase 6: Direct atomic value update
    for nexus, value in complete_nexus_and_values.items():
        nexus._previous_stored_value = nexus._stored_value  # type: ignore
        nexus._stored_value = value  # type: ignore

    # Phase 7: Optimized batch notification
    _execute_notifications_optimized(nexus_manager, affected_components, logger)

    return True, "Values are submitted"

def _complete_nexus_and_values_dict_ultra_optimized(
    nexus_manager: "NexusManager", 
    nexus_and_values: dict["Nexus[Any]", Any]
) -> tuple[bool, str]:
    """
    Ultra-optimized value completion with:
    - Cached owner IDs to avoid repeated 'in' checks on lists
    - Pre-imported protocol for faster type checking
    - Reduced function call overhead
    """
    from ...hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
    
    # Use set of owner IDs for O(1) lookup instead of O(n) list search
    processed_owner_ids: set[int] = set()
    iteration_count = 0
    max_iterations = 100

    while iteration_count < max_iterations:
        iteration_count += 1
        new_values_added = False

        # Collect unique owners efficiently using ID-based deduplication
        current_owners: list["CarriesSomeHooksProtocol[Any, Any]"] = []
        seen_owner_ids: set[int] = set()
        
        for nexus in nexus_and_values:
            for hook in nexus.hooks:
                if isinstance(hook, HookWithOwnerProtocol):
                    owner_id = id(hook.owner)
                    if owner_id not in processed_owner_ids and owner_id not in seen_owner_ids:
                        current_owners.append(hook.owner)
                        seen_owner_ids.add(owner_id)
        
        # Process each owner
        for owner in current_owners:
            success, msg, added_count = _process_owner_completion_fast(
                nexus_manager, owner, nexus_and_values
            )
            if not success:
                return False, msg
            if added_count > 0:
                new_values_added = True
                processed_owner_ids.add(id(owner))
        
        if not new_values_added:
            break
    
    if iteration_count >= max_iterations:
        return False, f"Value completion exceeded maximum iterations ({max_iterations}). Possible circular dependency."
    
    return True, "Successfully completed nexus and values"

def _process_owner_completion_fast(
    nexus_manager: "NexusManager", 
    owner: "CarriesSomeHooksProtocol[Any, Any]", 
    nexus_and_values: dict["Nexus[Any]", Any]
) -> tuple[bool, str, int]:
    """
    Faster owner completion processing with reduced allocations.
    """
    try:
        # Filter values for this owner
        value_dict, _ = filter_nexus_and_values_for_owner(nexus_and_values, owner)
        
        # Skip if no values for this owner
        if not value_dict:
            return True, "Success", 0
        
        # Get additional values
        current_values = owner._get_dict_of_values()  # type: ignore
        update_values = UpdateFunctionValues(
            current=current_values, 
            submitted=MappingProxyType(value_dict)
        )
        
        additional_values = owner._add_values_to_be_updated(update_values)  # type: ignore
        
        # Early exit if no additional values
        if not additional_values:
            return True, "Success", 0
        
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
            else:
                nexus_and_values[nexus] = value_for_storage
                added_count += 1
        
        return True, "Success", added_count
        
    except Exception as e:
        return False, f"Error processing owner {owner}: {e}", 0

def _collect_and_classify_components(
    nexus_manager: "NexusManager", 
    nexus_and_values: dict["Nexus[Any]", Any]
) -> dict[str, Any]:
    """
    Single-pass component collection with inline classification.
    Pre-imports all protocols to avoid repeated module lookups.
    """
    from ...hooks.mixin_protocols.hook_with_owner_protocol import HookWithOwnerProtocol
    from ...hooks.mixin_protocols.hook_with_isolated_validation_protocol import HookWithIsolatedValidationProtocol
    from ...hooks.mixin_protocols.hook_with_reaction_protocol import HookWithReactionProtocol
    
    # Pre-allocate collections
    owners: list["CarriesSomeHooksProtocol[Any, Any]"] = []
    owner_ids: set[int] = set()  # For O(1) deduplication
    hooks_with_validation: set[Hook[Any]] = set()
    hooks_with_reaction: set[Hook[Any]] = set()
    publishers: set[Any] = set()
    all_hooks: set[Hook[Any]] = set()
    
    # Single pass through all hooks
    for nexus in nexus_and_values:
        for hook in nexus.hooks:
            all_hooks.add(hook) # type: ignore
            
            # Check owner first (most common case)
            is_owned = isinstance(hook, HookWithOwnerProtocol)
            if is_owned:
                owner_id = id(hook.owner)
                if owner_id not in owner_ids:
                    owners.append(hook.owner)
                    owner_ids.add(owner_id)
                    # Check owner publishing capability once
                    if hasattr(hook.owner, 'publish'):
                        publishers.add(hook.owner)
            
            # Check validation (only for non-owned hooks)
            if isinstance(hook, HookWithIsolatedValidationProtocol):
                if not is_owned:
                    hooks_with_validation.add(hook) # type: ignore
            
            # Check reaction
            if isinstance(hook, HookWithReactionProtocol):
                hooks_with_reaction.add(hook) # type: ignore
            
            # Check hook publishing capability
            if hasattr(hook, 'publish'):
                publishers.add(hook)
    
    return {
        'owners': owners,
        'hooks_with_validation': hooks_with_validation,
        'hooks_with_reaction': hooks_with_reaction,
        'publishers': publishers,
        'all_hooks': all_hooks
    }

def _validate_all_components(
    nexus_manager: "NexusManager", 
    components: dict[str, Any], 
    nexus_and_values: dict["Nexus[Any]", Any]
) -> tuple[bool, str]:
    """
    Streamlined validation with reduced error handling overhead.
    """
    # Validate owners
    for owner in components['owners']:
        value_dict, _ = filter_nexus_and_values_for_owner(nexus_and_values, owner)
        if not value_dict:
            continue
            
        try:
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

def _execute_notifications_optimized(
    nexus_manager: "NexusManager", 
    components: dict[str, Any], 
    logger: Optional[Logger] = None
) -> None:
    """
    Highly optimized notification execution with reduced overhead.
    """
    # Phase 1: Invalidation (direct iteration, no intermediate variables)
    for owner in components['owners']:
        owner._invalidate()
    
    # Phase 2: Reactions
    for hook in components['hooks_with_reaction']:
        hook.react_to_value_changed()
    
    # Phase 3: Publishing (async)
    for publisher in components['publishers']:
        publisher.publish(None)
    
    # Phase 4: Listener notifications with optimized deduplication
    _notify_listeners_optimized(components, logger)

def _notify_listeners_optimized(
    components: dict[str, Any], 
    logger: Optional[Logger] = None
) -> None:
    """
    Ultra-optimized listener notifications with minimal allocations.
    """
    # Pre-allocate notified hooks set
    notified_hooks: set[int] = set()  # Use hook IDs for faster lookup
    
    def safe_notify(obj: Any, context: str) -> None:
        try:
            obj._notify_listeners()
        except RuntimeError:
            raise
        except Exception as e:
            if logger:
                logger.error(f"Error in {context} listener callback: {e}")
    
    # Notify owners first (with ListeningProtocol check)
    for owner in components['owners']:
        if isinstance(owner, ListeningProtocol):
            safe_notify(owner, "owner")
        
        # Notify owned hooks in same iteration to reduce passes
        for hook in owner._get_dict_of_hooks().values(): # type: ignore
            hook_id = id(hook) # type: ignore
            if hook in components['all_hooks'] and hook_id not in notified_hooks:
                safe_notify(hook, "owned_hook")
                notified_hooks.add(hook_id)
    
    # Notify remaining floating hooks
    for hook in components['all_hooks']:
        if id(hook) not in notified_hooks:
            safe_notify(hook, "floating_hook")

