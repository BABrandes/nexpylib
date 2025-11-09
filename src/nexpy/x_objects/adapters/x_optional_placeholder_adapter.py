from typing import Generic, TypeVar, Optional, Self
from logging import Logger

from ...foundations.x_left_right_adapter_base import XLeftRightAdapterBase
from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...core.hooks.implementations.owned_writable_hook import OwnedWritableHook

T = TypeVar("T")


class XOptionalPlaceholderAdapter(XLeftRightAdapterBase[Optional[T], T], Generic[T]):
    """
    Adapter object that bridges between Optional[T] and a placeholder-based T.
    
    This X object maintains two synchronized hooks with different None-handling strategies:
    - `hook_optional`: Typed as Optional[T], uses None to represent "no value"
    - `hook_placeholder`: Typed as T, uses a placeholder value to represent "no value"
    
    This is particularly useful for GUI widgets that cannot handle None values but need
    to represent "no selection" or "empty" states using a placeholder value.
    
    Conversion Logic
    ----------------
    - When hook_optional is None → hook_placeholder becomes placeholder_value
    - When hook_placeholder is placeholder_value → hook_optional becomes None
    - Other values of type T pass through unchanged in both directions
    - Submitting placeholder_value to hook_optional is forbidden (ambiguous)
    
    Parameters
    ----------
    hook_optional : Hook[Optional[T]] | ReadOnlyHook[Optional[T]] | T | None
        Either:
        - A value of type Optional[T] to initialize the optional side
        - A Hook[Optional[T]] to connect to the internal hook_optional
        - None (if hook_placeholder is provided)
        At least one parameter must be provided.
        
    hook_placeholder : Hook[T] | ReadOnlyHook[T] | None
        Either:
        - A Hook[T] to connect to the internal hook_placeholder
        - None (if hook_optional is provided)
        At least one parameter must be provided.
        
    placeholder_value : T
        The placeholder value used on the placeholder side to represent None.
        This value cannot be submitted to hook_optional (would be ambiguous).
        
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracking value changes.
        
    nexus_manager : NexusManager, default=_DEFAULT_NEXUS_MANAGER
        Nexus manager for coordination.
    
    Attributes
    ----------
    hook_optional : OwnedFullHookProtocol[Optional[T]]
        The internal hook that uses None to represent "no value".
        
    hook_placeholder : OwnedFullHookProtocol[T]
        The internal hook that uses placeholder_value to represent "no value".
        Always contains a concrete value of type T.
    
    placeholder_value : T
        The placeholder value being used by this adapter.
    
    Raises
    ------
    ValueError
        - If placeholder_value is submitted to hook_optional (ambiguous)
        - If both hooks are initialized with incompatible values
        - If neither parameter is provided
    
    Examples
    --------
    Basic usage with an initial None value:
    
    >>> adapter = XOptionalPlaceholderAdapter[int](
    ...     hook_optional=None,
    ...     hook_placeholder=None,
    ...     placeholder_value=-1
    ... )
    >>> adapter.hook_optional.value
    None
    >>> adapter.hook_placeholder.value
    -1
    
    Setting a real value (passes through both sides):
    
    >>> adapter.submit_values({"left": 42})
    (True, 'Values are submitted')
    >>> adapter.hook_optional.value
    42
    >>> adapter.hook_placeholder.value
    42
    
    Setting None on the optional side:
    
    >>> adapter.submit_values({"left": None})
    (True, 'Values are submitted')
    >>> adapter.hook_optional.value
    None
    >>> adapter.hook_placeholder.value
    -1
    
    Setting placeholder on the placeholder side:
    
    >>> adapter.submit_values({"right": -1})
    (True, 'Values are submitted')
    >>> adapter.hook_optional.value
    None
    >>> adapter.hook_placeholder.value
    -1
    
    Attempting to submit placeholder to optional side raises an error:
    
    >>> adapter.submit_values({"left": -1})
    Traceback (most recent call last):
        ...
    ValueError: Left validation failed: Cannot submit placeholder value to optional side (ambiguous)
    
    GUI widget integration example:
    
    >>> # Widget that can't handle None, needs a placeholder like ""
    >>> adapter = XOptionalPlaceholderAdapter[str](
    ...     hook_optional=None,
    ...     hook_placeholder=None,
    ...     placeholder_value="<Select an option>"
    ... )
    >>> # Connect widget to hook_placeholder
    >>> widget_value = adapter.hook_placeholder  # Always has a string
    >>> # Connect logic to hook_optional
    >>> optional_selection = adapter.hook_optional  # Can be None
    
    Notes
    -----
    - Both internal hooks are always kept synchronized
    - The placeholder value must be distinguishable from valid values
    - Common placeholder choices: -1, "", "<empty>", etc.
    - Submitting the placeholder to hook_optional is forbidden to avoid ambiguity
    
    See Also
    --------
    XOptionalAdapter : For Optional[T] ↔ T where None is blocked
    XFloatIntAdapter : For float ↔ int adapters
    XSetSequenceAdapter : For set ↔ sequence adapters
    """
    
    def __init__(
        self,
        hook_optional: HookProtocol[Optional[T]] | None | T,
        hook_placeholder: HookProtocol[T] | None = None,
        *,
        placeholder_value: T,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ):
        # Store placeholder value
        self._placeholder_value = placeholder_value
        
        #################################################################################################
        # Collect external hooks
        #################################################################################################

        external_hook_optional: Optional[HookProtocol[Optional[T]]] = hook_optional if isinstance(hook_optional, HookProtocol) else None # type: ignore
        external_hook_placeholder: Optional[HookProtocol[T]] = hook_placeholder if isinstance(hook_placeholder, HookProtocol) else None
        
        #################################################################################################
        # Determine initial values
        #################################################################################################

        # Determine initial value for optional side
        if hook_optional is not None and hook_placeholder is None:
            if isinstance(hook_optional, HookProtocol):
                initial_value_optional: Optional[T] = hook_optional.value  # type: ignore
            else:
                # This is a value
                initial_value_optional = hook_optional
        
        elif hook_optional is None and hook_placeholder is not None:
            if isinstance(hook_placeholder, HookProtocol):
                # Convert from placeholder to optional
                if nexus_manager.is_equal(hook_placeholder.value, placeholder_value):
                    initial_value_optional = None
                else:
                    initial_value_optional = hook_placeholder.value
            else:
                raise ValueError("hook_placeholder must be a HookProtocol when hook_optional is None")
        
        elif hook_optional is not None and hook_placeholder is not None:
            # Both provided - validate they're compatible
            if isinstance(hook_optional, HookProtocol):
                optional_val = hook_optional.value
            else:
                optional_val = hook_optional
            
            if isinstance(hook_placeholder, HookProtocol):
                placeholder_val = hook_placeholder.value
            else:
                raise ValueError("hook_placeholder must be a HookProtocol")
            
            # Check compatibility
            if optional_val is None:
                if not nexus_manager.is_equal(placeholder_val, placeholder_value):
                    raise ValueError("When optional is None, placeholder must equal placeholder_value")
            else:
                if nexus_manager.is_not_equal(optional_val, placeholder_val):
                    raise ValueError("Values do not match between the two given hooks!")
            
            initial_value_optional = optional_val
        else:
            raise ValueError("At least one parameter must be provided!")
        
        # Validate that optional side doesn't have the placeholder value
        if initial_value_optional is not None and nexus_manager.is_equal(initial_value_optional, placeholder_value):
            raise ValueError("Cannot initialize optional side with placeholder value (ambiguous)")
        
        # Convert to placeholder side
        if initial_value_optional is None:
            initial_value_placeholder: T = placeholder_value
        else:
            initial_value_placeholder = initial_value_optional
        
        #################################################################################################
        # Initialize parent with both hooks
        #################################################################################################

        initial_hook_values = { # type: ignore
            "left": external_hook_optional if external_hook_optional is not None else initial_value_optional,
            "right": external_hook_placeholder if external_hook_placeholder is not None else initial_value_placeholder,
        }
        
        super().__init__(
            initial_hook_values=initial_hook_values, # type: ignore
            logger=logger,
            nexus_manager=nexus_manager
        )

        #################################################################################################
    
    #########################################################################
    # Adapter base implementation
    #########################################################################
    
    def _convert_left_to_right(self, left_value: Optional[T]) -> T:
        """Convert Optional[T] to T with placeholder."""
        if left_value is None:
            return self._placeholder_value
        return left_value
    
    def _convert_right_to_left(self, right_value: T) -> Optional[T]:
        """Convert T with placeholder to Optional[T]."""
        if self._nexus_manager.is_equal(right_value, self._placeholder_value):
            return None
        return right_value
    
    def _validate_left(self, left_value: Optional[T]) -> tuple[bool, str]:
        """Validate optional value (cannot be the placeholder itself)."""
        if left_value is not None and self._nexus_manager.is_equal(left_value, self._placeholder_value):
            return False, "Cannot submit placeholder value to optional side (ambiguous)"
        return True, "Value is valid"
    
    def _validate_right(self, right_value: T) -> tuple[bool, str]:
        """Validate placeholder value (always valid)."""
        return True, "Value is valid"
    
    #########################################################################
    # Public properties
    #########################################################################
    
    @property
    def hook_optional(self) -> OwnedWritableHook[Optional[T], Self]:
        """Get the Optional[T] hook (left side)."""
        return self._primary_hooks["left"]
    
    @property
    def hook_placeholder(self) -> OwnedWritableHook[T, Self]:
        """Get the T hook with placeholder (right side)."""
        return self._primary_hooks["right"]  # type: ignore
    
    @property
    def placeholder_value(self) -> T:
        """Get the placeholder value used by this adapter."""
        return self._placeholder_value
