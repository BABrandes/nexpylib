"""
Observables Core - Advanced API for extending the library

⚠️ DEVELOPMENT STATUS: NOT PRODUCTION READY
This library is under active development. API may change without notice.
Use for experimental and development purposes only.

This module contains the core components and base classes for building on top of the 
Observables library. These are lower-level abstractions meant for users who want to 
create custom observable types or extend the library's functionality.

Core Components:
- BaseObservable: Base class for all observable types
- Hook/HookProtocol: Core hook implementations and protocols
- OwnedHook/HookWithOwnerProtocol: Owned hook implementations and protocols
- FloatingHook: Advanced hook with validation and reaction capabilities
- Nexus: Central storage for actual data values
- BaseCarriesHooks/CarriesSomeHooksProtocol: Base classes for hook carriers
- HookWithIsolatedValidationProtocol: Protocol for hooks with custom validation
- HookWithReactionProtocol: Protocol for hooks that react to changes
- BaseListening/BaseListeningProtocol: Base classes for listener management
- DEFAULT_NEXUS_MANAGER: The default nexus manager instance
- default_nexus_manager: Module containing configuration (e.g., FLOAT_ACCURACY)

Example Usage with New Protocol-Based Architecture:
    >>> from observables.core import BaseObservable, OwnedHook, HookWithOwnerProtocol
    >>> 
    >>> # Create a custom observable type using the new architecture
    >>> class MyCustomObservable(BaseObservable):
    ...     def __init__(self, initial_value):
    ...         # Create owned hook
    ...         self._value_hook = OwnedHook(owner=self, initial_value=initial_value)
    ...         super().__init__({"value": self._value_hook})
    ...     
    ...     @property
    ...     def value(self):
    ...         return self._value_hook.value
    ...     
    ...     @value.setter
    ...     def value(self, new_value):
    ...         self._value_hook.submit_value(new_value)
    ...     
    ...     @property
    ...     def value_hook(self) -> HookWithOwnerProtocol[Any]:
    ...         return self._value_hook

Advanced Usage with FloatingHook:
    >>> from observables.core import FloatingHook
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
    >>> from observables import core
    >>> # Adjust tolerance for your use case
    >>> core.default_nexus_manager.FLOAT_ACCURACY = 1e-6  # More lenient for UI
    >>> # This must be done before creating observables

For normal usage of the library, import from the main package:
    >>> from observables import ObservableSingleValue, ObservableList
"""

from ..x_objects_base.carries_some_hooks_base import CarriesSomeHooksBase
from ..x_objects_base.x_complex_base import ComplexObservableBase
from .nexus_system.nexus import Nexus
from ..x_objects_base.carries_some_hooks_protocol import CarriesSomeHooksProtocol
from ..x_objects_base.carries_single_hook_protocol import CarriesSingleHookProtocol
from .auxiliary.listening_base import ListeningBase
from .auxiliary.listening_protocol import ListeningProtocol
from .nexus_system.nexus_manager import NexusManager
from .publisher_subscriber.subscriber import Subscriber
from .nexus_system import default_nexus_manager
from .nexus_system.submission_error import SubmissionError
from .nexus_system.update_function_values import UpdateFunctionValues

# Re-export the module for easy access to configuration
# Users should modify: observables.core.default_nexus_manager.FLOAT_ACCURACY
# or import directly: from observables._utils import default_nexus_manager

DEFAULT_NEXUS_MANAGER = default_nexus_manager.DEFAULT_NEXUS_MANAGER

__all__ = [
    'ComplexObservableBase',
    'Nexus',
    'CarriesSomeHooksBase',
    'CarriesSomeHooksProtocol',
    'CarriesSingleHookProtocol',
    'ListeningBase',
    'ListeningProtocol',
    'NexusManager',
    'DEFAULT_NEXUS_MANAGER',
    'default_nexus_manager',  # Export module for configuration access
    'Subscriber',
    'SubmissionError',
    'UpdateFunctionValues',
]

