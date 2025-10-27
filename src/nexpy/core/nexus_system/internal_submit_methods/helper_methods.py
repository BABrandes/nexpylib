"""
Shared helper methods for internal submit implementations.

This module contains helper methods that are used by both internal_submit_1.py and internal_submit_2.py
to avoid code duplication and ensure consistency.
"""

from typing import Any, Optional, Mapping, TYPE_CHECKING
from types import MappingProxyType

from ...hooks.protocols.hook_protocol import HookProtocol

if TYPE_CHECKING:
    from ..nexus_manager import NexusManager
    from ..nexus import Nexus
    from ....foundations.carries_some_hooks_protocol import CarriesSomeHooksProtocol


def convert_value_for_storage(nexus_manager: "NexusManager", value: Any) -> tuple[Optional[str], Any]:
    """
    Convert a value for storage in a Nexus.
    
    Currently disabled - values are stored as-is without conversion.
    
    Args:
        nexus_manager: The nexus manager instance
        value: The value to convert
        
    Returns:
        A tuple of (error_message, converted_value)
    """
    # Immutability system disabled - pass through values as-is
    return None, value


def filter_nexus_and_values_for_owner(nexus_and_values: dict["Nexus[Any]", Any], owner: "CarriesSomeHooksProtocol[Any, Any]") -> tuple[dict[Any, Any], dict[Any, HookProtocol[Any]]]:
    """
    Extract the value and hook dict from the nexus and values dictionary for a specific owner.
    
    This method filters the nexus and values dictionary to only include values which the owner has a hook for. 
    It then finds the hook keys for the owner and returns the value and hook dict for these keys.

    Args:
        nexus_and_values: The nexus and values dictionary
        owner: The owner to filter for

    Returns:
        A tuple containing the value and hook dict corresponding to the owner
    """
    from ...hooks.protocols.owned_hook_protocol import OwnedHookProtocol
    from ...hooks.protocols.hook_protocol import HookProtocol

    key_and_value_dict: dict[Any, Any] = {}
    key_and_hook_dict: dict[Any, HookProtocol[Any]] = {}
    for nexus, value in nexus_and_values.items():
        for hook in nexus.hooks:
            if isinstance(hook, OwnedHookProtocol):
                if hook.get_owner() is owner:
                    hook_key: Any = owner._get_key_by_hook_or_nexus(hook) # type: ignore
                    key_and_value_dict[hook_key] = value
                    key_and_hook_dict[hook_key] = hook
    return key_and_value_dict, key_and_hook_dict


def complete_nexus_and_values_for_owner(value_dict: dict[Any, Any], owner: "CarriesSomeHooksProtocol[Any, Any]", as_reference_values: bool = False) -> None:
    """
    Complete the value dict for an owner.

    Args:
        value_dict: The value dict to complete
        owner: The owner to complete the value dict for
        as_reference_values: If True, the values will be returned as reference values
    """
    for hook_key in owner._get_hook_keys(): # type: ignore
        if hook_key not in value_dict:
            if as_reference_values:
                value_dict[hook_key] = owner._get_value_by_key(hook_key) # type: ignore
            else:
                value_dict[hook_key] = owner._get_value_by_key(hook_key) # type: ignore


def complete_nexus_and_values_dict(nexus_manager: "NexusManager", nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[bool, str]:
    """
    Complete the nexus and values dictionary using add_values_to_be_updated_callback.
    
    This method iteratively calls the add_values_to_be_updated_callback on all
    affected observables to complete missing values. For example, if a dictionary
    value is updated, the dictionary itself must be updated as well.
    
    The process continues until no more values need to be added, ensuring all
    related values are synchronized.
    
    Args:
        nexus_manager: The nexus manager instance
        nexus_and_values: The nexus and values dictionary to complete
        
    Returns:
        A tuple of (success, message)
    """
    def insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values: dict["Nexus[Any]", Any], value_dict: dict[Any, Any], hook_dict: dict[Any, HookProtocol[Any]]) -> tuple[bool, str]:
        """
        Insert the value and hook dict into the nexus and values dictionary.
        
        This method inserts the values from the value dict into the nexus and values dictionary. 
        The hook dict helps to find the hook nexus for each value.
        """
        if value_dict.keys() != hook_dict.keys():
            return False, "Value and hook dict keys do not match"
        for hook_key, value in value_dict.items():
            nexus: Nexus[Any] = hook_dict[hook_key]._get_nexus() # type: ignore
            if nexus in nexus_and_values:
                # The nexus is already in the nexus and values, this is not good. But maybe the associated value is the same?
                current_value: Any = nexus_and_values[nexus]
                # Use proper equality comparison that handles NaN values correctly
                if not nexus_manager.is_equal(current_value, value):
                    return False, f"Hook nexus already in nexus and values and the associated value is not the same! ({current_value} != {value})"
            nexus_and_values[nexus] = value
        return True, "Successfully inserted value and hook dict into nexus and values"

    def update_nexus_and_value_dict(owner: "CarriesSomeHooksProtocol[Any, Any]", nexus_and_values: dict["Nexus[Any]", Any]) -> tuple[Optional[int], str]:
        """
        Update the nexus and values dictionary with the additional nexus and values, if requested by the owner.
        """
        # Step 1: Prepare the value and hook dict to provide to the owner method
        value_dict, hook_dict = filter_nexus_and_values_for_owner(nexus_and_values, owner)

        # Step 2: Get the additional values from the owner method
        current_values_of_owner: Mapping[Any, Any] = owner._get_dict_of_values() # type: ignore
        from ..update_function_values import UpdateFunctionValues
        update_values = UpdateFunctionValues(current=current_values_of_owner, submitted=MappingProxyType(value_dict)) # Wrap the value_dict in MappingProxyType to prevent mutation by the owner function!

        try:
            additional_value_dict: Mapping[Any, Any] = owner._add_values_to_be_updated(update_values) # type: ignore
        except Exception as e:
            return None, f"Error in '_add_values_to_be_updated' of owner '{owner}': {e} (update_values: {update_values})"

        # Step 4: Make the new values ready for the sync system add them to the value and hook dict
        for hook_key, value in additional_value_dict.items():
            error_msg, value_for_storage = convert_value_for_storage(nexus_manager, value)
            if error_msg is not None:
                return None, f"Value of type {type(value).__name__} cannot be converted for storage: {error_msg}"
            value_dict[hook_key] = value_for_storage
            hook_dict[hook_key] = owner._get_hook_by_key(hook_key) # type: ignore

        # Step 5: Insert the value and hook dict into the nexus and values
        number_of_items_before: int = len(nexus_and_values)
        success, msg = insert_value_and_hook_dict_into_nexus_and_values(nexus_and_values, value_dict, hook_dict)
        if success == False:
            return None, msg
        number_of_inserted_items: int = len(nexus_and_values) - number_of_items_before

        # Step 6: Return the nexus and values
        return number_of_inserted_items, "Successfully updated nexus and values"

    from ...hooks.protocols.owned_hook_protocol import OwnedHookProtocol
        
    # This here is the main loop: We iterate over all the hooks to see if they belong to an owner, which require more values to be changed if the current values would change.
    while True:

        # Step 1: Collect the all the owners that need to be checked for additional nexus and values
        owners_to_check_for_additional_nexus_and_values: list["CarriesSomeHooksProtocol[Any, Any]"] = []
        for nexus in nexus_and_values:
            for hook in nexus.hooks:
                if isinstance(hook, OwnedHookProtocol):
                    if hook.get_owner() not in owners_to_check_for_additional_nexus_and_values:
                        owners_to_check_for_additional_nexus_and_values.append(hook.get_owner()) # type: ignore

        # Step 2: Check for each owner if there are additional nexus and values
        number_of_inserted_items: Optional[int] = 0
        for owner in owners_to_check_for_additional_nexus_and_values:
            number_of_inserted_items, msg = update_nexus_and_value_dict(owner, nexus_and_values)
            if number_of_inserted_items is None:
                return False, msg
            if number_of_inserted_items > 0:
                break

        # Step 3: If no additional nexus and values were found, break the loop
        if number_of_inserted_items == 0:
            break

    return True, "Successfully updated nexus and values"
