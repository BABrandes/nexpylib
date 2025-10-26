"""
Hook system for nexpylib.

This module provides a flexible, composable hook architecture for reactive programming.
Hooks are the primary way to create and manage synchronized reactive values in nexpylib.

Architecture:
    - protocols/: Interface definitions (what hooks CAN do)
    - foundation/: Core base implementation
    - mixins/: Reusable behaviors via composition
    - implementations/: Concrete hook types

Main Hook Types:
    - FloatingHook: A writable, reactive hook without an owner
    - OwnedReadOnlyHook: A read-only hook owned by a reactive object
    - OwnedWritableHook: A writable hook owned by a reactive object

Key Protocols:
    - HookProtocol: Core hook interface
    - OwnedHookProtocol: Adds ownership semantics
    - WritableHookProtocol: Adds mutation capability
    - ReactiveHookProtocol: Adds reaction/callback support
"""

# Protocols
from .protocols.hook_protocol import HookProtocol
from .protocols.owned_hook_protocol import OwnedHookProtocol
from .protocols.writable_hook_protocol import WritableHookProtocol
from .protocols.reactive_hook_protocol import ReactiveHookProtocol

# Implementations
from .implementations.floating_hook import FloatingHook
from .implementations.owned_read_only_hook import OwnedReadOnlyHook
from .implementations.owned_writable_hook import OwnedWritableHook

# Foundation (typically internal use, but exposed for advanced users)
from .foundation.hook_base import HookBase

# Mixins (typically internal use, but exposed for extending the system)
from .protocols.isolated_validatable_hook_protocol import IsolatedValidatableHookProtocol
from .mixins.hook_with_owner_mixin import HookWithOwnerMixin
from .mixins.hook_with_reaction_mixin import HookWithReactionMixin
from .mixins.hook_with_setter_mixin import HookWithSetterMixin

__all__ = [
    # Main Protocols (Public API)
    'HookProtocol',
    'OwnedHookProtocol',
    'WritableHookProtocol',
    'ReactiveHookProtocol',
    
    # Main Implementations (Public API)
    'FloatingHook',
    'OwnedReadOnlyHook',
    'OwnedWritableHook',
    
    # Foundation (Advanced API)
    'HookBase',
    
    # Mixins (Advanced API for extending)
    'IsolatedValidatableHookProtocol',
    'HookWithOwnerMixin',
    'HookWithReactionMixin',
    'HookWithSetterMixin',
]

