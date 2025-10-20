"""
Update Function Values - Parameter object for value update callbacks

This module provides a typed parameter object that standardizes how values
are passed to add_values_to_be_updated callbacks in the observable system.
"""

from typing import Generic, Mapping, TypeVar
from dataclasses import dataclass

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


@dataclass(frozen=True, slots=True)
class UpdateFunctionValues(Generic[K, V]):
    """
    Immutable container for values passed to add_values_to_be_updated callbacks.
    
    This provides a clean, typed interface for accessing both current (complete state)
    values and submitted (being updated) values in add_values_to_be_updated callbacks.
    
    Attributes:
        current: The complete current state of all values for the owner.
                 This contains all hook keys with their current values, providing
                 full context for determining what additional values need updating.
        submitted: The values that are being submitted/updated.
                   This is a subset of keys, containing only the values that are
                   part of the current submission and need to be processed.
    
    Note: The parameter order (current, submitted) matches the natural flow where
          you first consider the complete current state, then look at what's being
          submitted to determine what additional updates are needed.
    
    Example:
        >>> def add_values_to_be_updated(
        ...     self,
        ...     values: UpdateFunctionValues[str, int]
        ... ) -> Mapping[str, int]:
        ...     # Access complete current state
        ...     current_total = values.current.get('total', 0)
        ...     
        ...     # Check what's being submitted
        ...     if 'item_value' in values.submitted:
        ...         # Return additional values that need updating
        ...         return {'total': current_total + values.submitted['item_value']}
        ...     return {}
    """
    
    current: Mapping[K, V]
    submitted: Mapping[K, V]
    
    def __repr__(self) -> str:
        """Return a readable representation."""
        return f"UpdateFunctionValues(current={dict(self.current)}, submitted={dict(self.submitted)})"

