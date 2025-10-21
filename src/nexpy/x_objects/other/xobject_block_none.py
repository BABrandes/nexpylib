from typing import Generic, TypeVar, Literal, Optional, Mapping, Callable, Never
from logging import Logger

from ...x_objects_base.x_composite_base import XCompositeBase
from ...core.hooks.hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.nexus_system.update_function_values import UpdateFunctionValues
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

T = TypeVar("T")

class XBlockNone(XCompositeBase[Literal["value_without_none", "value_with_none"], Never, T, Never, "XBlockNone[T]"], Generic[T]):
    """
    An X object that maintains two synchronized hooks and raises errors when None values are submitted.

    This X object is useful when you have code paths where types suggest Optional[T] but you know 
    the value will never actually be None in practice. It provides runtime enforcement while maintaining 
    type safety and minimizing linter errors.
    
    The X object manages two internal hooks that are always kept in sync:
    - `hook_with_None`: Typed as Optional[T], can be connected to external hooks that allow None
    - `hook_without_None`: Typed as T, guarantees non-None values
    
    Any attempt to submit None to either hook will be rejected.

    Parameters
    ----------
    hook_without_None_or_value : HookProtocol[T] | None | T
        Either:
        - A value of type T to initialize both hooks
        - A HookProtocol[T] to connect to the internal hook_without_None
        - None (if hook_with_None is provided)
        At least one of hook_without_None_or_value or hook_with_None must be provided.
        
    hook_with_None : HookProtocol[Optional[T]] | None
        Either:
        - A HookProtocol[Optional[T]] to connect to the internal hook_with_None
        - None (if hook_without_None_or_value is provided)
        At least one of hook_without_None_or_value or hook_with_None must be provided.
        
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracking value changes.
    
    Attributes
    ----------
    hook_with_None : HookWithOwnerProtocol[Optional[T]]
        The internal hook typed as Optional[T]. Despite the type allowing None,
        submitting None will raise a ValueError.
        
    hook_without_None : HookWithOwnerProtocol[T]
        The internal hook typed as T (non-optional). This hook is guaranteed
        to never contain None values.
    
    Raises
    ------
    ValueError
        - If None is submitted to either hook
        - If both hooks are initialized with different values
        - If neither hook_without_None_or_value nor hook_with_None is provided
        - If both hooks are submitted with different non-None values simultaneously
    
    Examples
    --------
    Basic usage with an initial value:
    
    >>> obs = XBlockNone[int](
    ...     hook_without_None_or_value=42,
    ...     hook_with_None=None
    ... )
    >>> obs.hook_without_None.value
    42
    >>> obs.hook_with_None.value
    42
    
    Updating values (both hooks stay synchronized):
    
    >>> obs.submit_values({"value_without_none": 100})
    (True, 'Values are submitted')
    >>> obs.hook_without_None.value
    100
    >>> obs.hook_with_None.value
    100
    
    Attempting to submit None raises an error:
    
    >>> obs.submit_values({"value_without_none": None})
    Traceback (most recent call last):
        ...
    ValueError: One of the values is None
    
    Connecting to external hooks:
    
    >>> external_hook = FloatingHook[int | None](50)
    >>> obs = XBlockNone[int](
    ...     hook_without_None_or_value=None,
    ...     hook_with_None=external_hook
    ... )
    >>> obs.hook_without_None.value  # Initialized from external_hook
    50
    >>> external_hook.submit_value(75)
    >>> obs.hook_with_None.value  # Synchronized
    75
    
    Use with listeners:
    
    >>> obs = XBlockNone[str](
    ...     hook_without_None_or_value="hello",
    ...     hook_with_None=None
    ... )
    >>> def on_change():
    ...     print(f"Value changed to: {obs.hook_without_None.value}")
    >>> obs.hook_without_None.add_listeners(on_change)
    >>> obs.submit_values({"value_without_none": "world"})
    Value changed to: world
    
    Notes
    -----
    - Both internal hooks are always kept synchronized
    - The X object uses the sync system to propagate changes between hooks
    - External hooks can be connected but should have matching initial values
    - The validation ensures both hooks always contain the same non-None value
    
    See Also
    --------
    XAnyValue/XValue : For simple single-value X objects
    XSync : For custom synchronization logic between multiple values
    """
    def __init__(
        self,
        hook_without_None_or_value: Hook[T] | ReadOnlyHook[T] | None | T,
        hook_with_None: Hook[Optional[T]] | ReadOnlyHook[Optional[T]] | None = None,
        *,
        custom_validator: Optional[Callable[[T], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
        ):

        # Collect the external hooks
        external_hook_without_none: Optional[ManagedHookProtocol[T]] = None
        external_hook_with_None: Optional[ManagedHookProtocol[Optional[T]]] = None
        
        if isinstance(hook_without_None_or_value, ManagedHookProtocol):
            external_hook_without_none = hook_without_None_or_value # type: ignore
        if isinstance(hook_with_None, ManagedHookProtocol):
            external_hook_with_None = hook_with_None

        # Collect the initial value and do some checks
        if hook_with_None is not None and hook_without_None_or_value is None:
            initial_value: T = hook_with_None.value # type: ignore
        
        elif hook_with_None is None and hook_without_None_or_value is not None:
            if isinstance(hook_without_None_or_value, ManagedHookProtocol):
                initial_value = hook_without_None_or_value.value # type: ignore
            else:
                # This is a value
                initial_value = hook_without_None_or_value
        
        elif hook_with_None is not None and hook_without_None_or_value is not None:
            if isinstance(hook_without_None_or_value, ManagedHookProtocol):
                if nexus_manager.is_not_equal(hook_with_None.value, hook_without_None_or_value.value): # type: ignore
                    raise ValueError("Values do not match of the two given hooks!")
                initial_value = hook_with_None.value # type: ignore
            else:
                # This is a value
                if nexus_manager.is_not_equal(hook_with_None.value, hook_without_None_or_value):
                    raise ValueError("Values do not match of the two given hooks!")
                initial_value = hook_with_None.value # type: ignore
        else:
            raise ValueError("Something non-none must be given!")

        # Define callbacks for XCompositeBase
        def _compute_missing_primary_values_callback(
            self_ref: "XBlockNone[T]", 
            update_values: UpdateFunctionValues[Literal["value_without_none", "value_with_none"], T]
        ) -> Mapping[Literal["value_without_none", "value_with_none"], T]:
            """
            Add the missing value.
            """
            submitted = update_values.submitted
            match "value_without_none" in submitted, "value_with_none" in submitted:
                case (True, True):
                    return {}
                case (True, False):
                    value_without_none = submitted["value_without_none"]
                    return {"value_with_none": value_without_none}
                case (False, True):
                    value_with_none = submitted["value_with_none"]
                    return {"value_without_none": value_with_none}
                case _:
                    return {}

        def _validate_complete_primary_values_callback(values: Mapping[Literal["value_without_none", "value_with_none"], T]) -> tuple[bool, str]:
            """
            Validate the complete values in isolation. return False when any value is None or the values do not match.
            """
            if not "value_without_none" in values or not "value_with_none" in values:
                raise ValueError("Invalid keys")

            value_without_none: T = values["value_without_none"]
            value_with_none: Optional[T] = values["value_with_none"]
            if value_without_none is None or value_with_none is None:
                return False, "One or both of the values is/are None"
            elif nexus_manager.is_not_equal(value_without_none, value_with_none):
                return False, "Values do not match"

            return True, "Values are valid"

        # Initialize parent with both hooks as primary hooks
        initial_hook_values = { # type: ignore
            "value_without_none": external_hook_without_none if external_hook_without_none is not None else initial_value,
            "value_with_none": external_hook_with_None if external_hook_with_None is not None else initial_value,
        }

        super().__init__(
            initial_hook_values=initial_hook_values,  # type: ignore[arg-type]
            compute_missing_primary_values_callback=_compute_missing_primary_values_callback,
            compute_secondary_values_callback=None,
            validate_complete_primary_values_callback=_validate_complete_primary_values_callback,
            invalidate_after_update_callback=custom_validator, # type: ignore
            custom_validator=None,
            logger=logger,
            nexus_manager=nexus_manager
        )

    #########################################################################
    # Public properties
    #########################################################################

    @property
    def hook_with_None(self) -> OwnedFullHookProtocol[Optional[T]]:
        """
        Get the hook with None.
        """
        return self._primary_hooks["value_with_none"]  # type: ignore[return-value]

    @property
    def hook_without_None(self) -> OwnedFullHookProtocol[T]:
        """
        Get the hook without None.
        """
        return self._primary_hooks["value_without_none"]