from typing import Any, Generic, Optional, TypeVar, Iterable, Literal, Iterator, Set
from logging import Logger

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...x_objects_base.x_complex_base import XComplexBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
from .protocols import XSetProtocol
from .utils import likely_settable


T = TypeVar("T")
   
class XSet(XComplexBase[Literal["value"], Literal["length"], Iterable[T], int, "XSet"], XSetProtocol[T], Set[T], Generic[T]):
    """
    Acting like a set.

    The hooks store an Iterable - allowing them to connect to any other iterable. But values requested from this object will be a set.
    """

    def __init__(
        self,
        observable_or_hook_or_value: Iterable[T] | Hook[Iterable[T]] | ReadOnlyHook[Iterable[T]] | XSetProtocol[T] | None = None,
        *,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER) -> None:

        if observable_or_hook_or_value is None:
            initial_value: Iterable[T] = set()
            hook: Optional[ManagedHookProtocol[Iterable[T]]] = None 
        elif isinstance(observable_or_hook_or_value, XSetProtocol):
            initial_value = observable_or_hook_or_value.set
            hook = observable_or_hook_or_value.set_hook
        elif isinstance(observable_or_hook_or_value, ManagedHookProtocol):
            initial_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value
        else:
            # Pass set directly - nexus system will convert to frozenset
            initial_value = observable_or_hook_or_value
            hook = None
        
        super().__init__(
            initial_hook_values={"value": initial_value},
            verification_method=lambda x: (True, "Verification method passed") if likely_settable(x["value"]) else (False, "Value cannot be used as a set!"),
            secondary_hook_callbacks={"length": lambda x: len(x["value"])}, # type: ignore
            output_value_wrapper={
                "value": lambda x: set(x) # type: ignore
            },
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
    def set_hook(self) -> Hook[Iterable[T]]:
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
    def set(self, value: Iterable[T]) -> None:
        self.change_set(value)
    
    def change_set(self, value: Iterable[T]) -> None:
        """
        Set the current value of the set.
        
        Args:
            value: Any iterable that can be converted to a set
        """
        success, msg = self._submit_values({"value": set(value)})
        if not success:
            raise SubmissionError(msg, value, "value")

    #-------------------------------- length --------------------------------

    @property
    def length(self) -> int:
        """
        Get the current length of the set.
        """
        return len(self._primary_hooks["value"].value) # type: ignore
    
    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the set length.
        
        This hook can be used for linking operations that react to length changes.
        """
        return self._secondary_hooks["length"] # type: ignore
    
    #########################################################
    # Standard set methods
    #########################################################
    
    # Standard set methods
    def add(self, item: T) -> None:
        """
        Add an element to the set.
        
        Creates a new set with the added element.
        
        Args:
            item: The element to add to the set
        """
        if item not in self._primary_hooks["value"].value:
            new_set = set(self._primary_hooks["value"].value) | {item}
            success, msg = self._submit_value("value", new_set)
            if not success:
                raise ValueError(msg)
    
    def remove(self, item: T) -> None:
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
        success, msg = self._submit_value("value", new_set)
        if not success:
            raise ValueError(msg)
    
    def discard(self, item: T) -> None:
        """
        Remove an element from the set if it is present.
        
        Creates a new set without the element (if present).
        Unlike remove(), this method does not raise an error if the item is not found.
        
        Args:
            item: The element to remove from the set
        """
        if item in self._primary_hooks["value"].value:
            new_set = set(self._primary_hooks["value"].value) - {item}
            success, msg = self._submit_value("value", new_set)
            if not success:
                raise ValueError(msg)
    
    def pop(self) -> T:
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
        if not success:
            raise ValueError(msg)
        return item 
    
    def clear(self) -> None:
        """
        Remove all elements from the set.
        
        Creates an empty set.
        """
        if self._primary_hooks["value"].value:
            new_set: set[T] = set()
            success, msg = self._submit_values({"value": new_set})
            if not success:
                raise ValueError(msg)
    
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
                raise ValueError(msg)
    
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
                raise ValueError(msg)
    
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
                raise ValueError(msg)
    
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
                raise ValueError(msg)
    
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
        return len(self._primary_hooks["value"].value) # type: ignore
    
    def __contains__(self, item: object) -> bool:
        """
        Check if an element is contained in the set.
        
        Args:
            item: The element to check for
            
        Returns:
            True if the element is in the set, False otherwise
        """
        return item in self._primary_hooks["value"].value # type: ignore
    
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