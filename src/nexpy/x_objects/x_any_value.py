from typing import Any, Callable, Generic, Optional, TypeVar
from logging import Logger

from ..core.hooks.hook_aliases import Hook, ReadOnlyHook
from ..x_objects_base.x_single_value_base import XValueBase
from ..x_objects_base.carries_single_hook_protocol import CarriesSingleHookProtocol
from ..core.nexus_system.submission_error import SubmissionError
from ..core.nexus_system.nexus_manager import NexusManager
from ..core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

T = TypeVar("T")

class XAnyValue(XValueBase[T], CarriesSingleHookProtocol[T], Generic[T]):

    def __init__(
        self,
        value_or_hook: T | Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T],
        validator: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
    ) -> None: # type: ignore


        # Initialize the base class
        super().__init__(
            value_or_hook=value_or_hook,
            verification_method=validator,
            invalidate_callback=None,
            logger=logger,
            nexus_manager=nexus_manager
        )

    #########################################################
    # Access
    #########################################################

    @property
    def hook(self) -> Hook[T]:
        """
        Get the hook for the value (thread-safe).
        
        This hook can be used for joining operations with other observables.
        """
        with self._lock:
            return self._get_single_hook()

    @property
    def value(self) -> T:
        """
        Get the current value (thread-safe).
        """
        with self._lock:
            return self._get_single_value()

    @value.setter
    def value(self, value: T) -> None:
        """
        Set a new value (thread-safe).
        
        Args:
            new_value: The new value to set
            
        Raises:
            SubmissionError: If validation fails or value cannot be set
        """
        success, msg = self.change_value(value, raise_submission_error_flag=False)
        if not success:
            raise SubmissionError(msg, value, "value")

    def change_value(self, new_value: T, *, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            new_value: The new value to set
            
        Raises:
            SubmissionError: If the new value fails validation
        """
        success, msg = self._submit_value("value", new_value)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, new_value, "value")
        return success, msg

    #########################################################
    # Standard object methods
    #########################################################
    
    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"XAV(value={self.value})"
    
    def __repr__(self) -> str:
        """Return a string representation of the X object."""
        return f"XAnyValue({self.value!r})"
    
    def __hash__(self) -> int:
        """Make the X object hashable for use in sets and as dictionary keys."""
        return hash(id(self))
    
    def __eq__(self, other: object) -> bool:
        """Check if this X object equals another object."""
        if isinstance(other, XAnyValue):
            return id(self) == id(other) # type: ignore
        return False
    
    def __ne__(self, other: Any) -> bool:
        """
        Compare inequality with another value or X object.
        
        Args:
            other: Value or XAnyValue to compare with
            
        Returns:
            True if values are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other: Any) -> bool:
        """
        Compare if this value is less than another value or X object.
        
        Args:
            other: Value or XAnyValue to compare with
            
        Returns:
            True if this value is less than the other, False otherwise
        """
        if isinstance(other, XAnyValue):
            return self.value < other.value # type: ignore
        return self.value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Compare if this value is less than or equal to another value or X object.
        
        Args:
            other: Value or XAnyValue to compare with
            
        Returns:
            True if this value is less than or equal to the other, False otherwise
        """
        if isinstance(other, XAnyValue):
            return self.value <= other.value # type: ignore
        return self.value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Compare if this value is greater than another value or X object.
        
        Args:
            other: Value or XAnyValue to compare with
            
        Returns:
            True if this value is greater than the other, False otherwise
        """
        if isinstance(other, XAnyValue):
            return self.value > other.value # type: ignore
        return self.value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Compare if this value is greater than or equal to another value or X object.
        
        Args:
            other: Value or XAnyValue to compare with
            
        Returns:
            True if this value is greater than or equal to the other, False otherwise
        """
        if isinstance(other, XAnyValue):
            return self.value >= other.value # type: ignore
        return self.value >= other
    
    def __bool__(self) -> bool:
        """
        Convert the value to a boolean.
        
        Returns:
            Boolean representation of the current value
        """
        return bool(self.value)
    
    def __int__(self) -> int:
        """
        Convert the value to an integer.
        
        Returns:
            Integer representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to an integer
        """
        return int(self.value) # type: ignore
    
    def __float__(self) -> float:
        """
        Convert the value to a float.
        
        Returns:
            Float representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a float
        """
        return float(self.value) # type: ignore
    
    def __complex__(self) -> complex:
        """
        Convert the value to a complex number.
        
        Returns:
            Complex representation of the current value
            
        Raises:
            ValueError: If the value cannot be converted to a complex number
        """
        return complex(self.value) # type: ignore
    
    def __abs__(self) -> float:
        """
        Get the absolute value.
        
        Returns:
            Absolute value of the current value
            
        Raises:
            TypeError: If the value doesn't support absolute value operation
        """
        return abs(self.value) # type: ignore
    
    def __round__(self, ndigits: Optional[int] = None) -> float:
        """
        Round the value to the specified number of decimal places.
        
        Args:
            ndigits: Number of decimal places to round to (default: 0)
            
        Returns:
            Rounded value
            
        Raises:
            TypeError: If the value doesn't support rounding
        """
        return round(self.value, ndigits) # type: ignore
    
    def __floor__(self) -> int:
        """
        Get the floor value (greatest integer less than or equal to the value).
        
        Returns:
            Floor value
            
        Raises:
            TypeError: If the value doesn't support floor operation
        """
        import math
        return math.floor(self.value) # type: ignore
    
    def __ceil__(self) -> int:
        """
        Get the ceiling value (smallest integer greater than or equal to the value).
        
        Returns:
            Ceiling value
            
        Raises:
            TypeError: If the value doesn't support ceiling operation
        """
        import math
        return math.ceil(self.value) # type: ignore
    
    def __trunc__(self) -> int:
        """
        Get the truncated value (integer part of the value).
        
        Returns:
            Truncated value
            
        Raises:
            TypeError: If the value doesn't support truncation
        """
        import math
        return math.trunc(self.value) # type: ignore