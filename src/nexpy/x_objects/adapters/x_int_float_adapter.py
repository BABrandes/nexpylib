from typing import Optional, Self
from logging import Logger

from ...foundations.x_left_right_adapter_base import XLeftRightAdapterBase
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...core.hooks.implementations.owned_writable_hook import OwnedWritableHook

class XIntFloatAdapter(XLeftRightAdapterBase[int, float]):
    """
    Adapter object that bridges between int and float, validating integer values.
    
    This X object maintains two synchronized hooks with different numeric types:
    - `hook_int`: Typed as int
    - `hook_float`: Typed as float
    
    The adapter validates that float values have no fractional part (is_integer() == True)
    before allowing the adaptation. This enables connections between int and float hooks
    while ensuring type safety.
    
    Parameters
    ----------
    hook_int_or_value : Hook[int] | ReadOnlyHook[int] | int | None
        Either:
        - An int value to initialize both hooks
        - A Hook[int] to connect to the internal hook_int
        - None (if hook_float is provided)
        At least one parameter must be provided.
        
    hook_float : Hook[float] | ReadOnlyHook[float] | float | None
        Either:
        - A float value to initialize both hooks (must be integer-valued)
        - A Hook[float] to connect to the internal hook_float
        - None (if hook_int_or_value is provided)
        At least one parameter must be provided.
        
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracking value changes.
        
    nexus_manager : NexusManager, default=_DEFAULT_NEXUS_MANAGER
        Nexus manager for coordination.
    
    Attributes
    ----------
    hook_int : OwnedFullHookProtocol[int]
        The internal int hook. Accepts any integer value.
        
    hook_float : OwnedFullHookProtocol[float]
        The internal float hook. Only accepts float values that are integers.
    
    Raises
    ------
    ValueError
        - If a float value has a fractional part (not is_integer())
        - If both hooks are initialized with different values
        - If neither parameter is provided
    
    Examples
    --------
    Basic usage with an integer value:
    
    >>> adapter = XIntFloatAdapter(
    ...     hook_int_or_value=42,
    ...     hook_float=None
    ... )
    >>> adapter.hook_int.value
    42
    >>> adapter.hook_float.value
    42.0
    
    Updating with integer-valued float:
    
    >>> adapter.submit_values({"left": 100})
    (True, 'Values are submitted')
    >>> adapter.hook_float.value
    100.0
    
    Attempting to submit non-integer float raises an error:
    
    >>> adapter.submit_values({"left": 42.5})
    Traceback (most recent call last):
        ...
    ValueError: Left validation failed: Float value must be integer-valued (is_integer() must be True)
    
    Connecting to external hooks:
    
    >>> int_hook = FloatingHook[int](50)
    >>> float_hook = FloatingHook[float](50.0)
    >>> adapter = XIntFloatAdapter(
    ...     hook_int_or_value=int_hook,
    ...     hook_float=float_hook
    ... )
    >>> int_hook.submit_value(75)
    >>> adapter.hook_float.value  # Synchronized
    75.0
    
    Notes
    -----
    - Both internal hooks are always kept synchronized
    - Float values must satisfy is_integer() == True
    - The adapter handles automatic conversion between float and int
    - Useful for connecting numeric hooks with different type signatures
    
    See Also
    --------
    XOptionalAdapter : For T ↔ Optional[T] adapters
    XSequenceSetAdapter : For sequence ↔ set adapters
    """
    
    def __init__(
        self,
        hook_int_or_value: HookProtocol[int] | int | None,
        hook_float: HookProtocol[float] | float | None = None,
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ):

        #################################################################################################
        # Collect external hooks
        #################################################################################################

        external_hook_int: Optional[HookProtocol[int]] = hook_int_or_value if isinstance(hook_int_or_value, HookProtocol) else None
        external_hook_float: Optional[HookProtocol[float]] = hook_float if isinstance(hook_float, HookProtocol) else None
        
        #################################################################################################
        # Determine initial values
        #################################################################################################

        initial_int: int
        initial_float: float
        
        if hook_float is not None and hook_int_or_value is None:
            if isinstance(hook_float, HookProtocol):
                initial_float = hook_float.value
            else:
                initial_float = hook_float
            
            if not initial_float.is_integer():
                raise ValueError(f"Float value {initial_float} must be integer-valued")
            initial_int = int(initial_float)
        
        elif hook_float is None and hook_int_or_value is not None:
            if isinstance(hook_int_or_value, HookProtocol):
                initial_int = hook_int_or_value.value
            else:
                initial_int = hook_int_or_value
            initial_float = float(initial_int)
        
        elif hook_float is not None and hook_int_or_value is not None:
            if isinstance(hook_int_or_value, HookProtocol):
                initial_int = hook_int_or_value.value
            else:
                initial_int = hook_int_or_value
            
            if isinstance(hook_float, HookProtocol):
                initial_float = hook_float.value
            else:
                initial_float = hook_float
            
            if not initial_float.is_integer():
                raise ValueError(f"Float value {initial_float} must be integer-valued")
            
            if int(initial_float) != initial_int:
                raise ValueError(f"Values do not match: {initial_float} != {initial_int}")

        else:
            raise ValueError("At least one parameter must be provided!")
        
        #################################################################################################
        # Initialize parent with both hooks
        #################################################################################################

        initial_hook_values = {
            "left": external_hook_int if external_hook_int is not None else initial_int,
            "right": external_hook_float if external_hook_float is not None else initial_float,
        }
        
        super().__init__(
            initial_hook_values=initial_hook_values,  # type: ignore
            logger=logger,
            nexus_manager=nexus_manager
        )

        #################################################################################################
    
    #########################################################################
    # Adapter base implementation
    #########################################################################
    
    def _convert_left_to_right(self, left_value: int) -> float:
        """Convert int to float (trivial conversion)."""
        return float(left_value)
    
    def _convert_right_to_left(self, right_value: float) -> int:
        """Convert float to int (must be integer-valued)."""
        if not right_value.is_integer():
            raise ValueError(f"Cannot convert non-integer float {right_value} to int")
        return int(right_value)
    
    def _validate_left(self, left_value: int) -> tuple[bool, str]:
        """Validate int value (any int is valid)."""
        if not isinstance(left_value, int) or isinstance(left_value, bool): # type: ignore
            return False, f"Left value must be int, got {type(left_value)}"
        return True, "Int value is valid"
    
    def _validate_right(self, right_value: float) -> tuple[bool, str]:
        """Validate float value (must be integer-valued)."""
        if not isinstance(right_value, (float, int)): # type: ignore
            return False, f"Right value must be float, got {type(right_value)}"
        
        float_val = float(right_value)
        if not float_val.is_integer():
            return False, f"Float value must be integer-valued (is_integer() must be True), got {float_val}"
        return True, "Float value is valid"
    
    #########################################################################
    # Public properties
    #########################################################################
    
    @property
    def hook_int(self) -> OwnedWritableHook[int, Self]:
        """Get the int hook (left side)."""
        return self._primary_hooks["left"]  # type: ignore
    
    @property
    def hook_float(self) -> OwnedWritableHook[float, Self]:
        """Get the float hook (right side)."""
        return self._primary_hooks["right"]

