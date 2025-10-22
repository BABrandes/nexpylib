"""
Foundations - Core abstractions for X objects

This module contains the foundational classes and protocols that form the base
for all X objects in the NexPy library. These are the building blocks that
concrete X object implementations inherit from.

Components:
- XBase: Core base class for all X objects
- XSingletonBase: Base class for single-value X objects
- XCompositeBase: Base class for multi-hook X objects
- XAdapterBase: Base class for type adapter X objects
- CarriesSomeHooksProtocol: Protocol for objects with multiple hooks
- CarriesSingleHookProtocol: Protocol for objects with a single hook
- XObjectSerializableMixin: Mixin for serialization support
"""

from .x_base import XBase
from .x_singleton_base import XSingletonBase
from .x_composite_base import XCompositeBase
from .x_adapter_base import XAdapterBase
from .carries_some_hooks_protocol import CarriesSomeHooksProtocol
from .carries_single_hook_protocol import CarriesSingleHookProtocol
from .x_object_serializable_mixin import XObjectSerializableMixin

__all__ = [
    'XBase',
    'XSingletonBase', 
    'XCompositeBase',
    'XAdapterBase',
    'CarriesSomeHooksProtocol',
    'CarriesSingleHookProtocol',
    'XObjectSerializableMixin',
]
