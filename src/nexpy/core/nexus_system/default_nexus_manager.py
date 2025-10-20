"""Default nexus manager with built-in value equality callbacks.

This module provides the default NexusManager instance used throughout the observables
library. It includes equality callbacks for common types and optionally integrates with
third-party libraries if they are available.

Configurable Tolerance
----------------------
The floating-point comparison tolerance can be customized by modifying FLOAT_ACCURACY
before creating observables. This affects all float/int comparisons in the system.

Ways to Configure:
    >>> # Method 1: Via core module (recommended for users)
    >>> from observables import core
    >>> core.default_nexus_manager.FLOAT_ACCURACY = 1e-6
    >>> 
    >>> # Method 2: Direct import (for advanced users)
    >>> from observables._utils import default_nexus_manager
    >>> default_nexus_manager.FLOAT_ACCURACY = 1e-12
    >>> 
    >>> # Method 3: Import and modify
    >>> import observables.core as obs_core
    >>> obs_core.default_nexus_manager.FLOAT_ACCURACY = 1e-8
"""

import math

from .nexus_manager import NexusManager

FLOAT_ACCURACY: float = 1e-9
"""Tolerance for floating-point equality comparisons (configurable).

Two floats (or float/int pairs) are considered equal if their absolute difference 
is less than this value. This helps handle floating-point precision issues that can 
arise from arithmetic operations. For example, 0.1 + 0.2 might not exactly equal 
0.3 due to binary representation limitations.

Default Value
-------------
1e-9 (0.000000001) - A balanced choice suitable for most applications.

Common Use Cases
----------------
- UI applications: 1e-6 to 1e-3 (more lenient, ignore minor fluctuations)
- General purpose: 1e-9 to 1e-8 (default, good balance)
- Scientific/High precision: 1e-12 to 1e-15 (very strict)

How to Change
-------------
Modify this value at runtime before creating observables:

    >>> from observables import core
    >>> core.default_nexus_manager.FLOAT_ACCURACY = 1e-6  # More lenient
    
Important Notes
---------------
- This is an absolute tolerance, not relative
- Changes affect all new comparisons immediately (existing observables use the current value)
- For very large or very small numbers, consider implementing custom equality callbacks
  with relative tolerance if needed
"""

# =============================================================================
# Built-in equality callbacks
# =============================================================================

def _value_equality_callback_float(value1: float, value2: float) -> bool:
    """
    Check equality for float values with special NaN handling and tolerance.
    
    Args:
        value1: First float value to compare
        value2: Second float value to compare
        
    Returns:
        True if values are equal, False otherwise.
        Note: NaN is considered equal to NaN for the purposes of this library.
    """
    if abs(value1 - value2) < FLOAT_ACCURACY:
        return True
    if math.isnan(value1) and math.isnan(value2):
        return True
    if math.isnan(value1) or math.isnan(value2):
        return False

    # For all other cases, use regular equality
    return value1 == value2


def _value_equality_callback_int(value1: int, value2: int) -> bool:
    """
    Check equality for int values.
    
    Args:
        value1: First int value to compare
        value2: Second int value to compare
        
    Returns:
        True if values are exactly equal, False otherwise.
    """
    return value1 == value2


def _value_equality_callback_float_int(value1: float, value2: int) -> bool:
    """
    Check equality between float and int values with tolerance.
    
    Args:
        value1: Float value to compare
        value2: Int value to compare
        
    Returns:
        True if values are equal within tolerance, False otherwise.
    """
    if math.isnan(value1):
        return False
    return abs(value1 - value2) < FLOAT_ACCURACY


def _value_equality_callback_int_float(value1: int, value2: float) -> bool:
    """
    Check equality between int and float values with tolerance.
    
    Args:
        value1: Int value to compare
        value2: Float value to compare
        
    Returns:
        True if values are equal within tolerance, False otherwise.
    """
    if math.isnan(value2):
        return False
    return abs(value1 - value2) < FLOAT_ACCURACY


# Build value equality callbacks dictionary
_value_equality_callbacks = {
    (float, float): _value_equality_callback_float,
    (int, int): _value_equality_callback_int,
    (float, int): _value_equality_callback_float_int,
    (int, float): _value_equality_callback_int_float,
}

# =============================================================================
# Optional dependency integrations
# =============================================================================
# Add support for third-party libraries here using try/except ImportError.
# This allows the observables library to work without requiring these
# dependencies, while automatically providing enhanced functionality when
# they are available.
# =============================================================================

# --- united_system integration ---
try:
    from united_system import RealUnitedScalar
    
    def _value_equality_callback_real_united_scalar(value1: RealUnitedScalar, value2: RealUnitedScalar) -> bool:
        """Check equality for RealUnitedScalar values.
        
        Args:
            value1: First RealUnitedScalar value to compare
            value2: Second RealUnitedScalar value to compare
            
        Returns:
            True if values have the same dimension and equal canonical values, False otherwise.
        """
        if value1.dimension != value2.dimension:
            return False
        return _value_equality_callback_float(value1.value_in_canonical_unit(), value2.value_in_canonical_unit())
    
    _value_equality_callbacks[(RealUnitedScalar, RealUnitedScalar)] = _value_equality_callback_real_united_scalar # type: ignore

except ImportError:
    # united_system is not available, skip RealUnitedScalar support
    pass


# --- Add additional optional integrations here ---
# Example:
# try:
#     from some_library import SomeType
#     
#     def _value_equality_callback_some_type(value1: SomeType, value2: SomeType) -> bool:
#         """Check equality for SomeType values."""
#         # Implementation here
#         pass
#     
#     _value_equality_callbacks[(SomeType, SomeType)] = _value_equality_callback_some_type
# except ImportError:
#     pass


# =============================================================================
# Default nexus manager instance
# =============================================================================

DEFAULT_NEXUS_MANAGER: "NexusManager" = NexusManager(
    value_equality_callbacks=_value_equality_callbacks,
    registered_immutable_types=set()
)