from typing import Literal, Optional, Sequence, TypeVar
from collections.abc import Set as AbstractSet
from logging import Logger

from ...foundations.x_adapter_base import XAdapterBase
from ...core.hooks.hook_protocols.owned_full_hook_protocol import OwnedFullHookProtocol
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore

T = TypeVar("T")


class XSetSequenceAdapter(XAdapterBase[AbstractSet[T], Sequence[T]]):
    """
    Adapter object that bridges between AbstractSet and Sequence, validating uniqueness.
    
    This X object maintains two synchronized hooks with different collection types:
    - `hook_set`: Typed as AbstractSet[T] (unordered, unique elements)
    - `hook_sequence`: Typed as Sequence[T] (ordered, allows duplicates)
    
    The adapter validates that sequence values contain only unique elements before
    allowing the adaptation. This enables connections between set and sequence hooks
    while ensuring consistency.
    
    Parameters
    ----------
    hook_set_or_value : Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | AbstractSet[T] | None
        Either:
        - A set/frozenset value to initialize both hooks
        - A Hook[AbstractSet[T]] to connect to the internal hook_set
        - None (if hook_sequence is provided)
        At least one parameter must be provided.
        
    hook_sequence : Hook[Sequence[T]] | ReadOnlyHook[Sequence[T]] | Sequence[T] | None
        Either:
        - A sequence value to initialize both hooks (must have unique elements)
        - A Hook[Sequence[T]] to connect to the internal hook_sequence
        - None (if hook_set_or_value is provided)
        At least one parameter must be provided.
        
    logger : Optional[Logger], default=None
        Optional logger for debugging and tracking value changes.
        
    nexus_manager : NexusManager, default=_DEFAULT_NEXUS_MANAGER
        Nexus manager for coordination.
    
    Attributes
    ----------
    hook_set : OwnedFullHookProtocol[AbstractSet[T]]
        The internal set hook. Stores the unique elements.
        
    hook_sequence : OwnedFullHookProtocol[Sequence[T]]
        The internal sequence hook. Only accepts sequences with unique elements.
    
    Raises
    ------
    ValueError
        - If a sequence contains duplicate elements
        - If both hooks are initialized with different values
        - If neither parameter is provided
        - If sequence elements are not hashable
    
    Examples
    --------
    Basic usage with a set value:
    
    >>> adapter = XSetSequenceAdapter[int](
    ...     hook_set_or_value={1, 2, 3},
    ...     hook_sequence=None
    ... )
    >>> adapter.hook_set.value
    {1, 2, 3}
    >>> sorted(adapter.hook_sequence.value)
    [1, 2, 3]
    
    Updating with a unique sequence:
    
    >>> adapter.submit_values({"right": [4, 5, 6]})
    (True, 'Values are submitted')
    >>> adapter.hook_set.value
    {4, 5, 6}
    
    Attempting to submit sequence with duplicates raises an error:
    
    >>> adapter.submit_values({"right": [1, 2, 2, 3]})
    Traceback (most recent call last):
        ...
    ValueError: Right validation failed: Sequence contains duplicate elements
    
    Connecting to external hooks:
    
    >>> set_hook = FloatingHook[AbstractSet[str]]({"a", "b"})
    >>> seq_hook = FloatingHook[Sequence[str]](["a", "b"])
    >>> adapter = XSetSequenceAdapter[str](
    ...     hook_set_or_value=set_hook,
    ...     hook_sequence=seq_hook
    ... )
    >>> set_hook.submit_value({"x", "y", "z"})
    >>> adapter.hook_sequence.value  # Synchronized (order may vary)
    ['x', 'y', 'z']
    
    Notes
    -----
    - Both internal hooks are always kept synchronized
    - Sequences must have unique elements (no duplicates)
    - Order from set to sequence is not guaranteed
    - The adapter handles automatic conversion between set and sequence types
    - Useful for connecting collection hooks with different type signatures
    
    See Also
    --------
    XOptionalAdapter : For T ↔ Optional[T] adapters
    XIntFloatAdapter : For int ↔ float adapters
    """
    
    def __init__(
        self,
        hook_set_or_value: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | AbstractSet[T] | None,
        hook_sequence: Hook[Sequence[T]] | ReadOnlyHook[Sequence[T]] | Sequence[T] | None = None,
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ):
        # Collect the external hooks
        external_hook_set: Optional[ManagedHookProtocol[AbstractSet[T]]] = None
        external_hook_sequence: Optional[ManagedHookProtocol[Sequence[T]]] = None
        
        if isinstance(hook_set_or_value, ManagedHookProtocol):
            external_hook_set = hook_set_or_value  # type: ignore
        if isinstance(hook_sequence, ManagedHookProtocol):
            external_hook_sequence = hook_sequence  # type: ignore
        
        # Determine initial value
        initial_set: AbstractSet[T]
        initial_sequence: Sequence[T]
        
        if hook_sequence is not None and hook_set_or_value is None:
            if isinstance(hook_sequence, ManagedHookProtocol):
                initial_sequence = hook_sequence.value
            else:
                initial_sequence = hook_sequence
            
            # Validate uniqueness
            if len(initial_sequence) != len(set(initial_sequence)):
                raise ValueError("Sequence contains duplicate elements")
            initial_set = frozenset(initial_sequence)
        
        elif hook_sequence is None and hook_set_or_value is not None:
            if isinstance(hook_set_or_value, ManagedHookProtocol):
                initial_set = hook_set_or_value.value
            else:
                initial_set = hook_set_or_value
            
            initial_sequence = tuple(initial_set)
        
        elif hook_sequence is not None and hook_set_or_value is not None:
            if isinstance(hook_set_or_value, ManagedHookProtocol):
                initial_set = hook_set_or_value.value
            else:
                initial_set = hook_set_or_value
            
            if isinstance(hook_sequence, ManagedHookProtocol):
                initial_sequence = hook_sequence.value
            else:
                initial_sequence = hook_sequence
            
            # Validate uniqueness
            if len(initial_sequence) != len(set(initial_sequence)):
                raise ValueError("Sequence contains duplicate elements")
            
            # Validate consistency
            if set(initial_sequence) != set(initial_set):
                raise ValueError(f"Values do not match: {initial_set} != {set(initial_sequence)}")
        else:
            raise ValueError("At least one parameter must be provided!")
        
        # Initialize parent with both hooks
        initial_hook_values = {
            "left": external_hook_set if external_hook_set is not None else initial_set,
            "right": external_hook_sequence if external_hook_sequence is not None else initial_sequence,
        }
        
        super().__init__(
            initial_hook_values=initial_hook_values,  # type: ignore
            logger=logger,
            nexus_manager=nexus_manager
        )
    
    #########################################################################
    # Adapter base implementation
    #########################################################################
    
    def _convert_left_to_right(self, left_value: AbstractSet[T]) -> Sequence[T]:
        """Convert set to sequence (order not guaranteed)."""
        return tuple(left_value)
    
    def _convert_right_to_left(self, right_value: Sequence[T]) -> AbstractSet[T]:
        """Convert sequence to set (must have unique elements)."""
        result_set = frozenset(right_value)
        if len(result_set) != len(right_value):
            raise ValueError(f"Cannot convert sequence with duplicates to set: {right_value}")
        return result_set
    
    def _validate_left(self, left_value: AbstractSet[T]) -> tuple[bool, str]:
        """Validate set value (any set is valid)."""
        if not isinstance(left_value, AbstractSet):
            return False, f"Left value must be AbstractSet, got {type(left_value)}"
        return True, "Set value is valid"
    
    def _validate_right(self, right_value: Sequence[T]) -> tuple[bool, str]:
        """Validate sequence value (must have unique elements)."""
        if not isinstance(right_value, Sequence) or isinstance(right_value, (str, bytes)):
            return False, f"Right value must be Sequence (not str/bytes), got {type(right_value)}"
        
        try:
            # Check for duplicates
            if len(right_value) != len(set(right_value)):
                return False, "Sequence contains duplicate elements"
        except TypeError as e:
            return False, f"Sequence elements must be hashable: {e}"
        
        return True, "Sequence value is valid"
    
    def _validate_consistency(self, left_value: AbstractSet[T], right_value: Sequence[T]) -> tuple[bool, str]:
        """Validate that set and sequence contain the same elements."""
        try:
            set_from_sequence = set(right_value)
            if set(left_value) != set_from_sequence:
                return False, f"Set and sequence elements do not match: {left_value} != {set_from_sequence}"
            return True, "Values are consistent"
        except Exception as e:
            return False, f"Consistency check error: {e}"
    
    #########################################################################
    # Public properties
    #########################################################################
    
    @property
    def hook_set(self) -> OwnedFullHookProtocol[AbstractSet[T]]:
        """Get the set hook (left side)."""
        return self._primary_hooks["left"]  # type: ignore
    
    @property
    def hook_sequence(self) -> OwnedFullHookProtocol[Sequence[T]]:
        """Get the sequence hook (right side)."""
        return self._primary_hooks["right"]  # type: ignore

