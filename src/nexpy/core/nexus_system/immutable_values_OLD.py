"""
Immutable Values - Utilities for making values immutable for storage

This module provides utilities to ensure values stored in the nexus system
are immutable, preventing accidental modification and ensuring data integrity.
"""

from typing import Any, TypeVar
from dataclasses import fields, is_dataclass
import immutables


T = TypeVar("T")


# Primitive immutable types that are safe to store as-is
_IMMUTABLE_PRIMITIVES = (
    type(None),
    bool,
    int,
    float,
    str,
    bytes,
    complex,
    frozenset,
)


class ImmutabilityError(TypeError):
    """Raised when a value cannot be made immutable."""
    pass


def is_immutable_type(value: Any) -> bool:
    """
    Check if a value is of an immutable type.
    
    This checks if the value is:
    - A primitive immutable type (int, float, str, bool, None, bytes, complex)
    - An immutable collection from the immutables library
    - A frozen dataclass
    - A tuple (contents are not checked recursively)
    
    Args:
        value: The value to check
        
    Returns:
        True if the value is of an immutable type, False otherwise
        
    Examples:
        >>> is_immutable_type(42)
        True
        >>> is_immutable_type("hello")
        True
        >>> is_immutable_type([1, 2, 3])
        False
        >>> is_immutable_type(immutables.Map({'a': 1}))
        True
    """
    # Check primitives
    if isinstance(value, _IMMUTABLE_PRIMITIVES):
        return True
    
    # Check tuple
    if isinstance(value, tuple):
        return True
    
    # Check immutables library types
    if isinstance(value, (immutables.Map,)):
        return True
    
    # Check frozen dataclass
    if is_dataclass(value):
        if hasattr(value, '__dataclass_fields__'):
            # Check if frozen
            if getattr(value.__dataclass_params__, 'frozen', False):  # type: ignore
                return True
    
    return False


def make_immutable(value: T) -> T:
    """
    Convert a value to an immutable form suitable for storage in the nexus system.
    
    This function handles:
    - Primitives (int, float, str, bool, None, bytes, complex): returned as-is (already immutable)
    - Frozen dataclasses: returned as-is (already immutable)
    - immutables.Map and other immutables types: returned as-is (already immutable)
    - dict: converted to immutables.Map (recursively making values immutable)
    - list: converted to tuple (recursively making elements immutable)
    - set: converted to frozenset (recursively making elements immutable)
    - tuple: returned as new tuple with immutable contents
    
    Args:
        value: The value to make immutable
        
    Returns:
        An immutable version of the value
        
    Raises:
        ImmutabilityError: If the value cannot be made immutable (e.g., custom mutable objects)
        
    Examples:
        >>> make_immutable(42)
        42
        >>> make_immutable([1, 2, 3])
        (1, 2, 3)
        >>> make_immutable({'a': 1, 'b': 2})
        <immutables.Map({'a': 1, 'b': 2})>
        >>> make_immutable({1, 2, 3})
        frozenset({1, 2, 3})
        
    Note:
        This function recursively processes nested structures to ensure
        complete immutability. For example, a dict containing lists will
        have those lists converted to tuples.
    """
    # Handle None explicitly
    if value is None:
        return value  # type: ignore
    
    # Check if already immutable primitive
    if isinstance(value, _IMMUTABLE_PRIMITIVES):
        return value
    
    # Handle immutables library types
    if isinstance(value, (immutables.Map,)):
        return value
    
    # Handle frozen dataclass
    if is_dataclass(value):
        if hasattr(value, '__dataclass_fields__'):
            # Check if frozen
            if getattr(value.__dataclass_params__, 'frozen', False):  # type: ignore
                return value
            else:
                raise ImmutabilityError(
                    f"Dataclass {type(value).__name__} is not frozen. "
                    f"Only frozen dataclasses can be made immutable. "
                    f"Use @dataclass(frozen=True) decorator."
                )
    
    # Handle dict -> immutables.Map
    if isinstance(value, dict):
        immutable_dict = {}
        for k, v in value.items():
            # Keys must be immutable
            if not is_immutable_type(k):
                try:
                    k = make_immutable(k)
                except ImmutabilityError:
                    raise ImmutabilityError(
                        f"Dictionary key {k!r} of type {type(k).__name__} cannot be made immutable"
                    )
            # Values should be made immutable
            immutable_dict[k] = make_immutable(v)
        return immutables.Map(immutable_dict)  # type: ignore
    
    # Handle list -> tuple
    if isinstance(value, list):
        return tuple(make_immutable(item) for item in value)  # type: ignore
    
    # Handle set -> frozenset
    if isinstance(value, set):
        immutable_items = []
        for item in value:
            immutable_item = make_immutable(item)
            if not is_immutable_type(immutable_item):
                raise ImmutabilityError(
                    f"Set item {item!r} of type {type(item).__name__} cannot be made immutable"
                )
            immutable_items.append(immutable_item)
        return frozenset(immutable_items)  # type: ignore
    
    # Handle tuple -> ensure contents are immutable
    if isinstance(value, tuple):
        return tuple(make_immutable(item) for item in value)  # type: ignore
    
    # If we get here, the type is not supported
    raise ImmutabilityError(
        f"Value of type {type(value).__name__} cannot be made immutable. "
        f"Supported types: int, float, str, bool, None, bytes, complex, "
        f"frozenset, tuple, dict (→ immutables.Map), list (→ tuple), "
        f"set (→ frozenset), frozen dataclasses, and immutables library types."
    )


def validate_immutable(value: Any) -> tuple[bool, str]:
    """
    Validate that a value is immutable without converting it.
    
    This is useful for checking if a value is already in an acceptable
    immutable form before storage.
    
    Args:
        value: The value to validate
        
    Returns:
        Tuple of (is_valid, message) where is_valid is True if the value
        is immutable, False otherwise. The message provides details about
        why the validation failed.
        
    Examples:
        >>> validate_immutable(42)
        (True, "Value is immutable")
        >>> validate_immutable([1, 2, 3])
        (False, "Value of type list is mutable and must be converted")
    """
    try:
        # Try to check if it's immutable
        if is_immutable_type(value):
            # For tuples, check contents recursively
            if isinstance(value, tuple):
                for item in value:
                    is_valid, msg = validate_immutable(item)
                    if not is_valid:
                        return False, f"Tuple contains mutable item: {msg}"
            return True, "Value is immutable"
        else:
            return False, f"Value of type {type(value).__name__} is mutable and must be converted"
    except Exception as e:
        return False, f"Error validating immutability: {e}"

