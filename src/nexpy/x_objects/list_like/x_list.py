from typing import Generic, TypeVar, Callable, Literal, Optional, Any, Mapping, Self
from collections.abc import Iterator, Sequence
from logging import Logger

from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook
from nexpy.core.hooks.protocols.hook_protocol import HookProtocol
from ...foundations.x_composite_base import XCompositeBase
from ...core.nexus_system.submission_error import SubmissionError
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from .protocols import XListProtocol

T = TypeVar("T")
  

class XList(XCompositeBase[Literal["value"], Literal["length"], Sequence[T], int], XListProtocol[T], Generic[T]):
    """
    Reactive list wrapper providing seamless integration with NexPy's synchronization system.

    XList[T] is a reactive container for sequences that behaves like a standard Python list
    but with automatic change notifications, validation, and synchronization capabilities.
    The generic type parameter T specifies the type of elements in the list.

    Type Parameters
    ---------------
    T : TypeVar
        The type of elements stored in the list.
        Examples: XList[int], XList[str], XList[MyClass]

    Key Features
    ------------
    - **Reactive Updates**: Automatic notification when list contents change
    - **Sequence Compatibility**: Works with any Sequence type (list, tuple, etc.)
    - **Hook Fusion**: Join with other XList instances or hooks for synchronization
    - **Length Tracking**: Automatic secondary hook tracking list length
    - **Validation**: Optional custom validation for list updates
    - **Type-Safe**: Full generic type support

    See Also
    --------
    XSet : For set-like reactive containers
    XDict : For dict-like reactive containers
    XValue : For single-value reactive containers
    """
    def __init__(
        self,
        value: Sequence[T] | HookProtocol[Sequence[T]] | XListProtocol[T] | None = None,
        *,
        logger: Optional[Logger] = None,
        custom_validator: Optional[Callable[[Mapping[Literal["value", "length"], Any]], tuple[bool, str]]] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
        ) -> None:
        """
        Initialize a reactive list container.

        The generic type T specifies the element type. Use square bracket notation to specify:
        XList[int], XList[str], XList[MyClass], etc.

        Parameters
        ----------
        value : Sequence[T] | Hook[Sequence[T]] | XList[T] | None, optional
            Initial list contents or hook/XList to connect to:
            - Sequence[T]: Any sequence (list, tuple, etc.) to copy
            - Hook[Sequence[T]]: External hook to join with
            - XList[T]: Another XList to join with
            - None: Create empty list (default)

        logger : Logger, optional
            Logger instance for debugging operations.

        custom_validator : Callable[[Mapping[str, Any]], tuple[bool, str]], optional
            Custom validation function for value updates.
            Receives {"value": Sequence[T], "length": int}.
            Returns (True, "message") if valid, (False, "error") if invalid.

        nexus_manager : NexusManager, optional
            The NexusManager coordinating synchronization.
            Defaults to global DEFAULT_NEXUS_MANAGER.

        Examples
        --------
        Create an empty list:

        >>> numbers = XList[int]()
        >>> numbers.list
        []

        Initialize with values:

        >>> fruits = XList[str](["apple", "banana", "cherry"])
        >>> fruits.list
        ['apple', 'banana', 'cherry']

        Connect two lists:

        >>> source = XList[int]([1, 2, 3])
        >>> mirror = XList[int](source)  # Joins with source
        >>> source.list = [4, 5, 6]
        >>> mirror.list  # Automatically synchronized
        [4, 5, 6]

        With validation:

        >>> def validate_positive(values):
        ...     if all(x > 0 for x in values["value"]):
        ...         return True, "Valid"
        ...     return False, "All numbers must be positive"
        >>> positive_nums = XList[int]([1, 2, 3], custom_validator=validate_positive)

        Type-specific lists:

        >>> class Person:
        ...     def __init__(self, name: str):
        ...         self.name = name
        >>> people = XList[Person]([Person("Alice"), Person("Bob")])
        """


        if value is None:
            initial_value: Sequence[T] = ()
            hook: Optional[HookProtocol[Sequence[T]]] = None

        elif isinstance(value, XListProtocol):
            initial_value = value.list
            hook = value.list_hook

        elif isinstance(value, HookProtocol):
            initial_value = value.value
            hook = value

        elif isinstance(value, Sequence): # type: ignore
            # It's a sequence
            if isinstance(value, (str, bytes)):
                raise ValueError("String and bytes are not valid initial values for XList")
            initial_value = value
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
    def list_hook(self) -> OwnedWritableHook[Sequence[T], Self]:
        """
        Get the hook for the list (contains Sequence).
        """
        return self._primary_hooks["value"]

    @property
    def list(self) -> list[T]:
        """
        Get the list value as mutable list (copied from the hook).
        """
        value = self._primary_hooks["value"]._get_value() # type: ignore
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
    def length_hook(self) -> OwnedReadOnlyHook[int, Self]:
        """
        Get the hook for the list length.
        """
        return self._secondary_hooks["length"]

    @property
    def length(self) -> int:
        """
        Get the current length of the list.
        """
        return self._get_value_by_key("length") # type: ignore

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
        current_value: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        new_list: list[T] = list[T](current_value) + [item]
        self.change_list(new_list)
    
    def extend(self, iterable: Sequence[T]) -> None:
        """
        Extend the list by appending elements from the iterable.
        
        Creates a new tuple with the extended elements.
        
        Args:
            iterable: The iterable containing elements to add
        """
        current_value: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        new_list: list[T] = list[T](current_value) + list[T](iterable)
        self.change_list(new_list)
    
    def insert(self, index: int, item: T) -> None:
        """
        Insert an item at a given position.
        
        Creates a new tuple with the item inserted.
        
        Args:
            index: The position to insert the item at
            item: The item to insert
        """
        current: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        new_list: list[T] = list[T](current)
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
        current: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        if item not in current:
            raise ValueError(f"{item} not in list")
        
        # Create new list without the first occurrence
        new_list: list[T] = list[T](current)
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
        current: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        new_list: list[T] = list[T](current)
        item: T = new_list.pop(index)
        self.change_list(new_list)
        return item
    
    def clear(self) -> None:
        """
        Remove all items from the list.
        
        Creates an empty list.
        """
        if self._primary_hooks["value"]._get_value() is not None: # type: ignore
            self.change_list([])
    
    def sort(self, key: Optional[Callable[[T], Any]] = None, reverse: bool = False) -> None:
        """
        Sort the list in place.
        
        Creates a new sorted tuple.
        
        Args:
            key: Optional function to extract comparison key from each element
            reverse: If True, sort in descending order (default: False)
        """
        current_value: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        self.change_list(sorted(current_value, key=key, reverse=reverse)) # type: ignore
    
    def reverse(self) -> None:
        """
        Reverse the elements of the list in place.
        
        Creates a new tuple with elements in reversed order.
        """
        current_value: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        self.change_list(reversed(current_value)) # type: ignore
    
    def count(self, item: T) -> int:
        """
        Return the number of occurrences of a value in the list.
        
        Args:
            item: The item to count
            
        Returns:
            The number of times the item appears in the list
        """
        return list[T](self._primary_hooks["value"]._get_value()).count(item) # type: ignore
    
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
        list_value: list[T] = list[T](self._primary_hooks["value"]._get_value()) # type: ignore
        if stop is None:
            return list_value.index(item, start)
        else:
            return list_value.index(item, start, stop)
    
    def __str__(self) -> str:
        return f"OL(value={self._primary_hooks['value']._get_value()})" # type: ignore
    
    def __repr__(self) -> str:
        return f"XList({self._primary_hooks['value']._get_value()})" # type: ignore
    
    def __len__(self) -> int:
        """
        Get the length of the list.
        
        Returns:
            The number of items in the list
        """
        return len(list[T](self._primary_hooks["value"]._get_value())) # type: ignore
    
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
        return list[T](self._primary_hooks["value"]._get_value())[index] # type: ignore
    
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
        current: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
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
        current: Sequence[T] = self._primary_hooks["value"]._get_value() # type: ignore
        # Create list without the item at index
        new_list: list[T] = list[T](current)
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
        return item in self._primary_hooks["value"]._get_value() # type: ignore
    
    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the list items.
        
        Returns:
            An iterator that yields each item in the list
        """
        return iter(self._primary_hooks["value"]._get_value()) # type: ignore
    
    def __reversed__(self) -> Iterator[T]:
        """
        Get a reverse iterator over the list items.
        
        Returns:
            A reverse iterator that yields each item in the list in reverse order
        """
        return reversed(list[T](self._primary_hooks["value"]._get_value())) # type: ignore
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another list or observable list.
        
        Args:
            other: Another list or XList to compare with
            
        Returns:
            True if the lists contain the same items in the same order, False otherwise
        """
        if isinstance(other, XList):
            return self._primary_hooks["value"]._get_value() == other._primary_hooks["value"]._get_value() # type: ignore
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
        """Make XList hashable using UUID from XBase."""
        if hasattr(self, '_uuid'):
            return hash(self._uuid)
        else:
            # Fall back to id during initialization
            return hash(id(self))