"""
Adapter X Objects - Type adapters and bridges

This module contains X objects that bridge between incompatible but related types,
enabling connections between hooks that wouldn't normally be type-compatible.

Adapter objects validate and convert values during synchronization to maintain
type safety while providing flexibility.

Available Adapters:
- XOptionalAdapter: Bridges T ↔ Optional[T], blocking None values
- XIntFloatAdapter: Bridges int ↔ float, validating integer values  
- XSetSequenceAdapter: Bridges AbstractSet ↔ Sequence, validating uniqueness
"""

from .x_optional_adapter import XOptionalAdapter
from .x_int_float_adapter import XIntFloatAdapter
from .x_set_sequence_adapter import XSetSequenceAdapter

# Backward compatibility aliases
XOptionalTransfer = XOptionalAdapter
XFloatIntTransfer = XIntFloatAdapter
XSetSequenceTransfer = XSetSequenceAdapter
XBlockNone = XOptionalAdapter

__all__ = [
    'XOptionalAdapter',
    'XIntFloatAdapter',
    'XSetSequenceAdapter',
    # Backward compatibility
    'XOptionalTransfer',
    'XFloatIntTransfer',
    'XSetSequenceTransfer',
    'XBlockNone',
]
