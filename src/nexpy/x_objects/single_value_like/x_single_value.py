from typing import Any, Generic, Optional, TypeVar, Self, Callable
from logging import Logger

from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from ...foundations.x_singleton_base import XSingletonBase
from ...foundations.carries_single_hook_protocol import CarriesSingleHookProtocol
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XSingleValueProtocol

T = TypeVar("T")

class XSingleValue(XSingletonBase[T], XSingleValueProtocol[T], CarriesSingleHookProtocol[T], Generic[T]):
    """
    Reactive value wrapper providing seamless integration with NexPy's synchronization system.
    
    XSingleValue is a high-level reactive value container that wraps
    a single value with automatic change notifications, validation, and fusion capabilities.
    It's the simplest X object and ideal for wrapping primitive values or single objects.
    
    Key Features
    ------------
    - **Reactive Updates**: Automatic notification on value changes
    - **Validation**: Optional custom validation for value updates
    - **Hook Fusion**: Join with other XValue instances or hooks for synchronization
    - **Thread-Safe**: All operations protected by locks
    - **Operator Overloading**: Supports comparison, arithmetic (if value type supports it)
    - **Type-Safe**: Full generic type support with type hints
    
    Parameters
    ----------
    value_or_hook : T | Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T]
        Initial value, or an existing hook/X object to join with.
        If a hook or X object is provided, this XValue will join its fusion domain.
    validator : Optional[Callable[[T], tuple[bool, str]]], optional
        Validation function called before accepting new values.
        Should return (True, "message") if valid, (False, "error") if invalid.
    logger : Optional[Logger], optional
        Logger instance for debugging operations
    nexus_manager : NexusManager, optional
        The NexusManager instance coordinating synchronization.
        Defaults to DEFAULT_NEXUS_MANAGER (global singleton).
    
    Attributes
    ----------
    value : T
        Current value (read/write property)
    hook : Hook[T]
        The underlying owned hook for fusion operations
    
    Examples
    --------
    Create a simple reactive value:
    
    >>> import nexpy as nx
    >>> temperature = nx.XValue(20.0)
    >>> print(temperature.value)
    20.0
    >>> temperature.value = 25.5
    >>> print(temperature.value)
    25.5
    
    With validation:
    
    >>> def validate_range(value):
    ...     if 0 <= value <= 100:
    ...         return True, "Valid"
    ...     return False, "Value must be between 0 and 100"
    >>> 
    >>> percentage = nx.XValue(50, validator=validate_range)
    >>> percentage.value = 75  # OK
    >>> percentage.value = 150  # Raises SubmissionError
    
    With listeners:
    
    >>> counter = nx.XValue(0)
    >>> counter.hook.add_listener(lambda: print(f"Counter: {counter.value}"))
    >>> counter.value = 1  # Prints: "Counter: 1"
    >>> counter.value = 2  # Prints: "Counter: 2"
    
    Joining XValues:
    
    >>> sensor_reading = nx.XValue(20.0)
    >>> display_value = nx.XValue(0.0)
    >>> 
    >>> # Synchronize them via hook fusion
    >>> sensor_reading.hook.join(display_value.hook)
    >>> 
    >>> sensor_reading.value = 25.5
    >>> print(display_value.value)  # 25.5 (automatically synchronized)
    
    Comparison operators:
    
    >>> x = nx.XValue(10)
    >>> y = nx.XValue(20)
    >>> print(x < y)  # True (compares .value)
    >>> print(x == y)  # False (compares object identity, not value)
    
    Arithmetic operations (if value type supports it):
    
    >>> x = nx.XValue(10)
    >>> print(int(x))     # 10
    >>> print(float(x))   # 10.0
    >>> print(abs(x))     # 10
    
    See Also
    --------
    FloatingHook : Independent hook for simple reactive values
    XDict : Reactive dictionary
    XList : Reactive list
    XDictSelect : Selection from a dictionary with internal synchronization
    
    Notes
    -----
    Thread Safety:
        All XValue operations are thread-safe. Multiple threads can safely read
        and write the value concurrently.
    
    Memory Management:
        XValue stores the value by reference only (no copying). The value itself
        is stored in the underlying Nexus, and multiple XValue instances can share
        the same Nexus through hook fusion.
    
    Validation:
        Validation is performed before value updates. If validation fails, the
        value remains unchanged and a SubmissionError is raised.
        
        When XValues are joined, validation from ALL joined XValues must pass
        for an update to succeed (atomic cross-object validation).
    
    Object Identity vs Value Equality:
        The `==` operator compares object identity (whether two XValue instances
        are the same object), not their values. To compare values, use:
        `x.value == y.value`
    """

    def __init__(
        self,
        value: T | HookProtocol[T] | XSingleValueProtocol[T],
        *,
        validate_value_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
        invalidate_after_update_callback: Optional[Callable[[], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:

        #########################################################
        # Get initial values and hooks
        #########################################################

        #-------------------------------- value --------------------------------

        if isinstance(value, XSingleValueProtocol):
            initial_value: T = value.value # type: ignore
            value_hook: Optional[HookProtocol[T]] = value.value_hook # type: ignore
        elif isinstance(value, HookProtocol):
            initial_value = value.value # type: ignore
            value_hook = value # type: ignore
        else:
            initial_value = value
            value_hook = None

        #########################################################
        # Prepare and initialize base class
        #########################################################

        #-------------------------------- Initialize base class --------------------------------

        super().__init__(
            value_or_hook=initial_value, # type: ignore
            validate_value_callback=validate_value_callback,
            invalidate_after_update_callback=invalidate_after_update_callback, # type: ignore
            logger=logger,
            nexus_manager=nexus_manager
        )

        #########################################################
        # Establish joining
        #########################################################

        self._join("value", value_hook, "use_target_value") if value_hook is not None else None
    #########################################################
    # Access
    #########################################################

    @property
    def value_hook(self) -> OwnedWritableHook[T, Self]:
        """
        Get the hook for the value (thread-safe).
        
        This hook can be used for joining operations with other x_objects.
        """
        return self._value_hook

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

    def change_value(self, value: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> tuple[bool, str]:
        """
        Change the value (lambda-friendly method).
        
        This method is equivalent to setting the .value property but can be used
        in lambda expressions and other contexts where property assignment isn't suitable.
        
        Args:
            value: The new value to set
            
        Raises:
            SubmissionError: If the new value fails validation
        """
        success, msg = self._submit_value("value", value)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "value")
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
        """Make XSingleValue hashable using UUID from XSingletonBase."""
        if hasattr(self, '_uuid'):
            return hash(self._uuid)
        else:
            # Fall back to id during initialization
            return hash(id(self))
    
    def __eq__(self, other: object) -> bool:
        """Check if this X object equals another object."""
        if isinstance(other, XSingleValue):
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
        if isinstance(other, XSingleValueProtocol):
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
        if isinstance(other, XSingleValueProtocol):
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
        if isinstance(other, XSingleValueProtocol):
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
        if isinstance(other, XSingleValueProtocol):
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