from typing import Generic, TypeVar, Optional, Self
from logging import Logger

from ...foundations.x_left_right_adapter_base import XLeftRightAdapterBase
from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...core.hooks.implementations.owned_writable_hook import OwnedWritableHook

T = TypeVar("T")

class XOptionalAdapter(XLeftRightAdapterBase[T, Optional[T]], Generic[T]):
    """
    Adapter object that bridges between T and Optional[T], blocking None values.
    
    This X object maintains two synchronized hooks with different type signatures:
    - `hook_t`: Typed as T (non-optional)
    - `hook_optional`: Typed as Optional[T] (allows None in type signature)
    
    Despite the optional type signature, submitting None to either hook will be rejected.
    This is useful when you have code paths where types suggest Optional[T] but you know
    the value will never actually be None in practice.
    
    Parameters
    ----------
    hook_t_or_value : Hook[T] | ReadOnlyHook[T] | T | None
        Either:
        - A value of type T to initialize both hooks
        - A Hook[T] to connect to the internal hook_t
        - None (if hook_optional is provided)
        At least one parameter must be provided.
        
    hook_optional : Hook[Optional[T]] | ReadOnlyHook[Optional[T]] | None
        Either:
        - A Hook[Optional[T]] to connect to the internal hook_optional
        - None (if hook_t_or_value is provided)
        At least one parameter must be provided.
        
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracking value changes.
        
    nexus_manager : NexusManager, default=_DEFAULT_NEXUS_MANAGER
        Nexus manager for coordination.
    
    Attributes
    ----------
    hook_t : OwnedFullHookProtocol[T]
        The internal hook typed as T (non-optional). This hook is guaranteed
        to never contain None values.
        
    hook_optional : OwnedFullHookProtocol[Optional[T]]
        The internal hook typed as Optional[T]. Despite the type allowing None,
        submitting None will raise a ValueError.
    
    Raises
    ------
    ValueError
        - If None is submitted to either hook
        - If both hooks are initialized with different values
        - If neither parameter is provided
        - If both hooks are submitted with different non-None values simultaneously
    
    Examples
    --------
    Basic usage with an initial value:
    
    >>> adapter = XOptionalAdapter[int](
    ...     hook_t_or_value=42,
    ...     hook_optional=None
    ... )
    >>> adapter.hook_t.value
    42
    >>> adapter.hook_optional.value
    42
    
    Updating values (both hooks stay synchronized):
    
    >>> adapter.submit_values({"left": 100})
    (True, 'Values are submitted')
    >>> adapter.hook_t.value
    100
    >>> adapter.hook_optional.value
    100
    
    Attempting to submit None raises an error:
    
    >>> adapter.submit_values({"left": None})
    Traceback (most recent call last):
        ...
    ValueError: Left validation failed: Value cannot be None
    
    Connecting to external hooks:
    
    >>> external_hook = FloatingHook[int | None](50)
    >>> adapter = XOptionalAdapter[int](
    ...     hook_t_or_value=None,
    ...     hook_optional=external_hook
    ... )
    >>> adapter.hook_t.value  # Initialized from external_hook
    50
    >>> external_hook.submit_value(75)
    >>> adapter.hook_optional.value  # Synchronized
    75
    
    Notes
    -----
    - Both internal hooks are always kept synchronized
    - The adapter object uses the sync system to propagate changes between hooks
    - External hooks can be connected but should have matching initial values
    - The validation ensures both hooks always contain the same non-None value
    
    See Also
    --------
    XValue : For simple single-value X objects
    XFloatIntAdapter : For float ↔ int adapters
    XSetSequenceAdapter : For set ↔ sequence adapters
    """
    
    def __init__(
        self,
        hook_t_or_value: HookProtocol[T] | None | T,
        hook_optional: HookProtocol[Optional[T]] | None = None,
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ):
        #################################################################################################
        # Collect external hooks
        #################################################################################################

        external_hook_t: Optional[HookProtocol[T]] = hook_t_or_value if isinstance(hook_t_or_value, HookProtocol) else None # type: ignore
        external_hook_optional: Optional[HookProtocol[Optional[T]]] = hook_optional if isinstance(hook_optional, HookProtocol) else None
        
        #################################################################################################
        # Determine initial values
        #################################################################################################

        # Determine initial value
        if hook_optional is not None and hook_t_or_value is None:
            if hook_optional.value is None:
                raise ValueError("Cannot initialize with None value")
            initial_value: T = hook_optional.value
        
        elif hook_optional is None and hook_t_or_value is not None:
            if isinstance(hook_t_or_value, HookProtocol):
                if hook_t_or_value.value is None: # type: ignore
                    raise ValueError("Cannot initialize with None value")
                initial_value = hook_t_or_value.value  # type: ignore
            else:
                # This is a value
                if hook_t_or_value is None:
                    raise ValueError("Cannot initialize with None value")
                initial_value = hook_t_or_value
        
        elif hook_optional is not None and hook_t_or_value is not None:
            if isinstance(hook_t_or_value, HookProtocol):
                if nexus_manager.is_not_equal(hook_optional.value, hook_t_or_value.value): # type: ignore
                    raise ValueError("Values do not match of the two given hooks!")
                if hook_optional.value is None:
                    raise ValueError("Cannot initialize with None value")
                initial_value = hook_optional.value
            else:
                # This is a value
                if nexus_manager.is_not_equal(hook_optional.value, hook_t_or_value):
                    raise ValueError("Values do not match of the two given hooks!")
                if hook_t_or_value is None:
                    raise ValueError("Cannot initialize with None value")
                initial_value = hook_t_or_value

        else:
            raise ValueError("At least one parameter must be provided!")
        
        #################################################################################################
        # Initialize parent with both hooks
        #################################################################################################

        initial_hook_values = { # type: ignore
            "left": external_hook_t if external_hook_t is not None else initial_value,
            "right": external_hook_optional if external_hook_optional is not None else initial_value,
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
    
    def _convert_left_to_right(self, left_value: T) -> Optional[T]:
        """Convert non-optional to optional (trivial conversion)."""
        return left_value
    
    def _convert_right_to_left(self, right_value: Optional[T]) -> T:
        """Convert optional to non-optional (must not be None)."""
        if right_value is None:
            raise ValueError("Cannot convert None to non-optional type")
        return right_value
    
    def _validate_left(self, left_value: T) -> tuple[bool, str]:
        """Validate non-optional value (cannot be None)."""
        if left_value is None:
            return False, "Value cannot be None"
        return True, "Value is valid"
    
    def _validate_right(self, right_value: Optional[T]) -> tuple[bool, str]:
        """Validate optional value (cannot be None despite type)."""
        if right_value is None:
            return False, "Value cannot be None"
        return True, "Value is valid"
    
    #########################################################################
    # Public properties
    #########################################################################
    
    @property
    def hook_t(self) -> OwnedWritableHook[T, Self]:
        """Get the T hook (left side)."""
        return self._primary_hooks["left"]  # type: ignore
    
    @property
    def hook_optional(self) -> OwnedWritableHook[Optional[T], Self]:
        """Get the Optional[T] hook (right side)."""
        return self._primary_hooks["right"]
    
    # Aliases for backward compatibility
    @property
    def hook_non_optional(self) -> OwnedWritableHook[T, Self]:
        """Alias for hook_t (backward compatibility)."""
        return self.hook_t
    
    @property
    def hook_without_None(self) -> OwnedWritableHook[T, Self]:
        """Alias for hook_t (backward compatibility)."""
        return self.hook_t
    
    @property
    def hook_with_None(self) -> OwnedWritableHook[Optional[T], Self]:
        """Alias for hook_optional (backward compatibility)."""
        return self.hook_optional

