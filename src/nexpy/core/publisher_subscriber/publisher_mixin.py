"""
Publisher module for the Publisher-Subscriber pattern implementation.

This module provides a lightweight, async-enabled Publisher class that manages
subscriptions and publishes updates to subscribers using weak references for
automatic memory management.

**Asynchronous Unidirectional Notifications**

The Publisher-Subscriber pattern in this module is designed for asynchronous,
unidirectional communication:

- **Asynchronous**: Publications trigger async subscriber reactions that run
  independently in the event loop. The `publish()` method returns immediately
  without blocking for subscriber reactions to complete.
  
- **Unidirectional**: Subscribers can only observe and react to publications.
  They cannot validate, reject, or influence the publisher's state.
  
- **Non-blocking**: Ideal for decoupled components performing I/O operations,
  network calls, database writes, or other async operations that should not
  block the main execution flow.

Example:
    Basic publisher-subscriber setup::

        from observables._utils.publisher import Publisher
        from observables._utils.subscriber import Subscriber
        
        # Create a custom subscriber
        class MySubscriber(Subscriber):
            async def _react_to_publication(self, publisher):
                # This runs asynchronously, doesn't block the publisher
                await perform_async_operation()
        
        publisher = Publisher(logger=logger)
        subscriber = MySubscriber()
        publisher.add_subscriber(subscriber)
        
        # Publish to all subscribers (returns immediately)
        publisher.publish()
        # Subscriber reactions happen in the background
"""

from typing import Callable, Literal, Optional, TYPE_CHECKING
import warnings
import weakref
import asyncio
from logging import Logger

from ..auxiliary.weak_reference_storage import WeakReferenceStorage

if TYPE_CHECKING:
    from .subscriber import Subscriber

class PublisherMixin():
    """
    A mixin that adds publisher functionality to a class.
    
    This mixin provides the core publisher functionality, including:
    
    - Adding and removing subscribers
    - Publishing updates to subscribers
    - Handling publication exceptions
    - Managing publication modes
    
    This design is ideal for scenarios where reactions may involve I/O operations,
    network calls, or other potentially slow operations that should not block the
    publisher or other subscribers.
    
    Attributes:
        _logger (Optional[Logger]): Logger for error reporting.
        _references (set): Set of weak references to subscribers (inherited).
        _cleanup_interval (float): Time threshold for cleanup (inherited).
        _max_subscribers_before_cleanup (int): Size threshold for cleanup (inherited).
    
    Example:
        Basic publisher usage::
        
            import logging
            from observables._utils.publisher import Publisher
            
            # Create publisher with logging
            logger = logging.getLogger(__name__)
            publisher = Publisher(
                logger=logger,
                cleanup_interval=60.0,  # Cleanup every 60 seconds
                max_subscribers_before_cleanup=100  # Or when 100 subscribers
            )
            
            # Add subscribers
            publisher.add_subscriber(subscriber1)
            publisher.add_subscriber(subscriber2)
            
            # Check subscription
            if publisher.is_subscribed(subscriber1):
                print("Subscriber is subscribed")
            
            # Publish to all subscribers
            publisher.publish()
            
            # Remove a subscriber
            publisher.remove_subscriber(subscriber1)
    """

    def __init__(
        self,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"] = "sync",
        logger: Optional[Logger] = None,
        cleanup_interval: float = 60.0,  # seconds
        max_subscribers_before_cleanup: int = 100
        ) -> None:
        """
        Initialize a new Publisher.
        
        Args:
            preferred_publish_mode: The default publication mode to use when 
                publish(mode=None) is called. Defaults to "sync".
                - "async": Non-blocking, returns immediately
                - "sync": Blocking, waits for completion (good for testing)
                - "direct": Synchronous without asyncio overhead
                - "off": Disables publishing (no notifications sent)
            logger: Optional logger for error reporting. If provided, subscriber
                errors will be logged. If None, errors will raise RuntimeError.
            cleanup_interval: Time in seconds between automatic cleanup of dead
                subscriber references. Default is 60 seconds.
            max_subscribers_before_cleanup: Maximum number of subscribers before
                triggering automatic cleanup. Default is 100.
        
        Example:
            Create publishers with different configurations::
            
                # Default configuration (sync mode)
                pub1 = Publisher()
                
                # With async as preferred mode
                pub2 = Publisher(preferred_publish_mode="async")
                
                # With logging and custom cleanup
                import logging
                logger = logging.getLogger(__name__)
                pub3 = Publisher(
                    preferred_publish_mode="direct",
                    logger=logger,
                    cleanup_interval=30.0,
                    max_subscribers_before_cleanup=50
                )
                
                # With publishing disabled by default
                pub4 = Publisher(preferred_publish_mode="off")
        """
        super().__init__()

        self._logger: Optional[Logger] = logger
        self._preferred_publish_mode: Literal["async", "sync", "direct", "off"] = preferred_publish_mode

        self._subscriber_storage: WeakReferenceStorage[Subscriber] = WeakReferenceStorage(
            cleanup_interval=cleanup_interval,
            max_references_before_cleanup=max_subscribers_before_cleanup
        )
        self._callback_storage: set[Callable[[], None]] = set()

    def add_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Add a subscriber or callback to receive publications from this publisher.
        
        This method supports two types of subscriptions:
        
        1. **Subscriber objects**: Full subscriber pattern with async reactions.
           Stored as weak references with automatic cleanup and bidirectional tracking.
           
        2. **Callback functions**: Simple callable functions for direct notifications.
           Stored as strong references.
        
        Args:
            subscriber: Either a Subscriber instance or a callable function.
                - Subscriber: Must implement `_react_to_publication(publisher, mode)`
                - Callable: Regular function with signature `() -> None`
        
        Raises:
            ValueError: If the argument is neither a Subscriber nor a Callable.
        
        Example:
            Add subscribers and callbacks::
            
                from observables._utils.publisher import Publisher
                from observables._utils.subscriber import Subscriber
                
                publisher = Publisher()
                
                # Add a Subscriber instance
                class MySubscriber(Subscriber):
                    def _react_to_publication(self, publisher, mode):
                        print(f"Subscriber reacted in {mode} mode")
                
                publisher.add_subscriber(MySubscriber())
                
                # Add a callback function
                def my_callback():
                    print("Callback executed")
                
                publisher.add_subscriber(my_callback)
                
                # Now both will receive publications
                publisher.publish()
        """

        from .subscriber import Subscriber

        if isinstance(subscriber, Subscriber):
            self._subscriber_storage.cleanup()
            subscriber._add_publisher_called_by_subscriber(self) # type: ignore
            self._subscriber_storage.add_reference(weakref.ref(subscriber))

        elif callable(subscriber):
            # It's a callback function
            self._callback_storage.add(subscriber)

        else:
            raise ValueError(f"Subscriber must be a Subscriber instance or callable, got: {type(subscriber)}")

    def remove_subscriber(self, subscriber: "Subscriber|Callable[[], None]") -> None:
        """
        Remove a subscriber so it no longer receives publications.
        
        This method removes the subscriber or callback from both the publisher's subscriber
        list and the subscriber's publisher list (bidirectional cleanup).
        
        Args:
            subscriber_or_callback: The Subscriber or Callable instance to remove.
        
        Raises:
            ValueError: If the subscriber is not currently subscribed to this
                publisher.
        
        Example:
            Remove a subscriber::
            
                publisher = Publisher()
                subscriber = MySubscriber()
                
                publisher.add_subscriber(subscriber)
                assert publisher.is_subscribed(subscriber)
                
                publisher.remove_subscriber(subscriber)
                assert not publisher.is_subscribed(subscriber)
        """

        from .subscriber import Subscriber

        if isinstance(subscriber, Subscriber):
            self._subscriber_storage.cleanup()
            subscriber_ref_to_remove = None
            for subscriber_ref in self._subscriber_storage.weak_references:
                sub = subscriber_ref()
                if sub is subscriber:
                    subscriber_ref_to_remove = subscriber_ref
                    break
            if subscriber_ref_to_remove is None:
                raise ValueError("Subscriber not found")
            self._subscriber_storage.remove_reference(subscriber_ref_to_remove)
            subscriber._remove_publisher_called_by_subscriber(self) # type: ignore

        elif isinstance(subscriber, Callable): # type: ignore
            self._callback_storage.remove(subscriber)

        else:
            raise ValueError(f"Subscriber is not a Subscriber or Callable: {subscriber}")

    def is_subscribed(self, subscriber: "Subscriber") -> bool:
        """
        Check if a subscriber is currently subscribed to this publisher.
        
        Args:
            subscriber: The Subscriber instance to check.
        
        Returns:
            True if the subscriber is subscribed, False otherwise.
        
        Example:
            Check subscription status::
            
                publisher = Publisher()
                subscriber = MySubscriber()
                
                print(publisher.is_subscribed(subscriber))  # False
                
                publisher.add_subscriber(subscriber)
                print(publisher.is_subscribed(subscriber))  # True
        """
        self._subscriber_storage.cleanup()
        for subscriber_ref in self._subscriber_storage.weak_references:
            sub = subscriber_ref()
            if sub is subscriber:
                return True

        return False

    def _handle_task_exception(self, task: asyncio.Task[None], subscriber_or_callback: "Subscriber"|Callable[[], None], raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:
        """
        Handle exceptions that occur in subscriber reaction tasks.
        
        This callback is executed when an async subscriber task completes. If the
        task raised an exception, it will be logged (if a logger is configured)
        or re-raised as a RuntimeError (if no logger is configured).
        
        Args:
            task: The completed asyncio.Task.
            subscriber: The subscriber whose reaction raised an exception.
        
        Raises:
            RuntimeError: If the task failed and no logger is configured.
        
        Note:
            This is an internal method called automatically by asyncio task
            callbacks. It ensures that subscriber errors are never silently
            ignored.
        """
        try:
            task.result()  # This will raise the exception if one occurred
        except Exception as e:

            if isinstance(subscriber_or_callback, Subscriber):
                error_msg = f"Subscriber {subscriber_or_callback} failed to react to publication: {e}"
            elif isinstance(subscriber_or_callback, Callable[[], None]): # type: ignore
                error_msg = f"Callback {subscriber_or_callback} failed to react to publication: {e}"
            else:
                error_msg = f"subscriber_or_callback is not a Subscriber or Callable: {subscriber_or_callback}"

            if raise_error_mode == "raise":
                raise e
            elif raise_error_mode == "ignore":
                pass
            elif raise_error_mode == "warn":
                warnings.warn(error_msg, stacklevel=2)
            else: 
                raise ValueError(f"Invalid raise_error_mode: {raise_error_mode}")

    def publish(self, mode: Literal["async", "sync", "direct", "off", None] = None, raise_error_mode: Literal["raise", "ignore", "warn"] = "raise") -> None:
        """
        Publish an update to all subscribed subscribers and/or callbacks.
        
        This method supports three publication modes: asynchronous (default), synchronous, 
        and direct.
        
        **Async Mode (Default) - Non-Blocking with Asyncio**
        
        In async mode (mode="async"), the method triggers the `react_to_publication` 
        method on each subscriber and **returns immediately** without waiting for 
        reactions to complete. All reactions execute asynchronously and independently 
        in the event loop - they do not block the publisher, each other, or the calling code.
        
        **Async Execution Flow:**
        
        1. Method is called (e.g., during Phase 6 of `submit_values()`)
        2. Asyncio tasks are created for each subscriber's reaction and callback
        3. Method returns immediately to caller
        4. Subscriber reactions execute in the background
        5. Each reaction completes independently
        
        This design ensures that slow subscriber reactions (network I/O, database
        operations, file writes, etc.) never block the main execution flow or
        affect the performance of value submissions.
        
        **Use Case:** Production code with I/O-bound operations, decoupled async components
        
        **Sync Mode - Blocking with Asyncio**
        
        In sync mode (mode="sync"), the method waits for each subscriber reaction
        to complete before returning. Reactions are executed sequentially using
        `loop.run_until_complete()`, blocking the calling code until all subscribers
        have finished reacting.
        
        **Sync Execution Flow:**
        
        1. Method is called
        2. For each subscriber, run their async reaction to completion
        3. Wait for reaction to finish before moving to next subscriber
        4. Method returns only after all reactions complete
        
        Sync mode is useful when you need guaranteed completion before proceeding,
        such as in testing or when reactions must complete before the next operation.
        
        **Use Case:** Testing, debugging, ensuring all async operations complete
        
        **Direct Mode - Synchronous without Asyncio**
        
        In direct mode (mode="direct"), both subscribers and callbacks are executed 
        directly as regular function calls without any asyncio machinery. This provides 
        the fastest, simplest execution path with minimal overhead - just like the 
        listener pattern.
        
        **Direct Execution Flow:**
        
        1. Method is called
        2. Each subscriber's `_react_to_publication_direct()` is called synchronously
        3. Each callback is called directly as a regular function
        4. No asyncio tasks, no event loop, no coroutines
        5. Method returns after all reactions complete
        
        **Important Requirements:**
        - Subscribers must implement `_react_to_publication()` as a regular (non-async) method
        - Only synchronous callbacks are supported (no async functions)
        - If async callback is encountered, it's skipped with error logged
        
        **Use Case:** Fast synchronous notifications, listener-like behavior, no async needed
        
        **Off Mode - Disabled Publishing**
        
        In off mode (mode="off"), the publish method returns immediately without 
        notifying any subscribers or executing any callbacks. This is useful for
        temporarily disabling notifications without removing subscribers.
        
        **Use Case:** Temporarily disable notifications, batch operations, performance optimization
        
        **None Mode - Use Preferred Mode**
        
        When mode=None (default when calling publish() without arguments), the 
        publisher uses its `preferred_publish_mode` setting (configured during initialization).
        This allows you to set a default behavior for all publish calls.
        
        **Use Case:** Consistent default behavior, easy mode switching
        
        **Cleanup**
        
        Dead subscriber references are automatically skipped in all modes (except "off").
        If cleanup thresholds are met, dead references are cleaned up before publishing.
        
        **Error Handling**
        
        - If a subscriber's reaction raises an exception and a logger is
          configured, the error is logged and other subscribers continue.
        - If no logger is configured, the error raises a RuntimeError.
        - Errors in one subscriber never affect other subscribers.
        
        **Parameters**
        
        mode : Literal["async", "sync", "direct", "off", None], default=None
            Publication mode:
            
            - None (default): Uses the `preferred_publish_mode` setting
            - "async": Non-blocking with asyncio, returns immediately, reactions run in background
            - "sync": Blocking with asyncio, waits for all reactions to complete before returning
            - "direct": Synchronous without asyncio, both subscribers and callbacks, no event loop overhead
            - "off": Disables publishing entirely, returns immediately without notifications
        
        **Important Notes**
        
        - When mode=None: uses the `preferred_publish_mode` property
        - In async mode: returns immediately, before subscriber reactions complete
        - In sync mode: blocks until all subscriber reactions complete, uses asyncio
        - In direct mode: blocks until all reactions complete, no asyncio, pure synchronous calls
        - In off mode: returns immediately without any notifications (useful for batch operations)
        - Subscriber reactions cannot influence the publisher's state (unidirectional)
        - Subscribers receive publications after values are already committed
        - Direct mode requires Subscribers to have synchronous `_react_to_publication()` methods
        - The preferred mode can be changed at runtime via the `preferred_publish_mode` property
        
        Example:
            Publishing with async reactions (default)::
            
                import asyncio
                from observables._utils.publisher import Publisher
                from observables._utils.subscriber import Subscriber
                
                class NetworkSubscriber(Subscriber):
                    async def _react_to_publication(self, publisher):
                        # This runs asynchronously without blocking
                        await send_network_request()
                        await save_to_database()
                
                publisher = Publisher(logger=logger)
                publisher.add_subscriber(NetworkSubscriber())
                
                # Publish - returns immediately
                publisher.publish()
                print("Published! (reactions happening in background)")
                
                # Continue with other work without waiting
                # Subscriber reactions complete independently
            
            Publishing with sync reactions (blocking with asyncio)::
            
                publisher = Publisher(logger=logger)
                publisher.add_subscriber(DatabaseSubscriber())
                
                # Publish and wait for all reactions to complete
                publisher.publish(mode="sync")
                print("All async reactions completed!")
                
                # Can safely assert on side effects now
                assert database_was_updated()
            
            Publishing with direct mode (synchronous subscribers and callbacks)::
            
                from observables._utils.subscriber import Subscriber
                
                publisher = Publisher(logger=logger)
                
                # Add synchronous subscriber (non-async _react_to_publication!)
                class SyncSubscriber(Subscriber):
                    def _react_to_publication(self, publisher):
                        # Regular synchronous method (not async)
                        print("Subscriber reacted immediately!")
                        update_database()
                
                publisher.add_subscriber(SyncSubscriber())
                
                # Add synchronous callback
                def on_publish():
                    print("Callback executed immediately!")
                    update_counter()
                
                publisher.add_callback(on_publish)
                
                # Publish in direct mode - no asyncio overhead
                publisher.publish(mode="direct")
                print("All reactions completed!")
                
                # No waiting needed - everything already executed
                assert database_was_updated()
                assert counter_was_updated()
            
            Publishing with off mode (disabled)::
            
                publisher = Publisher()
                subscriber = MySubscriber()
                publisher.add_subscriber(subscriber)
                
                # Temporarily disable publishing
                publisher.publish(mode="off")
                # Nothing happens - subscriber not notified
                
                # Re-enable with explicit mode
                publisher.publish(mode="direct")
                # Now subscriber is notified
            
            Using preferred_publish_mode (None)::
            
                # Set preferred mode during initialization
                publisher = Publisher(preferred_publish_mode="direct")
                
                # Publish using preferred mode
                publisher.publish()  # mode=None, uses "direct"
                
                # Change preferred mode at runtime
                publisher.preferred_publish_mode = "async"
                publisher.publish()  # Now uses "async"
                
                # Or override with explicit mode
                publisher.publish(mode="sync")  # Uses "sync" regardless of preferred
        
        Testing Note:
            - Async mode: use `await asyncio.sleep(0)` to allow reactions to complete
            - Sync mode: reactions complete before return, no waiting needed
            - Direct mode: callbacks execute immediately, no waiting needed, fastest option
            - Off mode: nothing executes, instant return
            - None mode: uses preferred_publish_mode, behavior depends on preference
        """
        # Check if we should do a full cleanup before publishing
        self._subscriber_storage.cleanup()

        if mode is None:
            mode = self.preferred_publish_mode

        match mode:
            case "async":
                for subscriber_ref in self._subscriber_storage.weak_references:
                    subscriber: Subscriber | None = subscriber_ref()
                    if subscriber is not None:
                        task: asyncio.Task[None] = subscriber.react_to_publication_task(self, "async") # type: ignore
                        task.add_done_callback(
                            lambda task, subscriber=subscriber: self._handle_task_exception(task, subscriber)
                        )
                for callback in self._callback_storage:
                    # Handle both sync and async callbacks
                    if asyncio.iscoroutinefunction(callback):
                        task = asyncio.create_task(callback())
                        task.add_done_callback(
                            lambda t, c=callback: self._handle_task_exception(t, callback, raise_error_mode)
                        )
                    else:
                        # Wrap sync callback in async task
                        async def run_sync_callback(cb: Callable[[], None]) -> None:
                            cb()
                        task = asyncio.create_task(run_sync_callback(callback))
                        task.add_done_callback(
                            lambda task, callback=callback: self._handle_task_exception(task, callback, raise_error_mode)
                        )

            case "sync":
                # Synchronous mode: wait for each subscriber reaction to complete
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No event loop in this thread, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                for subscriber_ref in self._subscriber_storage.weak_references:
                    subscriber = subscriber_ref()
                    if subscriber is not None:
                        try:
                            # Run the async reaction synchronously
                            loop.run_until_complete(subscriber._react_async_to_publication(self, "sync")) # type: ignore
                        except Exception as e:
                            if raise_error_mode == "raise":
                                raise e
                            elif raise_error_mode == "ignore":
                                pass
                            elif raise_error_mode == "warn":
                                warnings.warn(f"Subscriber {subscriber} failed to react to publication: {e}", stacklevel=2)
                
                for callback in self._callback_storage:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            loop.run_until_complete(callback())
                        else:
                            callback()
                    except Exception as e:
                        if raise_error_mode == "raise":
                            raise e
                        elif raise_error_mode == "ignore":
                            pass
                        elif raise_error_mode == "warn":
                            warnings.warn(f"Callback {callback} failed to react to publication: {e}", stacklevel=2)   
            
            case "direct":
                # Direct mode: pure synchronous execution without asyncio overhead
                # Both subscribers and callbacks execute synchronously
                
                # Execute subscribers directly (synchronous)
                for subscriber_ref in self._subscriber_storage.weak_references:
                    subscriber = subscriber_ref()
                    if subscriber is not None:
                        try:
                            # Direct synchronous call
                            subscriber._react_to_publication(self, "direct") # type: ignore
                        except Exception as e:
                            if raise_error_mode == "raise":
                                raise RuntimeError(f"Subscriber {subscriber} failed to react in direct mode: {e}") from e
                            elif raise_error_mode == "ignore":
                                pass
                            elif raise_error_mode == "warn":
                                warnings.warn(f"Subscriber {subscriber} failed to react in direct mode: {e}", stacklevel=2)
                
                # Execute callbacks directly without asyncio
                for callback in self._callback_storage:
                    try:
                        # Check if callback is async (not supported in direct mode)
                        if asyncio.iscoroutinefunction(callback):
                            error_msg = (
                                f"Direct mode does not support async callbacks. "
                                f"Callback {callback} is async. Use 'async' or 'sync' mode instead, "
                                f"or provide a synchronous callback."
                            )
                            if self._logger:
                                self._logger.error(error_msg)
                            else:
                                raise RuntimeError(error_msg)
                            continue
                        
                        # Direct synchronous call
                        callback()
                    except Exception as e:
                        error_msg = f"Callback {callback} failed in direct mode: {e}"
                        if self._logger:
                            self._logger.error(error_msg, exc_info=True)
                        else:
                            raise RuntimeError(error_msg) from e

            case "off":
                # Do nothing
                pass
                    
            case _: # type: ignore
                raise ValueError(f"Invalid mode: {mode}")

    @property
    def preferred_publish_mode(self) -> Literal["async", "sync", "direct", "off"]:
        """
        Get the preferred publish mode for this publisher.
        """
        return self._preferred_publish_mode

    @preferred_publish_mode.setter
    def preferred_publish_mode(self, mode: Literal["async", "sync", "direct", "off"]) -> None:
        """
        Set the preferred publish mode for this publisher.
        """
        self._preferred_publish_mode = mode