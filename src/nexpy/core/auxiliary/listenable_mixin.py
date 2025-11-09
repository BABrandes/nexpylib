from typing import Callable, Literal
import warnings

from .listenable_protocol import ListenableProtocol

class ListenableMixin(ListenableProtocol):
    """
    Mixin providing listener management functionality for objects that are listenable.
    """

    def __init__(self) -> None:
        """
        Initialize the ListenableMixin with an empty set of listeners.
        """
        super().__init__()
        self._listeners: set[Callable[[], None]] = set()

    @property
    def listeners(self) -> set[Callable[[], None]]:
        """
        Get a copy of all registered listeners.
        
        Returns:
            A copy of the current listeners set to prevent external modification
        """
        return self._listeners.copy()

    def add_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners to the listenable.
        """
        # Prevent duplicate listeners
        for callback in callbacks:
            if callback not in self._listeners:
                self._listeners.add(callback)

    def add_listener_and_call_once(self, *callbacks: Callable[[], None]) -> None:
        """
        Add a listener and call it once.
        """
        for callback in callbacks:
            self._listeners.add(callback)
        for callback in callbacks:
            callback()

    def remove_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove one or more listeners from the listenable.
        """
        for callback in callbacks:
            try:
                self._listeners.remove(callback)
            except KeyError:
                # Ignore if callback doesn't exist
                pass

    def remove_all_listeners(self) -> set[Callable[[], None]]:
        """
        Remove all listeners from the listenable.
        """
        removed_listeners = self._listeners
        self._listeners = set()
        return removed_listeners

    def has_listeners(self) -> bool:
        """
        Check if there are any listeners registered.
        """
        return len(self._listeners) > 0

    def _notify_listeners(self, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:

        # Create a copy of listeners to avoid modification during iteration
        listeners_copy = list(self._listeners)
        for callback in listeners_copy:
            if raise_error_mode == "raise":
                try:
                    callback()
                except Exception as e:
                    raise e
            elif raise_error_mode == "ignore":
                try:
                    callback()
                except Exception:
                    pass
            elif raise_error_mode == "warn":
                try:
                    callback()
                except Exception as e:
                    warnings.warn(f"Error in listener callback: {e}")
    
    def is_listening_to(self, callback: Callable[[], None]) -> bool:
        """
        Check if a specific callback is registered as a listener.
        
        Args:
            callback: The callback function to check
            
        Returns:
            True if the callback is registered, False otherwise
            
        Example:
            >>> listenable = MyListenable(10)
            >>> callback = lambda: print("Hello")
            >>> print(listenable.is_listening_to(callback))  # False
            >>> listenable.add_listeners(callback)
            >>> print(listenable.is_listening_to(callback))  # True
        """
        return callback in self._listeners