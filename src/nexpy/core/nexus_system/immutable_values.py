"""
Immutable Values - Utilities for making values immutable for storage

This module provides utilities to ensure values stored in the nexus system
are immutable, preventing accidental modification and ensuring data integrity.

The module organizes conversions into 4 type categories:
1. Items: Primitives and frozen dataclasses
2. Sequences: Lists and tuples
3. Dictionaries: Dicts and mappings
4. Sets: Sets and frozensets

The system is extensible - custom immutable types can be registered via NexusManager.
"""

from typing import Any, Sequence, Mapping, TYPE_CHECKING, Optional
from collections.abc import Set as AbstractSet
import dataclasses
from decimal import Decimal
from fractions import Fraction
from datetime import datetime, date, time, timedelta, timezone
from enum import Enum
from uuid import UUID

from immutables import Map

if TYPE_CHECKING:
    from .nexus_manager import NexusManager


########################################################
# Standard Immutable Types Registry
########################################################

# Standard library immutable types that should pass through unchanged
_STANDARD_IMMUTABLE_TYPES = (
    # Core primitives
    int, float, str, bool, type(None), bytes, complex,
    # Numeric types
    Decimal, Fraction,
    # Date/time types
    datetime, date, time, timedelta, timezone,
    # Other standard immutable types
    range,
    UUID,
    # Note: Enum is handled separately since it's a metaclass
)


########################################################
# Items (Primitives + Frozen Dataclasses + Standard Types)
########################################################

def check_and_convert_item_to_immutable(value: Any) -> tuple[Optional[str], Any]:
    """
    Check and convert primitive items to immutable form.
    
    Handles ONLY known types:
    - Primitives: int, float, str, bool, None, bytes, complex
    - Standard library: Decimal, Fraction, datetime types, UUID, range
    - Enum types
    - Frozen dataclasses
    
    Note: Custom registered types are checked at a higher level in check_and_convert_to_immutable()
    
    Returns:
        tuple[Optional[str], Any]: (error_message, immutable_value)
            - If error_message is None: conversion successful
            - If error_message is str: conversion failed with reason
    """
    # Standard immutable types (including primitives and stdlib types)
    if isinstance(value, _STANDARD_IMMUTABLE_TYPES):
        return None, value
    
    # Enum types (special handling since Enum is a metaclass)
    if isinstance(value, Enum):
        return None, value
    
    # Check if it is a frozen dataclass
    if dataclasses.is_dataclass(value):
        if hasattr(value, '__dataclass_params__'):
            if getattr(value.__dataclass_params__, 'frozen', False):  # type: ignore
                return None, value
            else:
                # Non-frozen dataclass - reject it
                error_msg = (
                    f"Dataclass {type(value).__name__} is not frozen. "
                    f"Only frozen dataclasses can be made immutable. "
                    f"Use @dataclass(frozen=True) decorator."
                )
                return error_msg, None
    
    return f"Value of type {type(value).__name__} is not a known immutable item type", None


def convert_item_from_immutable(value: Any) -> Any:
    """Convert from immutable form (items are unchanged)."""
    return value


########################################################
# Sequences (List → Tuples → List)
########################################################

def check_and_convert_sequence_to_immutable(value: Sequence[Any], nexus_manager: "NexusManager | None" = None) -> tuple[Optional[str], tuple[Any, ...]]:
    """
    Check and convert sequences to immutable form.
    
    Handles: list → tuple (recursive), tuple (recursive check)
    Note: Recursively converts all elements to immutable form
    
    Returns:
        tuple[Optional[str], tuple]: (error_message, immutable_value)
            - If error_message is None: conversion successful
            - If error_message is str: conversion failed with reason
    """
    if isinstance(value, list):
        # Recursively convert all elements
        list_items: list[Any] = []
        for item in value:
            error_msg, immutable_item = check_and_convert_to_immutable(item, nexus_manager)
            if error_msg is not None:
                return f"List contains unconvertible item: {error_msg}", ()
            list_items.append(immutable_item)
        return None, tuple(list_items)
    elif isinstance(value, tuple):
        # Recursively convert all elements to ensure full immutability
        tuple_items: list[Any] = []
        for item in value:
            error_msg, immutable_item = check_and_convert_to_immutable(item, nexus_manager)
            if error_msg is not None:
                return f"Tuple contains unconvertible item: {error_msg}", ()
            tuple_items.append(immutable_item)
        return None, tuple(tuple_items)
    else:
        return f"Value of type {type(value).__name__} is not a known sequence type", ()


def convert_sequence_from_immutable(value: tuple[Any, ...]) -> list[Any]:
    """Convert from immutable tuple to list."""
    return list(value)

########################################################
# Dictionaries (Dict → immutables.Map)
########################################################

def check_and_convert_dictionary_to_immutable(value: Mapping[Any, Any], nexus_manager: "NexusManager | None" = None) -> tuple[Optional[str], Map[Any, Any]]:
    """
    Check and convert dictionaries to immutable form.
    
    Handles: dict → immutables.Map (recursive), Map (already immutable)
    Note: Recursively converts both keys and values to immutable form
    
    Returns:
        tuple[Optional[str], Map]: (error_message, immutable_value)
            - If error_message is None: conversion successful
            - If error_message is str: conversion failed with reason
    """
    if isinstance(value, Map):
        # Already an immutable Map
        return None, value
    
    if isinstance(value, dict):
        # Recursively convert keys and values
        immutable_dict: dict[Any, Any] = {}
        for k, v in value.items():
            # Ensure keys are immutable
            key_error, immutable_key = check_and_convert_to_immutable(k, nexus_manager)
            if key_error is not None:
                return f"Dictionary key cannot be made immutable: {key_error}", Map()
            
            # Convert values to immutable
            val_error, immutable_value = check_and_convert_to_immutable(v, nexus_manager)
            if val_error is not None:
                return f"Dictionary value cannot be made immutable: {val_error}", Map()
            
            immutable_dict[immutable_key] = immutable_value
        return None, Map(immutable_dict)
    
    # For other Mapping types, try to convert via dict
    try:
        temp_dict = dict(value)
        immutable_dict = {}
        for k, v in temp_dict.items():
            key_error, immutable_key = check_and_convert_to_immutable(k, nexus_manager)
            if key_error is not None:
                return f"Dictionary key cannot be made immutable: {key_error}", Map()
            
            val_error, immutable_value = check_and_convert_to_immutable(v, nexus_manager)
            if val_error is not None:
                return f"Dictionary value cannot be made immutable: {val_error}", Map()
            
            immutable_dict[immutable_key] = immutable_value
        return None, Map(immutable_dict)
    except (TypeError, ValueError) as e:
        return f"Cannot convert mapping to immutable: {e}", Map()


def convert_dictionary_from_immutable(value: Map[Any, Any]) -> dict[Any, Any]:
    """Convert from immutable Map to dict."""
    return dict(value)


########################################################
# Sets (AbstractSet → frozenset)
########################################################

def check_and_convert_set_to_immutable(value: AbstractSet[Any], nexus_manager: "NexusManager | None" = None) -> tuple[Optional[str], frozenset[Any]]:
    """
    Check and convert sets to immutable form.
    
    Handles: set → frozenset (recursive), frozenset (already immutable)
    Note: Recursively converts all elements to immutable form
    
    Returns:
        tuple[Optional[str], frozenset]: (error_message, immutable_value)
            - If error_message is None: conversion successful
            - If error_message is str: conversion failed with reason
    """
    if isinstance(value, frozenset):
        # Already immutable, but verify elements are immutable
        immutable_items: list[Any] = []
        for item in value:
            error_msg, immutable_item = check_and_convert_to_immutable(item, nexus_manager)
            if error_msg is not None:
                return f"Frozenset contains unconvertible item: {error_msg}", frozenset()
            immutable_items.append(immutable_item)
        return None, frozenset(immutable_items)
    
    if isinstance(value, set):
        # Convert elements to immutable and create frozenset
        immutable_items = []
        for item in value:
            error_msg, immutable_item = check_and_convert_to_immutable(item, nexus_manager)
            if error_msg is not None:
                return f"Set contains unconvertible item: {error_msg}", frozenset()
            immutable_items.append(immutable_item)
        return None, frozenset(immutable_items)
    
    return f"Value of type {type(value).__name__} is not a known set type", frozenset()


def convert_set_from_immutable(value: frozenset[Any]) -> set[Any]:
    """Convert from immutable frozenset to set."""
    return set(value)


########################################################
# Main Conversion Function
########################################################

def check_and_convert_to_immutable(value: Any, nexus_manager: "NexusManager | None" = None) -> tuple[Optional[str], Any]:
    """
    Check and convert a value to immutable form with recursive processing.
    
    Type checking order is critical:
    1. None (special case)
    2. Primitives (int, float, bool, bytes, complex) - BEFORE str check
    3. str - MUST be before Sequence (str is a Sequence!)
    4. Standard library immutable types (Decimal, datetime, Enum, etc.)
    5. Custom registered types (via nexus_manager) - CHECK EARLY!
    6. Frozen dataclasses
    7. Mapping (dict → immutables.Map)
    8. Set (set → frozenset)  
    9. Sequence (list/tuple → tuple)
    
    Args:
        value: The value to make immutable
        nexus_manager: Optional NexusManager with custom immutable type registry
    
    Returns:
        tuple[Optional[str], Any]: (error_message, immutable_value)
            - If error_message is None: conversion successful
            - If error_message is str: conversion failed with reason
    
    Examples:
        >>> check_and_convert_to_immutable(42)
        (None, 42)
        >>> check_and_convert_to_immutable([1, 2, 3])
        (None, (1, 2, 3))
        >>> check_and_convert_to_immutable({'a': 1})
        (None, <immutables.Map({'a': 1})>)
    """
    # None
    if value is None:
        return None, value
    
    # Primitives (check these early)
    if isinstance(value, (int, float, bool, bytes, complex)):
        return None, value
    
    # String - MUST be before Sequence check since str is a Sequence!
    if isinstance(value, str):
        return None, value
    
    # Standard library immutable types (Decimal, datetime, Enum, UUID, etc.)
    if isinstance(value, (_STANDARD_IMMUTABLE_TYPES + (Enum,))):
        return None, value
    
    # Custom registered immutable types - CHECK EARLY!
    if nexus_manager is not None:
        if nexus_manager.is_registered_immutable_type(type(value)): # type: ignore
            return None, value
    
    # Frozen dataclass (via item handler)
    if dataclasses.is_dataclass(value):
        return check_and_convert_item_to_immutable(value)
    
    # Mapping (includes dict, Map, etc.)
    if isinstance(value, Mapping):
        return check_and_convert_dictionary_to_immutable(value, nexus_manager) # type: ignore
    
    # Set (includes set, frozenset)
    if isinstance(value, (set, frozenset)):
        return check_and_convert_set_to_immutable(value, nexus_manager) # type: ignore
    
    # Sequence (includes list, tuple) - AFTER str check!
    if isinstance(value, (list, tuple)):
        return check_and_convert_sequence_to_immutable(value, nexus_manager) # type: ignore
    
    # Unsupported type
    error_msg = (
        f"Value of type {type(value).__name__} cannot be made immutable. "
        f"Supported types: int, float, str, bool, None, bytes, complex, "
        f"frozenset, tuple, dict (→ immutables.Map), list (→ tuple), "
        f"set (→ frozenset), frozen dataclasses, immutables library types, "
        f"and custom registered types."
    )
    return error_msg, None


def convert_from_immutable(value: Any, nexus_manager: "NexusManager | None" = None) -> Any:
    """
    Convert a value from immutable form back to mutable (where applicable).
    
    This is useful for interoperability with code that expects mutable types.
    
    Args:
        value: The immutable value to convert
        nexus_manager: Optional NexusManager (currently unused but kept for API consistency)
    """
    if value is None:
        return value
    elif isinstance(value, (int, float, str, bool, bytes, complex)):
        return value
    elif dataclasses.is_dataclass(value):
        return value
    elif isinstance(value, Map):
        return convert_dictionary_from_immutable(value) # type: ignore
    elif isinstance(value, frozenset):
        return convert_set_from_immutable(value) # type: ignore
    elif isinstance(value, tuple):
        return convert_sequence_from_immutable(value) # type: ignore
    else:
        return value
