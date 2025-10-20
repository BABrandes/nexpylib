"""
ObservableSubscriber module for reactive observable integration.

This module provides the ObservableSubscriber class, which combines the Publisher-
Subscriber pattern with the Observable framework. It automatically updates its
observable values in response to publications from Publishers.

Example:
    Basic usage with a single publisher::

        from observables import Publisher, ObservableSubscriber
        
        # Create a publisher
        data_source = Publisher()
        
        # Create an observable that reacts to publications
        def get_data(publisher):
            if publisher is None:
                return {"value": 0}  # Initial value
            # Fetch actual data when publisher publishes
            return fetch_current_data()
        
        observable = ObservableSubscriber(
            publisher=data_source,
            on_publication_callback=get_data
        )
        
        # Now when data_source publishes, observable updates automatically
        data_source.publish()
"""

from typing import Generic, TypeVar, Callable, Mapping, Optional, Literal
from logging import Logger

from ...x_objects_base.x_complex_base import ComplexObservableBase
from ...core.publisher_subscriber.publisher import Publisher
from ...core.publisher_subscriber.subscriber import Subscriber
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

HK = TypeVar("HK")
HV = TypeVar("HV")


class XSubscriber(ComplexObservableBase[HK, None, HV, None, "XSubscriber"], Subscriber, Generic[HK, HV]):
    """
    Observable that automatically updates in response to Publisher publications.
    
    ObservableSubscriber bridges the Publisher-Subscriber pattern with the Observable
    framework, creating reactive data flows where observable values automatically update
    in response to external events. It combines the async/unidirectional nature of
    pub-sub with the validation and linking capabilities of observables.
    
    Type Parameters:
        HK: The type of keys in the observable's hook mapping. Typically str for named
            hooks like "temperature", "humidity", etc.
        HV: The type of values stored in the observable's hooks. Can be any type - int,
            float, str, list, dict, custom objects, etc.
    
    Multiple Inheritance:
        - BaseObservable: Core observable functionality with hooks and validation
        - Subscriber: Async reaction to publisher notifications
        - Generic[HK, HV]: Type-safe key-value storage
    
    Architecture:
        1. **Subscription**: Subscribes to one or more Publishers
        2. **Publication**: When publisher publishes, `_react_to_publication` is called
        3. **Callback**: Callback function generates new values based on publication
        4. **Update**: Observable updates its values via `submit_values()`
        5. **Propagation**: Linking, listeners, and subscribers are notified
    
    Use Cases:
        - React to external data sources (sensors, APIs, databases)
        - Aggregate data from multiple publishers
        - Create derived observables from async events
        - Bridge async operations into the observable system
    
    Attributes:
        _on_publication_callback: Callback function that generates new values when
            publishers publish. Called with the publishing Publisher (or None initially).
    
    Example:
        Simple reactive observable::
        
            from observables import Publisher, ObservableSubscriber
            
            # Create a data source
            temperature_sensor = Publisher()
            
            # Create observable that updates with sensor data
            def read_temperature(publisher):
                if publisher is None:
                    return {"celsius": 20.0}  # Initial value
                # Read actual temperature when published
                return {"celsius": get_sensor_reading()}
            
            temperature = ObservableSubscriber(
                publisher=temperature_sensor,
                on_publication_callback=read_temperature
            )
            
            # Access current temperature
            print(temperature["celsius"])  # 20.0
            
            # Sensor publishes update
            temperature_sensor.publish()
            print(temperature["celsius"])  # Updated value
        
        Multiple publishers::
        
            # Create multiple data sources
            source1 = Publisher()
            source2 = Publisher()
            source3 = Publisher()
            
            # Observable reacts to any of them
            def aggregate_data(publisher):
                if publisher is None:
                    return {"count": 0}
                # Can check which publisher triggered the update
                if publisher is source1:
                    return {"count": get_count_from_source1()}
                else:
                    return {"count": get_count_from_others()}
            
            data = ObservableSubscriber(
                publisher={source1, source2, source3},
                on_publication_callback=aggregate_data
            )
            
            # Any publisher can trigger an update
            source1.publish()  # Updates data
            source2.publish()  # Also updates data
    
    Note:
        - The callback is called with `None` during initialization to get initial values
        - The callback is called with the publishing Publisher during updates
        - All updates happen asynchronously
        - The observable can be bound to other observables like any other observable
    """

    def __init__(
        self,
        publisher: Publisher|set[Publisher],
        on_publication_callback: Callable[[None|Publisher], Mapping[HK, HV]],
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
    ) -> None:
        """
        Initialize a new ObservableSubscriber.
        
        The observable automatically subscribes to the provided publisher(s) and updates
        its hook values whenever any of them publishes. The callback function determines
        what values should be set based on which publisher triggered the notification.
        
        Args:
            publisher: Publisher(s) to subscribe to. Can be either:
                - Single Publisher: Subscribe to one data source
                - Set[Publisher]: Subscribe to multiple sources (reacts to any of them)
                The observable will automatically call `publisher.add_subscriber(self)`.
            on_publication_callback: Function that generates observable values when
                publications occur. Signature: (publisher: None|Publisher) -> Mapping[HK, HV]
                - Called with None during initialization to get initial values
                - Called with the publishing Publisher during updates
                - Must return a mapping where keys are hook keys (type HK) and values
                  are the new values for those hooks (type HV)
                Example: lambda pub: {"temp": 20.0, "humidity": 50.0}
            logger: Optional logger for debugging. If provided, logs observable operations,
                value changes, validation errors, and hook connections. Passed to both
                the BaseObservable and Subscriber base classes. Default is None.
            nexus_manager: The NexusManager that coordinates value updates and validation.
                Uses the global DEFAULT_NEXUS_MANAGER by default, which is shared across
                the entire application. Custom managers can be used for isolated systems.
                Default is DEFAULT_NEXUS_MANAGER.
        
        Example:
            With a single publisher::
            
                def get_values(pub):
                    if pub is None:
                        return {"x": 0, "y": 0}
                    return {"x": current_x(), "y": current_y()}
                
                observable = ObservableSubscriber(
                    publisher=my_publisher,
                    on_publication_callback=get_values
                )
            
            With multiple publishers::
            
                def get_values(pub):
                    if pub is None:
                        return {"status": "idle"}
                    # Different behavior based on which publisher triggered
                    if pub is pub1:
                        return {"status": "active"}
                    else:
                        return {"status": "processing"}
                
                observable = ObservableSubscriber(
                    publisher={pub1, pub2, pub3},
                    on_publication_callback=get_values,
                    logger=my_logger
                )
        
        Note:
            The callback is immediately called with `None` to get initial values.
            This happens before the observable is fully initialized, so the callback
            should handle the None case appropriately.
        """

        self._on_publication_callback = on_publication_callback

        initial_values: Mapping[HK, HV] = self._on_publication_callback(None)
        
        Subscriber.__init__(self)
        ComplexObservableBase.__init__( # type: ignore
            self,
            initial_hook_values=initial_values,
            verification_method=None,
            secondary_hook_callbacks={},
            add_values_to_be_updated_callback=None,
            invalidate_callback=None,
            logger=logger,
            nexus_manager=nexus_manager)
        
        # Subscribe to publisher(s)
        if isinstance(publisher, Publisher):
            publisher.add_subscriber(self)
        else:
            for pub in publisher:
                pub.add_subscriber(self)

    def _react_to_publication(self, publisher: Publisher, mode: Literal["async", "sync", "direct"]) -> None:
        """
        React to a publication by updating the observable's values.
        
        This method is called asynchronously when any subscribed Publisher publishes.
        It invokes the callback function with the publisher that triggered the update,
        then submits the returned values to update the observable.
        
        Args:
            publisher: The Publisher that triggered this update.
            mode: The mode of publication.
        
        Raises:
            Any exception raised by the callback function or submit_values will
            propagate and be handled by the Publisher's error handling mechanism.
        
        Example:
            The flow when a publisher publishes::
            
                publisher.publish()
                  ↓
                ObservableSubscriber._react_to_publication(publisher)
                  ↓
                values = on_publication_callback(publisher)
                  ↓
                submit_values(values)
                  ↓
                Observable updates, hooks trigger, linking propagates
        
        Note:
            This is an internal method called automatically by the Subscriber
            base class. Users don't need to call it directly.
        """
        values: Mapping[HK, HV] = self._on_publication_callback(publisher)
        self.submit_values_by_keys(values) # type: ignore