from typing import Any, Generic, Optional, TypeVar, Literal, Iterator, Set, Callable, Mapping, Iterable, Self
from collections.abc import Set as AbstractSet
from logging import Logger

from ...core.hooks.protocols.hook_protocol import HookProtocol
from ...core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from ...core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XSetProtocol


T = TypeVar("T")
   
class XSet(XCompositeBase[Literal["value"], Literal["length"], AbstractSet[T], int], XSetProtocol[T], Set[T], Generic[T]):
    """
    Reactive set wrapper providing seamless integration with NexPy's synchronization system.

    XSet[T] is a reactive container for sets that behaves like a standard Python set
    but with automatic change notifications, validation, and synchronization capabilities.
    The generic type parameter T specifies the type of elements in the set.

    Type Parameters
    ---------------
    T : TypeVar
        The type of elements stored in the set. Must be hashable.
        Examples: XSet[int], XSet[str], XSet[MyHashableClass]

    Key Features
    ------------
    - **Reactive Updates**: Automatic notification when set contents change
    - **Set Operations**: Supports standard set operations (union, intersection, etc.)
    - **Hook Fusion**: Join with other XSet instances or hooks for synchronization
    - **Length Tracking**: Automatic secondary hook tracking set size
    - **Validation**: Optional custom validation for set updates
    - **Type-Safe**: Full generic type support

    See Also
    --------
    XList : For list-like reactive containers
    XDict : For dict-like reactive containers
    XValue : For single-value reactive containers
    """

    def __init__(
        self,
        value: AbstractSet[T] | HookProtocol[AbstractSet[T]] | XSetProtocol[T] | None = None,
        *,
        custom_validator: Optional[Callable[[Mapping[Literal["value", "length"], AbstractSet[T] | int]], tuple[bool, str]]] = None,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER) -> None:
        """
        Initialize a reactive set container.

        The generic type T specifies the element type (must be hashable). 
        Use square bracket notation: XSet[int], XSet[str], XSet[MyClass], etc.

        Parameters
        ----------
        value : AbstractSet[T] | Hook[AbstractSet[T]] | XSet[T] | None, optional
            Initial set contents or hook/XSet to connect to:
            - AbstractSet[T]: Any set, frozenset, or set-like object to copy
            - Hook[AbstractSet[T]]: External hook to join with
            - XSet[T]: Another XSet to join with
            - None: Create empty set (default)

        custom_validator : Callable[[Mapping[str, AbstractSet[T] | int]], tuple[bool, str]], optional
            Custom validation function for value updates.
            Receives {"value": AbstractSet[T], "length": int}.
            Returns (True, "message") if valid, (False, "error") if invalid.

        logger : Logger, optional
            Logger instance for debugging operations.

        nexus_manager : NexusManager, optional
            The NexusManager coordinating synchronization.
            Defaults to global DEFAULT_NEXUS_MANAGER.

        Examples
        --------
        Create an empty set:

        >>> tags = XSet[str]()
        >>> tags.set
        set()

        Initialize with values:

        >>> numbers = XSet[int]({1, 2, 3, 4})
        >>> numbers.set
        {1, 2, 3, 4}

        Connect two sets:

        >>> source = XSet[str]({"red", "green", "blue"})
        >>> mirror = XSet[str](source)  # Joins with source
        >>> source.add("yellow")
        >>> mirror.set  # Automatically synchronized
        {'red', 'green', 'blue', 'yellow'}

        With validation (enforce non-empty):

        >>> def validate_not_empty(values):
        ...     if len(values["value"]) > 0:
        ...         return True, "Valid"
        ...     return False, "Set must not be empty"
        >>> required_tags = XSet[str]({"initial"}, custom_validator=validate_not_empty)

        Type-specific sets:

        >>> class ID:
        ...     def __init__(self, value: int):
        ...         self.value = value
        ...     def __hash__(self):
        ...         return hash(self.value)
        >>> ids = XSet[ID]({ID(1), ID(2), ID(3)})
        """

        if value is None:
            initial_value: AbstractSet[T] = set()
            hook: Optional[HookProtocol[AbstractSet[T]]] = None 
        elif isinstance(value, XSetProtocol):
            initial_value = value.set
            hook = value.set_hook
        elif isinstance(value, HookProtocol):
            initial_value = value.value
            hook = value
        else:
            # Pass set directly - nexus system will convert to frozenset
            initial_value = value
            hook = None
        
        super().__init__(
            initial_hook_values={"value": initial_value},
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={"length": lambda x: len(x["value"])},
            validate_complete_primary_values_callback=lambda x: (True, "Verification method passed") if isinstance(x["value"], AbstractSet) else (False, "Value cannot be used as a set!"),
            output_value_wrapper={"value": lambda x: set(x)}, # type: ignore
            custom_validator=custom_validator,
            logger=logger,
            nexus_manager=nexus_manager
        )

        if hook is not None:
            self._join("value", hook, "use_target_value") # type: ignore

    #########################################################
    # XSetProtocol implementation
    #########################################################

    #-------------------------------- set value --------------------------------

    @property
    def set_hook(self) -> OwnedWritableHook[AbstractSet[T], Self]:
        """
        Get the hook for the set.

        This hook can be used for linking operations with other observables.
        Returns frozenset for immutability.
        """
        return self._primary_hooks["value"]

    @property
    def set(self) -> set[T]:
        """
        Get the current set value.
        
        Returns:
            A copy of the current set value.
            
        Note:
            Returns a copy of the set to prevent external mutation.
        """
        return self._value_wrapped("value") # type: ignore
    
    @set.setter
    def set(self, value: AbstractSet[T]) -> None:
        self.change_set(value)
    
    def change_set(self, value: AbstractSet[T], *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Set the current value of the set.
        
        Args:
            value: Any iterable that can be converted to a set
        """
        success, msg = self._submit_values({"value": set(value)}, logger=logger)
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, value, "value")

    #-------------------------------- length --------------------------------

    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        return len(self._primary_hooks["value"].value)
    
    @property
    def length_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the set length.
        
        This hook can be used for linking operations that react to length changes.
        """
        return self._secondary_hooks["length"]
    
    #########################################################
    # Standard set methods
    #########################################################
    
    # Standard set methods
    def add(self, item: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Add an element to the set.
        
        Creates a new set with the added element.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._primary_hooks["value"].value:
            new_set = set(self._primary_hooks["value"].value) | {item}
            success, msg = self._submit_value("value", new_set, logger=logger)
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, item, "value")
    
    def remove(self, item: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Remove an element from the set.
        
        Creates a new set without the element.
        
        Args:
            item: The element to remove from the set
            
        Raises:
            KeyError: If the item is not in the set
        """
        if item not in self._primary_hooks["value"].value:
            raise KeyError(item)
        
        new_set = set(self._primary_hooks["value"].value) - {item}
        success, msg = self._submit_value("value", new_set, logger=logger)
        if not success:
            raise SubmissionError(msg, item, "value")
    
    def discard(self, item: T, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Remove an element from the set if it is present.
        
        Creates a new set without the element (if present).
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._primary_hooks["value"].value:
            new_set = set(self._primary_hooks["value"].value) - {item}
            success, msg = self._submit_value("value", new_set, logger=logger)
            if not success and raise_submission_error_flag:
                raise ValueError(msg)
    
    def pop(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> T:
        """
        Remove and return an arbitrary element from the set.
        
        Creates a new set without the popped element.
        
        Returns:
            The removed element
            
        Raises:
            KeyError: If the set is empty
        """
        if not self._primary_hooks["value"].value:
            raise KeyError("pop from an empty set")
        
        item: T = next(iter(self._primary_hooks["value"].value))
        new_set = set(self._primary_hooks["value"].value) - {item}
        success, msg = self._submit_value("value", set(new_set))
        if not success and raise_submission_error_flag:
            raise SubmissionError(msg, item, "value")
        return item 
    
    def clear(self, *, logger: Optional[Logger] = None, raise_submission_error_flag: bool = True) -> None:
        """
        Remove all elements from the set.
        
        Creates an empty set.
        """
        if self._primary_hooks["value"].value:
            new_set: set[T] = set()
            success, msg = self._submit_values({"value": new_set})
            if not success and raise_submission_error_flag:
                raise SubmissionError(msg, "value")
    
    def update(self, *others: Iterable[T]) -> None:
        """
        Update the set with elements from all other iterables.
        
        Creates a new set with all elements from current set and provided iterables.
        
        Args:
            *others: Variable number of iterables to add elements from
        """
        new_set: set[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set | set(other)
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise SubmissionError(msg, "value")
    
    def intersection_update(self, *others: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in this set and all others.
        
        Creates a new set with only common elements.
        
        Args:
            *others: Variable number of iterables to intersect with
        """
        new_set: set[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set & set(other)
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise SubmissionError(msg, "value")
    
    def difference_update(self, *others: Iterable[T]) -> None:
        """
        Update the set removing elements found in any of the others.
        
        Creates a new set without elements from the provided iterables.
        
        Args:
            *others: Variable number of iterables to remove elements from
        """
        new_set: set[T] = self._primary_hooks["value"].value # type: ignore
        for other in others:
            new_set = new_set - set(other)
        if new_set != self._primary_hooks["value"].value:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise SubmissionError(msg, "value")
    
    def symmetric_difference_update(self, other: Iterable[T]) -> None:
        """
        Update the set keeping only elements found in either set but not both.
        
        Creates a new set with symmetric difference.
        
        Args:
            other: An iterable to compute symmetric difference with
        """
        current_set: set[T] = self._primary_hooks["value"].value # type: ignore
        new_set = current_set ^ set(other)
        
        # Only update if there's an actual change
        if new_set != current_set:
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise SubmissionError(msg, "value")
    
    def __str__(self) -> str:
        return f"XSet(options={self._primary_hooks['value'].value!r})"
    
    def __repr__(self) -> str:
        return f"XSet({self._primary_hooks['value'].value!r})"
    
    def __len__(self) -> int:
        """
        Get the number of elements in the set.
        
        Returns:
            The number of elements in the set
        """
        return len(self._primary_hooks["value"].value)
    
    def __contains__(self, item: object) -> bool:
        """
        Check if an element is contained in the set.
        
        Args:
            item: The element to check for
            
        Returns:
            True if the element is in the set, False otherwise
        """
        return item in self._primary_hooks["value"].value
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the set elements.
        
        Returns:
            An iterator that yields each element in the set
        """
        return iter(self._primary_hooks["value"].value)
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another set or observable set.
        
        Args:
            other: Another set or XSet to compare with
            
        Returns:
            True if the sets contain the same elements, False otherwise
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value == other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value == other
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another set or observable set.
        
        Args:
            other: Another set or XSet to compare with
            
        Returns:
            True if the sets are not equal, False otherwise
        """
        return not (self == other)
    
    def __le__(self, other: Any) -> bool:
        """
        Check if this set is a subset of another set or observable set.
        
        Args:
            other: Another set or XSet to check against
            
        Returns:
            True if this set is a subset of the other, False otherwise
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value <= other
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this set is a proper subset of another set or observable set.
        
        Args:
            other: Another set or XSet to check against
            
        Returns:
            True if this set is a proper subset of the other, False otherwise
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value < other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this set is a superset of another set or observable set.
        
        Args:
            other: Another set or XSet to check against
            
        Returns:
            True if this set is a superset of the other, False otherwise
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value >= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this set is a proper superset of another set or observable set.
        
        Args:
            other: Another set or XSet to check against
            
        Returns:
            True if this set is a proper superset of the other, False otherwise
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value > other
    
    def __and__(self, other: Any) -> Set[T]:
        """
        Compute the intersection with another set or observable set.
        
        Args:
            other: Another iterable or XSet to intersect with
            
        Returns:
            A new set containing elements common to both sets
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value & other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value & set(other) # type: ignore
    
    def __or__(self, other: Any) -> Set[T]:
        """
        Compute the union with another set or observable set.
        
        Args:
            other: Another iterable or XSet to union with
            
        Returns:
            A new set containing all elements from both sets
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value | other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value | set(other) # type: ignore
    
    def __sub__(self, other: Any) -> Set[T]:
        """
        Compute the difference with another set or observable set.
        
        Args:
            other: Another iterable or XSet to subtract from this set
            
        Returns:
            A new set containing elements in this set but not in the other
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value - other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value - set(other) # type: ignore
    
    def __xor__(self, other: Any) -> Set[T]:
        """
        Compute the symmetric difference with another set or observable set.
        
        Args:
            other: Another iterable or XSet to compute symmetric difference with
            
        Returns:
            A new set containing elements in either set but not in both
        """
        if isinstance(other, XSet):
            return self._primary_hooks["value"].value ^ other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value ^ set(other) # type: ignore
    
    # Override __hash__ to use UUID instead of Set's __hash__ = None
    def __hash__(self) -> int: # type: ignore
        """Make XSet hashable using UUID from XBase."""
        return super().__hash__()