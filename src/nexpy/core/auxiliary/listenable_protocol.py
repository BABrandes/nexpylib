from typing import Callable, Protocol, runtime_checkable

@runtime_checkable
class ListenableProtocol(Protocol):
    """
    Protocol defining the interface for all objects that are listenable.
    """
    ...

    @property
    def listeners(self) -> set[Callable[[], None]]:
        """
        Get the listeners.
        """
        ...

    def add_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners to the listenable.
        """
        ...

    def add_listener_and_call_once(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners and call them once.
        """
        ...

    def remove_listener(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove one or more listeners from the listenable.
        """
        ...

    def remove_all_listeners(self) -> set[Callable[[], None]]:
        """
        Remove all listeners from the listenable.
        """
        ...

    def is_listening_to(self, callback: Callable[[], None]) -> bool:
        """
        Check if a specific callback is registered as a listener.
        """
        ...

    def has_listeners(self) -> bool:
        """
        Check if there are any listeners registered.
        """
        ...

    def _notify_listeners(self) -> None:
        """
        Notify the listeners.
        """
        ...