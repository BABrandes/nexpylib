"""
Subscriber module for the Publisher-Subscriber pattern implementation.

This module provides the abstract base Subscriber class that receives and reacts
to publications from Publishers. Subscribers use weak references to track their
publishers for automatic memory management.

**Asynchronous Reaction Pattern**

Subscribers implement asynchronous reactions to publications:

- **Async Execution**: Reactions are defined as `async def` methods and run
  independently in the event loop without blocking the publisher or other
  subscribers.
  
- **Non-Blocking**: Reactions can perform I/O operations, network calls, or
  other async operations without affecting the publisher's performance.
  
- **Unidirectional**: Subscribers observe publications but cannot validate or
  reject them. By the time a subscriber reacts, the publisher's state has
  already been committed.

Example:
    Creating a custom subscriber with async operations::

        from observables._utils.subscriber import Subscriber
        from observables._utils.publisher import Publisher
        import asyncio
        
        class DatabaseSubscriber(Subscriber):
            async def _react_to_publication(self, publisher: Publisher) -> None:
                # This runs asynchronously without blocking the publisher
                print(f"Received publication from {publisher}")
                
                # Perform async operations (network, database, file I/O)
                await save_to_database()
                await send_notification()
                
                print("Async reaction complete")
        
        # Usage
        publisher = Publisher()
        subscriber = DatabaseSubscriber()
        publisher.add_subscriber(subscriber)
        
        # Trigger async reaction (returns immediately)
        publisher.publish()
        print("Published! (reaction happening in background)")
"""

import weakref
import asyncio
from typing import TYPE_CHECKING, Literal

from ..auxiliary.weak_reference_storage import WeakReferenceStorage

if TYPE_CHECKING:
    from .publisher import Publisher

class Subscriber():
    """
    Abstract base class for objects that subscribe to and react to Publishers.
    
    Subscribers receive asynchronous notifications from Publishers via the
    `react_to_publication` method. Concrete subclasses must implement the
    `_react_to_publication` async method to define their reaction behavior.
    
    **Asynchronous Non-Blocking Architecture**
    
    - Reactions are executed as asyncio tasks that run independently
    - The `react_to_publication` method creates a task and returns immediately
    - Multiple subscribers react in parallel without blocking each other
    - Ideal for I/O-bound operations: network requests, database writes, file operations
    - Exceptions in one subscriber's reaction don't affect other subscribers
    
    **Unidirectional Communication**
    
    - Subscribers can only observe and react to publications
    - Cannot validate, reject, or influence the publisher's state
    - Reactions occur after the publisher's state is already committed
    - Suitable for side effects and external system synchronization
    
    **Automatic Memory Management**
    
    The Subscriber uses weak references to track publishers, enabling automatic
    cleanup when publishers are garbage collected. It supports threshold-based
    cleanup (time and size) to maintain performance.
    
    Attributes:
        _publisher_storage (WeakReferenceStorage): Manages weak references to publishers.
        _cleanup_interval (float): Time threshold for cleanup (default: 60 seconds).
        _max_publishers_before_cleanup (int): Size threshold for cleanup (default: 1000).
    
    Example:
        Implementing a custom subscriber::
        
            from observables._utils.subscriber import Subscriber
            from observables._utils.publisher import Publisher
            import asyncio
            
            class LoggingSubscriber(Subscriber):
                def __init__(self):
                    super().__init__()
                    self.publication_count = 0
                
                async def _react_to_publication(self, publisher: Publisher) -> None:
                    # This method is called asynchronously when publisher publishes
                    self.publication_count += 1
                    print(f"Publication #{self.publication_count} from {publisher}")
                    
                    # Can perform async operations
                    await asyncio.sleep(0.1)
                    print("Reaction complete")
            
            # Create and use
            publisher = Publisher()
            subscriber = LoggingSubscriber()
            publisher.add_subscriber(subscriber)
            
            # Trigger async reaction
            publisher.publish()
    
    Note:
        Subclasses must implement the `_react_to_publication` method. If not
        implemented, NotImplementedError will be raised when a publication occurs.
    """

    def __init__(
        self,
        cleanup_interval: float = 60.0,  # seconds
        max_publishers_before_cleanup: int = 1000
        ) -> None:
        """
        Initialize a new Subscriber.
        
        Sets up the weak reference tracking system with default cleanup thresholds:
        - Time-based cleanup: Every 60 seconds
        - Size-based cleanup: When 1000 publisher references accumulate
        
        These defaults are suitable for most use cases but can be adjusted by
        modifying the StoresWeakReferences initialization in subclasses if needed.
        """

        self._publisher_storage: WeakReferenceStorage[Publisher] = WeakReferenceStorage(
            cleanup_interval=cleanup_interval,
            max_references_before_cleanup=max_publishers_before_cleanup
        )

    def _add_publisher_called_by_subscriber(self, publisher: "Publisher") -> None:
        """
        Internal method to add a publisher to this subscriber's tracking list.
        
        This method is called automatically by Publisher.add_subscriber() to
        maintain bidirectional references between publishers and subscribers.
        
        Args:
            publisher: The Publisher instance to track.
        
        Note:
            This is an internal method. Users should not call it directly.
            Use Publisher.add_subscriber() instead to properly establish
            the publisher-subscriber relationship.
        """
        self._publisher_storage.cleanup()
        self._publisher_storage.add_reference(weakref.ref(publisher))

    def _remove_publisher_called_by_subscriber(self, publisher: "Publisher") -> None:
        """
        Internal method to remove a publisher from this subscriber's tracking list.
        
        This method is called automatically by Publisher.remove_subscriber() to
        maintain bidirectional references between publishers and subscribers.
        
        Args:
            publisher: The Publisher instance to remove.
        
        Raises:
            ValueError: If the publisher is not currently tracked by this subscriber.
        
        Note:
            This is an internal method. Users should not call it directly.
            Use Publisher.remove_subscriber() instead to properly break
            the publisher-subscriber relationship.
        """
        self._publisher_storage.cleanup()
        publisher_ref_to_remove = None
        for publisher_ref in self._publisher_storage.weak_references:
            pub = publisher_ref()
            if pub is publisher:
                publisher_ref_to_remove = publisher_ref
                break
        if publisher_ref_to_remove is None:
            raise ValueError("Publisher not found")
        self._publisher_storage.remove_reference(publisher_ref_to_remove)

    def react_to_publication_task(self, publisher: "Publisher", mode: Literal["async", "sync"]) -> asyncio.Task[None]:
        """
        React to a publication from a publisher (entry point for async reaction).
        
        This method is called by the Publisher when it publishes. It creates an
        asynchronous task that executes the `_react_to_publication` method,
        allowing reactions to run independently without blocking the publisher.
        
        Args:
            publisher: The Publisher that triggered this reaction.
        
        Returns:
            An asyncio.Task that executes the `_react_to_publication` coroutine.
            The Publisher uses this task to track completion and handle errors.
        
        Note:
            This method is called automatically by Publisher.publish(). Users
            typically don't need to call it directly. Subclasses should implement
            `_react_to_publication` instead of overriding this method.
        
        Example:
            Typical flow::
            
                # Publisher calls this automatically
                publisher.publish()
                  ↓
                subscriber.react_to_publication(publisher)
                  ↓
                asyncio.create_task(subscriber._react_to_publication(publisher))
                  ↓
                # Your custom _react_to_publication logic runs asynchronously
        """
        self._publisher_storage.cleanup()
        loop = asyncio.get_event_loop()
        return loop.create_task(self._react_async_to_publication(publisher, mode))

    async def _react_async_to_publication(self, publisher: "Publisher", mode: Literal["async", "sync"]) -> None:
        self._react_to_publication(publisher, mode)

    def _react_to_publication_direct(self, publisher: "Publisher") -> None:
        self._react_to_publication(publisher, "direct")

    def _react_to_publication(self, publisher: "Publisher", mode: Literal["async", "sync", "direct"]) -> None:
        """
        Abstract method to define how this subscriber reacts to a publication.
        
        This async method is called when a publisher publishes an update. Subclasses
        must implement this method to define their specific reaction behavior.
        
        The method runs asynchronously, so it can perform async operations without
        blocking the publisher or other subscribers. Any exceptions raised will be
        caught and handled by the Publisher (logged if a logger is configured,
        or raised as RuntimeError if not).
        
        Args:
            publisher: The Publisher that triggered this reaction. This allows
                the subscriber to identify which publisher sent the notification
                and react accordingly.
        
        Raises:
            NotImplementedError: If not overridden by a subclass.
        
        Example:
            Implementing reaction logic::
            
                class DataSubscriber(Subscriber):
                    def __init__(self, data_store):
                        super().__init__()
                        self.data_store = data_store
                    
                    async def _react_to_publication(self, publisher: Publisher) -> None:
                        # Fetch data asynchronously
                        data = await fetch_data_from_source()
                        
                        # Process it
                        processed = process_data(data)
                        
                        # Store results
                        self.data_store.save(processed)
                        
                        print(f"Processed publication from {publisher}")
        
        Note:
            - This method must be async (defined with `async def`)
            - It receives the publisher as a parameter
            - Exceptions are caught and handled by the Publisher
            - Multiple subscribers' reactions run independently in parallel
        """
        raise NotImplementedError("Subclass must implement _react_to_publication")
