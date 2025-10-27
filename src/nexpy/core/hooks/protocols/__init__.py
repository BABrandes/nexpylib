"""
Protocol definitions for hooks.
"""

from .hook_protocol import HookProtocol
from .owned_hook_protocol import OwnedHookProtocol
from .reactive_hook_protocol import ReactiveHookProtocol
from .writable_hook_protocol import WritableHookProtocol
from .isolated_validatable_hook_protocol import IsolatedValidatableHookProtocol

__all__ = [
    'HookProtocol',
    'OwnedHookProtocol',
    'ReactiveHookProtocol',
    'WritableHookProtocol',
    'IsolatedValidatableHookProtocol',
]

