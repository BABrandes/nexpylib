"""Default configuration and settings for the nexpy library.

This module provides easy access to global configuration settings that affect
the behavior of the library. Settings should be modified before creating observables.

Available Settings:
- FLOAT_ACCURACY: Tolerance for floating-point equality comparisons
- NEXUS_MANAGER: The default nexus manager instance used by all observables

Configuration Functions:
- register_equality_callback(): Register custom equality comparison for types
- clone_manager(): Clone the default manager with all its callbacks
- create_manager(): Create a fresh manager without pre-configured callbacks

Basic Usage:
    >>> from nexpy import default
    >>> 
    >>> # View current float accuracy
    >>> print(default.FLOAT_ACCURACY)
    1e-9
    >>> 
    >>> # Change float accuracy for your application
    >>> default.FLOAT_ACCURACY = 1e-12  # High precision
    >>> 
    >>> # Access the default nexus manager
    >>> manager = default.NEXUS_MANAGER

Advanced Usage - Custom Equality:
    >>> from nexpy import default
    >>> import numpy as np
    >>> 
    >>> # Register custom equality for numpy arrays
    >>> def numpy_array_equal(a, b):
    ...     return np.array_equal(a, b)
    >>> 
    >>> default.register_equality_callback(
    ...     np.ndarray, np.ndarray, numpy_array_equal
    ... )

Common Float Accuracy Values:
- UI applications: 1e-6 to 1e-3 (more lenient, ignore minor fluctuations)
- General purpose: 1e-9 to 1e-8 (default, good balance)
- Scientific/High precision: 1e-12 to 1e-15 (very strict)

Important Notes:
- Changes to FLOAT_ACCURACY take effect immediately for all new comparisons
- FLOAT_ACCURACY uses absolute tolerance, not relative tolerance
- Register custom equality callbacks before creating observables
- Custom callbacks are checked before default equality (==) comparison
"""

import sys
from typing import Any, Callable, Type, Optional, TYPE_CHECKING
from .core.nexus_system import default_nexus_manager

if TYPE_CHECKING:
    from .core.nexus_system.nexus_manager import NexusManager


# ============================================================================
# Configuration Module Implementation
# ============================================================================

class _DefaultConfigModule:
    """Module-like class that provides proper __setattr__ support for FLOAT_ACCURACY."""
    
    def __init__(self) -> None:
        # Store the actual module reference
        object.__setattr__(self, '_module', sys.modules[__name__])
        object.__setattr__(self, '_nexus_manager', default_nexus_manager._DEFAULT_NEXUS_MANAGER)  # type: ignore[reportPrivateUsage]
    
    @property
    def FLOAT_ACCURACY(self) -> float:
        """Get the current float accuracy tolerance."""
        return default_nexus_manager.FLOAT_ACCURACY
    
    @FLOAT_ACCURACY.setter
    def FLOAT_ACCURACY(self, value: float):
        """Set the float accuracy tolerance."""
        default_nexus_manager.FLOAT_ACCURACY = value
    
    @property
    def NEXUS_MANAGER(self):
        """Get the default nexus manager."""
        return self._nexus_manager
    
    def register_equality_callback(
        self,
        type1: Type[Any],
        type2: Type[Any],
        callback: Callable[[Any, Any, float], bool]
    ) -> None:
        """Register a custom equality comparison function for specific types.
        
        This allows you to define how values of certain types should be compared
        for equality within the nexpy system. Useful for custom types, numpy arrays,
        dataclasses, etc.
        
        **Required**: All callbacks must accept a `float_accuracy` parameter:
        
            def my_callback(v1, v2, float_accuracy):
                # float_accuracy is passed from active manager
                return abs(v1 - v2) < float_accuracy
        
        The manager will automatically pass its `FLOAT_ACCURACY` to your callback.
        You can add a default value (e.g., `float_accuracy=1e-9`) for standalone use,
        but the manager will override it with its own setting.
        
        For non-numerical types, you can ignore the parameter:
        
            def id_equal(v1, v2, float_accuracy):
                # Ignore float_accuracy for non-numerical types
                return v1.id == v2.id
        
        Args:
            type1: First type in the comparison pair
            type2: Second type in the comparison pair
            callback: Function that takes (value1, value2, float_accuracy) and returns bool
                     The float_accuracy parameter is required (but can have a default value)
            
        Example with float_accuracy (recommended for numerical types):
            >>> from nexpy import default
            >>> from dataclasses import dataclass
            >>> 
            >>> @dataclass
            >>> class Vector:
            ...     x: float
            ...     y: float
            >>> 
            >>> def vector_equal(v1, v2, float_accuracy):
            ...     # float_accuracy is passed from active manager
            ...     return (abs(v1.x - v2.x) < float_accuracy and 
            ...             abs(v1.y - v2.y) < float_accuracy)
            >>> 
            >>> default.register_equality_callback(Vector, Vector, vector_equal)
            >>> 
            >>> # When you use a manager with custom tolerance:
            >>> mgr = default.clone_manager(float_accuracy=1e-12)
            >>> # Manager calls: vector_equal(v1, v2, float_accuracy=1e-12)
            >>> # Your callback receives 1e-12, NOT 1e-9!
            
        Example for non-numerical types (ignore float_accuracy):
            >>> from nexpy import default
            >>> from dataclasses import dataclass
            >>> 
            >>> @dataclass
            >>> class Person:
            ...     id: int
            ...     name: str
            >>> 
            >>> def person_equal(p1, p2, float_accuracy):
            ...     # Parameter required, but can be ignored for non-numerical types
            ...     return p1.id == p2.id
            >>> 
            >>> default.register_equality_callback(Person, Person, person_equal)
            
        Example with numpy arrays:
            >>> from nexpy import default
            >>> import numpy as np
            >>> 
            >>> def numpy_equal(a, b, float_accuracy):
            ...     # float_accuracy is passed from active manager
            ...     return np.allclose(a, b, atol=float_accuracy, rtol=0)
            >>> 
            >>> default.register_equality_callback(
            ...     np.ndarray, np.ndarray, numpy_equal
            ... )
            
        Note:
            Register callbacks before creating observables for consistent behavior.
        """
        self._nexus_manager.add_value_equality_callback((type1, type2), callback)
    
    def clone_manager(self, float_accuracy: Optional[float] = None) -> 'NexusManager':
        """Clone the default nexus manager with all its equality callbacks.
        
        This creates a new manager instance with all the same equality callbacks
        as the default manager. The new manager gets its own FLOAT_ACCURACY,
        and the built-in callbacks will automatically use that value.
        
        Args:
            float_accuracy: Optional custom float accuracy for the new manager.
                          If None, the new manager will use the module-level default.
        
        Returns:
            NexusManager: A new manager instance with cloned callbacks
            
        Example:
            >>> from nexpy import default
            >>> 
            >>> # Clone with custom float accuracy
            >>> my_manager = default.clone_manager(float_accuracy=1e-12)
            >>> # Built-in callbacks will use 1e-12!
            >>> 
            >>> # Use with observables
            >>> from nexpy import XValue
            >>> x = XValue(42, nexus_manager=my_manager)
            
        Example with custom callbacks:
            >>> from nexpy import default
            >>> 
            >>> # Clone and add custom callbacks
            >>> my_manager = default.clone_manager()
            >>> my_manager.add_value_equality_callback(MyType, MyType, my_equal_func)
        """
        from .core.nexus_system.nexus_manager import NexusManager
        
        # Get a copy of all callbacks from the default manager
        callbacks = dict(self._nexus_manager._value_equality_callbacks)
        
        # Create new manager with cloned callbacks
        return NexusManager(
            value_equality_callbacks=callbacks,
            registered_immutable_types=set(),
            float_accuracy=float_accuracy
        )
    
    def create_manager(self, float_accuracy: Optional[float] = None) -> 'NexusManager':
        """Create a fresh nexus manager without any pre-configured equality callbacks.
        
        This creates a completely clean manager that only uses default equality (==)
        for all types. Useful when you want full control over equality comparison.
        
        Args:
            float_accuracy: Optional custom float accuracy for the new manager.
                          If None, the new manager will use the module-level default.
        
        Returns:
            NexusManager: A new, empty manager instance
            
        Example:
            >>> from nexpy import default
            >>> 
            >>> # Create clean manager
            >>> clean_manager = default.create_manager()
            >>> 
            >>> # Add only the callbacks you need
            >>> def my_float_equal(a: float, b: float) -> bool:
            ...     return abs(a - b) < 1e-15  # Very strict
            >>> 
            >>> clean_manager.add_value_equality_callback(
            ...     float, float, my_float_equal
            ... )
        """
        from .core.nexus_system.nexus_manager import NexusManager
        
        return NexusManager(
            value_equality_callbacks={},
            registered_immutable_types=set(),
            float_accuracy=float_accuracy
        )
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the original module."""
        return getattr(self._module, name)
    
    def __dir__(self):
        """Return available attributes."""
        return ['FLOAT_ACCURACY', 'NEXUS_MANAGER', 'register_equality_callback'] + dir(self._module)


# Replace the module with our custom class instance
_config_instance = _DefaultConfigModule()
sys.modules[__name__] = _config_instance  # type: ignore

# For type checkers and IDEs, keep these defined
NEXUS_MANAGER = default_nexus_manager._DEFAULT_NEXUS_MANAGER  # type: ignore[reportPrivateUsage]
FLOAT_ACCURACY: float
register_equality_callback = _config_instance.register_equality_callback
clone_manager = _config_instance.clone_manager
create_manager = _config_instance.create_manager

__all__ = [
    'FLOAT_ACCURACY',
    'NEXUS_MANAGER',
    'register_equality_callback',
    'clone_manager',
    'create_manager',
]

