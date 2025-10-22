from typing import Generic, TypeVar, Callable, Literal, Optional, Any, Mapping
from collections.abc import Iterator, Sequence
from logging import Logger

from ...core.hooks.hook_aliases import Hook, ReadOnlyHook
from ...core.hooks.hook_protocols.managed_hook_protocol import ManagedHookProtocol
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XListProtocol

T = TypeVar("T")
  

class XList(XCompositeBase[Literal["value"], Literal["length"], Sequence[T], int, "XList"], XListProtocol[T], Generic[T]):
    """
    Acting like a list.

    The hooks store an Iterable - allowing them to connect to any other iterable. But values requested from this object will be a list.
    """
    def __init__(
        self,
        observable_or_hook_or_value: Sequence[T] | Hook[Sequence[T]] | ReadOnlyHook[Sequence[T]] | XListProtocol[T] | None = None,
        *,
        logger: Optional[Logger] = None,
        custom_validator: Optional[Callable[[Mapping[Literal["value", "length"], Any]], tuple[bool, str]]] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
        ) -> None:


        if observable_or_hook_or_value is None:
            initial_value: Sequence[T] = ()
            hook: Optional[ManagedHookProtocol[Sequence[T]]] = None

        elif isinstance(observable_or_hook_or_value, XListProtocol):
            initial_value = observable_or_hook_or_value.list
            hook = observable_or_hook_or_value.list_hook

        elif isinstance(observable_or_hook_or_value, ManagedHookProtocol):
            initial_value = observable_or_hook_or_value.value
            hook = observable_or_hook_or_value

        elif isinstance(observable_or_hook_or_value, Sequence): # type: ignore
            # It's a sequence
            initial_value = observable_or_hook_or_value
            hook = None
        else:
            raise ValueError("Invalid initial value")

        super().__init__(
            initial_hook_values={"value": initial_value},
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={"length": lambda x: len(x["value"])},
            validate_complete_primary_values_callback=lambda x: (True, "Verification method passed") if isinstance(x["value"], Sequence) else (False, "Value has not been converted to a list!"), # type: ignore
            output_value_wrapper={
                "value": lambda x: list(x) # type: ignore
            },
            custom_validator=custom_validator,
            logger=logger,
            nexus_manager=nexus_manager
        )

        if hook is not None:
            self._join("value", hook, "use_target_value") # type: ignore

    #########################################################
    # XListProtocol implementation
    #########################################################

    #-------------------------------- list value --------------------------------   

    @property
    def list_hook(self) -> Hook[Sequence[T]]:
        """
        Get the hook for the list (contains Sequence).
        """
        return self._primary_hooks["value"]

    @property
    def list(self) -> list[T]:
        """
        Get the list value as mutable list (copied from the hook).
        """
        value = self._primary_hooks["value"].value
        return list(value)

    @list.setter
    def list(self, value: Sequence[T]) -> None:
        self.change_list(value)

    def change_list(self, value: Sequence[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        """
        success, msg = self._submit_value("value", list(value))
        if not success:
            raise SubmissionError(msg, value, "value")
    
    def change_value(self, new_value: Sequence[T]) -> None:
        """
        Change the list value (lambda-friendly method).
        
        Deprecated: Use change_list instead for consistency with XDict.
        """
        self.change_list(new_value)

    #-------------------------------- length --------------------------------

    @property
    def length_hook(self) -> ReadOnlyHook[int]:
        """
        Get the hook for the list length.
        """
        return self._secondary_hooks["length"] # type: ignore

    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        return len(self._primary_hooks["value"].value)

    #########################################################
    # Standard list methods
    #########################################################
    
    # Standard list methods
    def append(self, item: T) -> None:
        """
        Add an item to the end of the list.
        
        Creates a new tuple with the appended item.
        
        Args:
            item: The item to add to the list
        """
        current_value = self._primary_hooks["value"].value
        new_list: list[T] = list(current_value) + [item]
        self.change_list(new_list)
    
    def extend(self, iterable: Sequence[T]) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Creates a new tuple with the extended elements.
        
        Args:
            iterable: The iterable containing elements to add
        """
        current_value = self._primary_hooks["value"].value
        new_list = list(current_value) + list(iterable)
        self.change_list(new_list)
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Creates a new tuple with the item inserted.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        current = self._primary_hooks["value"].value
        new_list = list(current)
        new_list.insert(index, item)
        self.change_list(new_list)
    
    def remove(self, item: T) -> None:
        """
        Remove the first occurrence of a value from the list.
        
        Creates a new tuple without the first occurrence of the item.
        
        Args:
            item: The item to remove from the list
            
        Raises:
            ValueError: If the item is not in the list
        """
        current = self._primary_hooks["value"].value
        if item not in current:
            raise ValueError(f"{item} not in list")
        
        # Create new list without the first occurrence
        new_list = list(current)
        new_list.remove(item)
        self.change_list(new_list)
    
    def pop(self, index: int = -1) -> T:
        """
        Remove and return the item at the specified index.
        
        Creates a new tuple without the popped item.
        
        Args:
            index: The index of the item to remove (default: -1, last item)
            
        Returns:
            The removed item
            
        Raises:
            IndexError: If the index is out of range
        """
        current = self._primary_hooks["value"].value
        new_list = list(current)
        item: T = new_list.pop(index)
        self.change_list(new_list)
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the list.
        
        Creates an empty list.
        """
        if self._primary_hooks["value"].value:
            self.change_list([])
    
    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> None:
        """
        Sort the list in place.
        
        Creates a new sorted tuple.
        
        Args:
            key: Optional function to extract comparison key from each element
            reverse: If True, sort in descending order (default: False)
        """
        current_value = self._primary_hooks["value"].value
        self.change_list(sorted(current_value, key=key, reverse=reverse)) # type: ignore
    
    def reverse(self) -> None:
        """
        Reverse the elements of the list in place.
        
        Creates a new tuple with elements in reversed order.
        """
        current_value = self._primary_hooks["value"].value
        self.change_list(reversed(current_value)) # type: ignore
    
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of a value in the list.
        
        Args:
            item: The item to count
            
        Returns:
            The number of times the item appears in the list
        """
        return list(self._primary_hooks["value"].value).count(item)
    
    def index(self, item: T, start: int = 0, stop: Optional[int] = None) -> int:
        """
        Return the first index of a value in the list.
        
        Args:
            item: The item to find
            start: Start index for the search (default: 0)
            stop: End index for the search (default: end of list)
            
        Returns:
            The index of the first occurrence of the item
            
        Raises:
            ValueError: If the item is not found in the specified range
        """
        list_value = list(self._primary_hooks["value"].value)
        if stop is None:
            return list_value.index(item, start)
        else:
            return list_value.index(item, start, stop)
    
    def __str__(self) -> str:
        return f"OL(value={self._primary_hooks['value'].value})"
    
    def __repr__(self) -> str:
        return f"XList({self._primary_hooks['value'].value})"
    
    def __len__(self) -> int:
        """
        Get the length of the list.
        
        Returns:
            The number of items in the list
        """
        return len(list(self._primary_hooks["value"].value))
    
    def __getitem__(self, index: int) -> T:
        """
        Get an item at the specified index or slice.
        
        Args:
            index: Integer index or slice object
            
        Returns:
            The item at the index or a slice of items
            
        Raises:
            IndexError: If the index is out of range
        """
        return list(self._primary_hooks["value"].value)[index]
    
    def __setitem__(self, index: int, value: T) -> None:
        """
        Set an item at the specified index.
        
        Creates a new tuple with the item replaced.
        
        Args:
            index: Integer index
            value: The value to set
            
        Raises:
            IndexError: If the index is out of range
        """
        current = self._primary_hooks["value"].value
        # Modify list
        new_list = list(current)
        new_list[index] = value
        if new_list != current:
            self.change_list(new_list)
    
    def __delitem__(self, index: int) -> None:
        """
        Delete an item at the specified index.
        
        Creates a new tuple without the deleted item.
        
        Args:
            index: Integer index
            
        Raises:
            IndexError: If the index is out of range
        """
        current = self._primary_hooks["value"].value
        # Create list without the item at index
        new_list = list(current)
        del new_list[index]
        self.change_list(new_list)
    
    def __contains__(self, item: T) -> bool:
        """
        Check if an item is contained in the list.
        
        Args:
            item: The item to check for
            
        Returns:
            True if the item is in the list, False otherwise
        """
        return item in self._primary_hooks["value"].value
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the list items.
        
        Returns:
            An iterator that yields each item in the list
        """
        return iter(self._primary_hooks["value"].value)
    
    def __reversed__(self) -> Iterator[T]:
        """
        Get a reverse iterator over the list items.
        
        Returns:
            A reverse iterator that yields each item in the list in reverse order
        """
        return reversed(list(self._primary_hooks["value"].value))
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if the lists contain the same items in the same order, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"].value == other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value == other
    
    def __ne__(self, other: Any) -> bool:
        """
        Check inequality with another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if the lists are not equal, False otherwise
        """
        return not (self == other)
    
    def __lt__(self, other: Any) -> bool:
        """
        Check if this list is less than another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if this list is lexicographically less than the other, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"].value < other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value < other
    
    def __le__(self, other: Any) -> bool:
        """
        Check if this list is less than or equal to another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if this list is lexicographically less than or equal to the other, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"].value <= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value <= other
    
    def __gt__(self, other: Any) -> bool:
        """
        Check if this list is greater than another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if this list is lexicographically greater than the other, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"].value > other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value > other
    
    def __ge__(self, other: Any) -> bool:
        """
        Check if this list is greater than or equal to another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if this list is lexicographically greater than or equal to the other, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"].value >= other._primary_hooks["value"].value # type: ignore
        return self._primary_hooks["value"].value >= other
    
    def __add__(self, other: Any) -> tuple[T, ...]:
        """
        Concatenate this list with another list or observable list.
        
        Args:
            other: Another iterable or XList to concatenate with
            
        Returns:
            A new tuple containing all items from both collections
        """
        current_value = self._primary_hooks["value"].value
        if isinstance(other, XList):
            return list(current_value) + list(other._primary_hooks["value"].value) # type: ignore
        return list(current_value) + list(other) # type: ignore
    
    def __mul__(self, other: int) -> tuple[T, ...]:
        """
        Repeat the list a specified number of times.
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new tuple with the original items repeated
        """
        return self._primary_hooks["value"].value * other # type: ignore
    
    def __rmul__(self, other: int) -> tuple[T, ...]:
        """
        Repeat the list a specified number of times (right multiplication).
        
        Args:
            other: The number of times to repeat the list
            
        Returns:
            A new tuple with the original items repeated
        """
        return other * self._primary_hooks["value"].value # type: ignore
    
    def __hash__(self) -> int:
        """
        Get the hash value based on the current list contents.
        
        Returns:
            Hash value of the tuple
        """
        return hash(self._primary_hooks["value"].value)