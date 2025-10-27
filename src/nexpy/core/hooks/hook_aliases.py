"""
Type aliases for common hook patterns.

This module provides convenient type aliases for frequently used hook types,
making code more readable and reducing verbosity.
"""

from typing import TypeVar, Any

from .protocols.hook_protocol import HookProtocol
from .implementations.owned_writable_hook import OwnedWritableHook
from .implementations.owned_read_only_hook import OwnedReadOnlyHook

T = TypeVar("T")
O = TypeVar("O")

# General hook alias (any hook type)
Hook = HookProtocol

# Read-only hooks (owned by Any by default for flexibility)
ReadOnlyHook = OwnedReadOnlyHook

# Writable hooks (owned by Any by default for flexibility)  
WritableHook = OwnedWritableHook

__all__ = [
    'Hook',
    'ReadOnlyHook',
    'WritableHook',
]

