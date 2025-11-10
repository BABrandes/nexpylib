"""
Adapter X Objects - Type adapters and bridges

This module contains X objects that bridge between incompatible but related types,
enabling connections between hooks that wouldn't normally be type-compatible.

Adapter objects validate and convert values during synchronization to maintain
type safety while providing flexibility.

Available Adapters:
- XOptionalAdapter: Bridges T ↔ Optional[T], blocking None values
- XOptionalPlaceholderAdapter: Bridges Optional[T] ↔ T with placeholder for None
- XIntFloatAdapter: Bridges int ↔ float, validating integer values  
- XSetSequenceAdapter: Bridges AbstractSet ↔ Sequence, validating uniqueness
"""

from .x_optional_adapter import XOptionalAdapter
from .x_optional_placeholder_adapter import XOptionalPlaceholderAdapter
from .x_int_float_adapter import XIntFloatAdapter
from .x_set_sequence_adapter import XSetSequenceAdapter
from .x_sequence_items_adapter import XSequenceItemsAdapter

__all__ = [
    'XOptionalAdapter',
    'XOptionalPlaceholderAdapter',
    'XIntFloatAdapter',
    'XSetSequenceAdapter',
    'XSequenceItemsAdapter',
]
