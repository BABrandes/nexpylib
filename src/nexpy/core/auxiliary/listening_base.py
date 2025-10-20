from typing import Callable, Optional, Any
from logging import Logger
from typing_extensions import deprecated

from .listening_protocol import ListeningProtocol

class ListeningBase(ListeningProtocol):
    """
    Base class providing listener management functionality for observables.
    
    This class implements the core listener pattern used by all observable classes.
    It manages a collection of callback functions that are notified when the
    observable's value changes. The class provides methods to add, remove, and
    manage listeners, as well as to notify them of changes.
    
    Features:
    - Automatic duplicate prevention
    - Safe listener removal (ignores non-existent listeners)
    - Bulk listener operations
    - Listener existence checking
    
    Example:
        >>> class MyObservable(ListeningBase):
        ...     def __init__(self, value):
        ...         super().__init__()
        ...         self._value = value
        ...     
        ...     def set_value(self, new_value):
        ...         if new_value != self._value:
        ...             self._value = new_value
        ...             self._notify_listeners()
        ...     
        ...     @property
        ...     def value(self):
        ...         return self._value
    
        >>> # Create observable and add listeners
        >>> obs = MyObservable(10)
        >>> obs.add_listeners(
        ...     lambda: print("Value changed!"),
        ...     lambda: print(f"New value: {obs.value}")
        ... )
        >>> obs.set_value(20)
        Value changed!
        New value: 20
    """

    def __init__(self, logger: Optional[Logger] = None, **kwargs: Any):
        """
        Initialize the ListeningBase with an empty set of listeners.
        """
        self._listeners: set[Callable[[], None]] = set()
        self._logger: Optional[Logger] = logger

    @property
    def listeners(self) -> set[Callable[[], None]]:
        """
        Get a copy of all registered listeners.
        
        Returns:
            A copy of the current listeners set to prevent external modification
        """
        return self._listeners.copy()

    @deprecated("Will be removed in the future. Use add_listener instead.")
    def add_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners to the observable.
        """
        self.add_listener(*callbacks)

    def add_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners to the observable.
        
        This method adds callback functions that will be called whenever the
        observable's value changes. Duplicate callbacks are automatically
        prevented to avoid multiple notifications for the same listener.
        
        Args:
            *callbacks: Variable number of callback functions to add.
                       Each callback should take no arguments and return None.
                       Callbacks are called when _notify_listeners() is invoked.
        
        Example:
            >>> obs = MyObservable(10)
            >>> obs.add_listeners(
            ...     lambda: print("First listener"),
            ...     lambda: print("Second listener")
            ... )
            >>> obs.set_value(20)  # Both listeners will be called
        """
        # Prevent duplicate listeners
        for callback in callbacks:
            if callback not in self._listeners:
                self._listeners.add(callback)

        self._log("add_listeners", True, f"Successfully added {len(callbacks)} listeners")

    def add_listener_and_call_once(self, *callbacks: Callable[[], None]) -> None:
        """
        Add a listener and call it once.
        """
        for callback in callbacks:
            self._listeners.add(callback)
        for callback in callbacks:
            callback()
        self._log("add_listener_and_call_once", True, f"Successfully added {len(callbacks)} listeners and called them once")

    def remove_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove one or more listeners from the observable.
        
        This method safely removes callback functions from the observable.
        If a callback doesn't exist, it's silently ignored. This makes it
        safe to remove listeners multiple times or remove non-existent ones.
        
        Args:
            *callbacks: Variable number of callback functions to remove.
                       Each callback should match one that was previously added.
        
        Example:
            >>> obs = MyObservable(10)
            >>> callback = lambda: print("Hello")
            >>> obs.add_listeners(callback)
            >>> obs.remove_listeners(callback)  # Listener removed
            >>> obs.remove_listeners(callback)  # Safe to call again
        """
        for callback in callbacks:
            try:
                self._listeners.remove(callback)
            except KeyError:
                # Ignore if callback doesn't exist
                pass
        self._log("remove_listeners", True, f"Successfully removed {len(callbacks)} listeners")

    @deprecated("Will be removed in the future. Use remove_listener instead.")
    def remove_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove one or more listeners from the observable.
        """
        self.remove_listener(*callbacks)

    def remove_all_listeners(self) -> set[Callable[[], None]]:
        """
        Remove all listeners from the observable.
        
        This method clears all registered listeners and returns them as a set.
        This is useful for cleanup operations or when you need to temporarily
        disable all notifications.
        
        Returns:
            A set containing all previously registered listeners
            
        Example:
            >>> obs = MyObservable(10)
            >>> obs.add_listeners(lambda: print("A"), lambda: print("B"))
            >>> removed = obs.remove_all_listeners()
            >>> print(f"Removed {len(removed)} listeners")
            Removed 2 listeners
        """
        removed_listeners = self._listeners
        self._listeners = set()
        self._log("remove_all_listeners", True, f"Successfully removed {len(removed_listeners)} listeners")
        return removed_listeners

    def has_listeners(self) -> bool:
        """
        Check if there are any listeners registered.
        """
        return len(self._listeners) > 0

    def _notify_listeners(self):
        """
        Notify all registered listeners of a change.
        
        This method calls all registered callback functions. It's typically
        called by subclasses when the observable's value changes. The method
        iterates through all listeners and calls each one.
        
        Note:
            This is an internal method intended to be called by subclasses.
            It should be called whenever the observable's state changes
            and listeners need to be notified.
        
        Example:
            >>> class MyObservable(ListeningBase):
            ...     def set_value(self, new_value):
            ...         if new_value != self._value:
            ...             self._value = new_value
            ...             self._notify_listeners()  # Notify all listeners
        """
        # Create a copy of listeners to avoid modification during iteration
        listeners_copy = list(self._listeners)
        for callback in listeners_copy:
            try:
                callback()
            except RuntimeError:
                # RuntimeError indicates a programming error (like recursive submit_values)
                # that should not be silently caught - re-raise it immediately
                raise
            except Exception as e:
                self._log("notify_listeners", False, f"Error in listener callback: {e}")
                continue
        self._log("notify_listeners", True, "Successfully notified listeners")
    
    def is_listening_to(self, callback: Callable[[], None]) -> bool:
        """
        Check if a specific callback is registered as a listener.
        
        Args:
            callback: The callback function to check
            
        Returns:
            True if the callback is registered, False otherwise
            
        Example:
            >>> obs = MyObservable(10)
            >>> callback = lambda: print("Hello")
            >>> print(obs.is_listening_to(callback))  # False
            >>> obs.add_listeners(callback)
            >>> print(obs.is_listening_to(callback))  # True
        """
        return callback in self._listeners
    
    def _log(self, action: str, success: bool, msg: str) -> None:
        """
        Log a message to the logger.
        """
        if self._logger is not None:
            if not success:
                self._logger.debug(f"BaseListening ({self}): Action {action} returned False: {msg}")
            else:
                self._logger.debug(f"BaseListening ({self}): Action {action} returned True")