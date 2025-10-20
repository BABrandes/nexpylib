from typing import Callable, Protocol, runtime_checkable

@runtime_checkable
class ListeningProtocol(Protocol):
    """
    Protocol defining the interface for all listening objects in the library.
    """
    ...

    @property
    def listeners(self) -> set[Callable[[], None]]:
        """
        Get the listeners.
        """
        ...

    def add_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners to the observable.
        """
        ...

    def add_listener_and_call_once(self, *callbacks: Callable[[], None]) -> None:
        """
        Add one or more listeners and call them once.
        """
        ...

    def remove_listeners(self, *callbacks: Callable[[], None]) -> None:
        """
        Remove one or more listeners from the observable.
        """
        ...

    def remove_all_listeners(self) -> set[Callable[[], None]]:
        """
        Remove all listeners from the observable.
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