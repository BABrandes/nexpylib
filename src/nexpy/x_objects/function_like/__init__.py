"""
Function-like X Objects

This module contains X objects that behave like functions, including:
- XFunction: Bidirectional function with validation
- XOneWayFunction: One-way transformation function
- FunctionValues: Data structure for function input/output values
"""

from .function_values import FunctionValues
from .x_function import XFunction
from .x_one_way_function import XOneWayFunction

__all__ = [
    'FunctionValues',
    'XFunction', 
    'XOneWayFunction',
]
