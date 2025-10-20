from typing import Callable, Literal, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from .subscriber import Subscriber

@runtime_checkable
class PublisherProtocol(Protocol):

    def add_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Add a subscriber or callback to receive publications from this publisher.
        """
        ...

    def remove_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Remove a subscriber or callback so it no longer receives publications.
        """
        ...

    def publish(self, mode: Literal["async", "sync", "direct", "off", None]) -> None:
        """
        Publish an update to all subscribed subscribers asynchronously.
        """
        ...

    @property
    def preferred_publish_mode(self) -> Literal["async", "sync", "direct", "off"]:
        """
        Get the preferred publish mode for this publisher.
        """
        ...

    @preferred_publish_mode.setter
    def preferred_publish_mode(self, mode: Literal["async", "sync", "direct", "off"]) -> None:
        """
        Set the preferred publish mode for this publisher.
        """
        ...