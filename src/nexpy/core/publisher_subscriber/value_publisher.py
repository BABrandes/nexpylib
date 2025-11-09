"""
ValuePublisher module for value-based publish-subscribe pattern.

This module provides the ValuePublisher class, which extends Publisher to hold
a value and automatically publish updates whenever the value changes. This is
particularly useful for unidirectional data synchronization patterns.

Example:
    Basic value publishing::

        from observables._utils.value_publisher import ValuePublisher
        
        # Create a publisher with initial value
        counter = ValuePublisher(0)
        
        # Value changes trigger automatic publication
        counter.value = 1  # Automatically publishes to subscribers
        counter.value = 2  # Publishes again
    
    Unidirectional sync with ObservableSubscriber::
    
        from observables import ValuePublisher, ObservableSubscriber
        
        # Source of truth
        source = ValuePublisher({"status": "idle", "count": 0})
        
        # Reactive observable that stays in sync
        def sync_values(publisher):
            if publisher is None:
                return source.value  # Initial sync
            # Get updated value from the publisher
            return publisher.value
        
        observable = ObservableSubscriber(
            publisher=source,
            on_publication_callback=sync_values
        )
        
        # Now changes to source automatically sync to observable
        source.value = {"status": "active", "count": 5}
        # observable automatically receives the new value
"""

from typing import Generic, Literal, TypeVar, Optional
from logging import Logger

from ..auxiliary.listenable_mixin import ListenableMixin
from ..auxiliary.listenable_protocol import ListenableProtocol
from .publisher_mixin import PublisherMixin
from .publisher_protocol import PublisherProtocol

T = TypeVar("T")

class ValuePublisher(PublisherMixin, PublisherProtocol, ListenableMixin, ListenableProtocol, Generic[T]):
    """
    A Publisher that holds a value and publishes automatically on value changes.
    
    ValuePublisher extends the basic Publisher with value storage and automatic
    publication when the value is updated via the setter. This makes it ideal for
    creating unidirectional data flows where changes to a source value should
    automatically propagate to subscribers.
    
    The combination of ValuePublisher with ObservableSubscriber creates a powerful
    unidirectional sync pattern: changes to the ValuePublisher's value automatically
    trigger updates to subscribed ObservableSubscribers, which can then access the
    new value through the publisher parameter in their callback.
    
    Type Parameters:
        T: The type of value this publisher holds.
    
    Attributes:
        _value (T): The current value held by this publisher.
        All PublisherMixin and ListeningMixin attributes are also available.
    
    Example:
        Simple value publishing::
        
            from observables._utils.value_publisher import ValuePublisher
            
            # Create with initial value
            temperature = ValuePublisher(20.0)
            
            # Access current value
            print(temperature.value)  # 20.0
            
            # Update value (triggers automatic publication)
            temperature.value = 25.0  # Publishes to all subscribers
        
        Unidirectional sync pattern::
        
            from observables import ValuePublisher, ObservableSubscriber
            
            # Source: ValuePublisher holds the authoritative state
            user_data = ValuePublisher({
                "name": "Alice",
                "age": 30,
                "status": "active"
            })
            
            # Sink: ObservableSubscriber stays in sync with the source
            def get_user_data(publisher):
                if publisher is None:
                    # Initial value from source
                    return user_data.value
                # When source publishes, get its current value
                # The publisher parameter IS the ValuePublisher
                return publisher.value
            
            user_observable = ObservableSubscriber(
                publisher=user_data,
                on_publication_callback=get_user_data
            )
            
            # Now they're synchronized unidirectionally:
            # user_data → (change) → publish → user_observable updates
            
            user_data.value = {
                "name": "Alice",
                "age": 31,  # Birthday!
                "status": "active"
            }
            # user_observable automatically has the new value
        
        Multiple subscribers (one-to-many sync)::
        
            from observables import ValuePublisher, ObservableSubscriber
            
            # Single source
            config = ValuePublisher({"theme": "light", "lang": "en"})
            
            # Multiple observers stay in sync
            def sync_config(pub):
                return pub.value if pub else config.value
            
            ui_config = ObservableSubscriber(config, sync_config)
            backend_config = ObservableSubscriber(config, sync_config)
            cache_config = ObservableSubscriber(config, sync_config)
            
            # One change updates all three
            config.value = {"theme": "dark", "lang": "en"}
            # ui_config, backend_config, and cache_config all updated!
    
    Note:
        - Setting the value property automatically calls publish()
        - The value is stored by reference; mutable values should be copied
          if you want to prevent external modifications
        - For complex sync logic, use a custom callback in ObservableSubscriber
        - This is unidirectional: changes to subscribers don't affect the source
    """

    def __init__(
        self,
        value: T,
        preferred_publish_mode: Literal["async", "sync", "direct", "off"],
        logger: Optional[Logger] = None,
        cleanup_interval: float = 60.0,
        max_subscribers_before_cleanup: int = 100
    ):
        """
        Initialize a new ValuePublisher with an initial value.
        
        Args:
            value: The initial value to be held and published by this publisher.
                This value will be accessible via the `value` property and will
                be available to subscribers when they react to publications.
        
        Example:
            Create publishers with different value types::
            
                # Simple types
                counter = ValuePublisher(0)
                message = ValuePublisher("Hello")
                flag = ValuePublisher(True)
                
                # Complex types
                config = ValuePublisher({"key": "value"})
                data_list = ValuePublisher([1, 2, 3])
                
                # Custom objects
                user = ValuePublisher(User(name="Alice"))
        """
        ListenableMixin.__init__(self)
        PublisherMixin.__init__(
            self,
            preferred_publish_mode=preferred_publish_mode,
            logger=logger,
            cleanup_interval=cleanup_interval,
            max_subscribers_before_cleanup=max_subscribers_before_cleanup
        )
        self._value = value
        self.publish()

    @property
    def value(self) -> T:
        """
        Get the current value held by this publisher.
        
        Returns:
            The current value of type T.
        
        Example:
            Access the current value::
            
                publisher = ValuePublisher(42)
                current = publisher.value  # 42
                
                # In ObservableSubscriber callback
                def get_value(pub):
                    if pub is None:
                        return {"data": 0}
                    # pub is the ValuePublisher - access its value
                    return {"data": pub.value}
        """
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """
        Set a new value and automatically publish to all subscribers.
        
        Setting this property does two things:
        1. Updates the internal _value
        2. Calls publish() to notify all subscribers
        
        This automatic publication is what makes ValuePublisher ideal for
        unidirectional sync patterns - you just update the value and subscribers
        automatically receive the update.
        
        Args:
            value: The new value to store and publish.
        
        Example:
            Update value and trigger publication::
            
                # Create publisher
                status = ValuePublisher("idle")
                
                # Create subscriber
                def sync_status(pub):
                    return {"status": pub.value if pub else "idle"}
                
                observable = ObservableSubscriber(status, sync_status)
                
                # Update - automatically publishes and syncs
                status.value = "active"  # observable receives update
                status.value = "processing"  # observable receives update
                status.value = "complete"  # observable receives update
            
            Unidirectional data flow::
            
                # Source → ValuePublisher → Subscribers
                #
                # Changes flow in one direction only:
                # 1. Update source.value
                # 2. Automatic publish()
                # 3. Subscribers react with publisher.value
                
                source = ValuePublisher({"counter": 0})
                
                def sync(pub):
                    return pub.value if pub else source.value
                
                obs1 = ObservableSubscriber(source, sync)
                obs2 = ObservableSubscriber(source, sync)
                
                # One change updates all subscribers
                source.value = {"counter": 1}
        """
        self._value = value
        self.publish()

    def change_value(self, value: T) -> None:
        """
        Change the value and publish to subscribers (method-style alternative to property setter).
        
        This method provides a method-style interface for changing the value, which
        can be more convenient in certain programming contexts (e.g., callbacks,
        method references). It is functionally equivalent to setting the `value`
        property directly.
        
        Args:
            value: The new value to store and publish.
        
        Example:
            Using change_value() instead of property setter::
            
                publisher = ValuePublisher(0)
                
                # These are equivalent:
                publisher.value = 1       # Property setter
                publisher.change_value(1) # Method call
                
                # Both trigger automatic publication to subscribers
            
            Useful for callbacks and method references::
            
                publisher = ValuePublisher("idle")
                
                # Can pass as a callback directly
                button.on_click(lambda: publisher.change_value("active"))
                
                # Or with partial application
                from functools import partial
                set_processing = partial(publisher.change_value, "processing")
                set_processing()  # Changes to "processing" and publishes
            
            In unidirectional sync patterns::
            
                source = ValuePublisher({"count": 0})
                
                def sync(pub):
                    return pub.value if pub else source.value
                
                observable = ObservableSubscriber(source, sync)
                
                # Use change_value for explicit method calls
                def increment():
                    current = source.value
                    source.change_value({"count": current["count"] + 1})
                
                increment()  # Updates source and syncs to observable
        
        Note:
            - This method internally uses the value setter, which already calls publish()
            - The extra publish() call is redundant but harmless (idempotent)
            - Use whichever style (property or method) fits your code better
        """
        self.value = value
        self.publish()