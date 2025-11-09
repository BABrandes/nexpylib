"""
NexPy Core - Advanced API for extending the library

⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY
This library is under active development. API may change without notice.
Use for experimental and development purposes only.

This module contains the core components and base classes for building on top of the 
NexPy library. These are lower-level abstractions meant for users who want to 
create custom reactive types or extend the library's functionality.

Core Components:
- Nexus: Central storage for actual data values
- NexusManager: Central coordinator for transitive synchronization
- FloatingHook: Independent writable hook with validation and reaction capabilities
- OwnedReadOnlyHook: Read-only hook owned by X objects
- OwnedWritableHook: Writable hook owned by X objects
- HookProtocol: Core hook protocol
- OwnedHookProtocol: Protocol for hooks with ownership
- WritableHookProtocol: Protocol for hooks with write access
- ReactiveHookProtocol: Protocol for hooks with reactions
- Subscriber: Asynchronous subscriber for receiving publications
- ListeningMixin/ListeningProtocol: Base classes for listener management

Example Usage with Hook System:
    >>> from nexpy.core import FloatingHook, OwnedWritableHook, XValue
    >>> 
    >>> # Create independent floating hooks
    >>> hook1 = FloatingHook(value=42)
    >>> hook2 = FloatingHook(value=100)
    >>> 
    >>> # Join them together
    >>> hook1.join(hook2)
    >>> print(hook1.value, hook2.value)  # 42 42
    >>> 
    >>> # Create X object with owned writable hook
    >>> value = XValue(42)
    >>> hook = value.value_hook  # OwnedWritableHook
    >>> print(hook.value)  # 42
    >>> hook.value = 100
    >>> print(value.value)  # 100

Advanced Usage with FloatingHook:
    >>> from nexpy.core import FloatingHook
    >>> 
    >>> def validate_value(value):
    ...     return value >= 0, "Value must be non-negative"
    >>> 
    >>> def on_change():
    ...     print("Value changed!")
    ...     return True, "Reaction completed"
    >>> 
    >>> # Create floating hook with validation and reaction
    >>> hook = FloatingHook(
    ...     value=42,
    ...     isolated_validation_callback=validate_value,
    ...     reaction_callback=on_change
    ... )

Configuring Float Tolerance:
    >>> from nexpy import default
    >>> # Adjust tolerance for your use case
    >>> default.FLOAT_ACCURACY = 1e-6  # More lenient for UI
    >>> # This must be done before creating observables

For normal usage of the library, import from the main package:
    >>> from nexpy import XValue, XList
"""

from .nexus_system.nexus import Nexus
from .auxiliary.listenable_mixin import ListenableMixin
from .auxiliary.listenable_protocol import ListenableProtocol
from .nexus_system.nexus_manager import NexusManager
from .publisher_subscriber.subscriber import Subscriber
from .nexus_system.submission_error import SubmissionError
from .hooks import (
    HookProtocol,
    OwnedHookProtocol,
    WritableHookProtocol,
    ReactiveHookProtocol,
    FloatingHook,
    OwnedReadOnlyHook,
    OwnedWritableHook,
    HookBase,
)

# Re-export the module for advanced configuration
# Note: For user-facing configuration, use: from nexpy import default

__all__ = [
    'Nexus',
    'NexusManager',
    'ListenableMixin',
    'ListenableProtocol',
    'Subscriber',
    'SubmissionError',
    'HookProtocol',
    'OwnedHookProtocol',
    'WritableHookProtocol',
    'ReactiveHookProtocol',
    'FloatingHook',
    'OwnedReadOnlyHook',
    'OwnedWritableHook',
    'HookBase',
]

