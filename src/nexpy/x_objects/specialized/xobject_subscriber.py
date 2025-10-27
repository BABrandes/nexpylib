"""
XSubscriber module for reactive X object integration.

This module provides the XSubscriber class, which combines the Publisher-
Subscriber pattern with the X object framework. It automatically updates its
X object values in response to publications from Publishers.

Example:
    Basic usage with a single publisher::

        from nexpy import Publisher, XSubscriber
        
        # Create a publisher
        data_source = Publisher()
        
        # Create an X object that reacts to publications
        def get_data(publisher):
            if publisher is None:
                return {"value": 0}  # Initial value
            # Fetch actual data when publisher publishes
            return fetch_current_data()
        
        x_obj = XSubscriber(
            publisher=data_source,
            on_publication_callback=get_data
        )
        
        # Now when data_source publishes, X object updates automatically
        data_source.publish()
"""

from typing import Generic, TypeVar, Callable, Mapping, Optional, Literal
from logging import Logger
from ...foundations.x_composite_base import XCompositeBase
from ...core.publisher_subscriber.publisher_protocol import PublisherProtocol
from ...core.publisher_subscriber.subscriber import Subscriber
from ...core.nexus_system.nexus_manager import NexusManager
from ...core.nexus_system.default_nexus_manager import _DEFAULT_NEXUS_MANAGER # type: ignore
from ...core.nexus_system.submission_error import SubmissionError
from nexpy.core.auxiliary.utils import make_weak_callback

HK = TypeVar("HK")
HV = TypeVar("HV")


class XSubscriber(XCompositeBase[HK, None, HV, None], Subscriber, Generic[HK, HV]):
    """
    X object that automatically updates in response to Publisher publications.
    
    XSubscriber bridges the Publisher-Subscriber pattern with the X object
    framework, creating reactive data flows where X object values automatically update
    in response to external events. It combines the async/unidirectional nature of
    pub-sub with the validation and linking capabilities of X objects.
    
    Type Parameters:
        HK: The type of keys in the X object's hook mapping. Typically str for named
            hooks like "temperature", "humidity", etc.
        HV: The type of values stored in the X object's hooks. Can be any type - int,
            float, str, list, dict, custom objects, etc.
    
    Multiple Inheritance:
        - XCompositeBase: Core X object functionality with hooks and validation
        - Subscriber: Async reaction to publisher notifications
        - Generic[HK, HV]: Type-safe key-value storage
    
    Architecture:
        1. **Subscription**: Subscribes to one or more Publishers
        2. **Publication**: When publisher publishes, `_react_to_publication` is called
        3. **Callback**: Callback function generates new values based on publication
        4. **Update**: X object updates its values via `submit_values()`
        5. **Propagation**: Linking, listeners, and subscribers are notified
    
    Use Cases:
        - React to external data sources (sensors, APIs, databases)
        - Aggregate data from multiple publishers
        - Create derived X objects from async events
        - Bridge async operations into the X object system
    
    Attributes:
        _on_publication_callback: Callback function that generates new values when
            publishers publish. Called with the publishing Publisher (or None initially).
    
    Example:
        Simple reactive X object::
        
            from nexpy import Publisher, XSubscriber
            
            # Create a data source
            temperature_sensor = Publisher()
            
            # Create X object that updates with sensor data
            def read_temperature(publisher):
                if publisher is None:
                    return {"celsius": 20.0}  # Initial value
                # Read actual temperature when published
                return {"celsius": get_sensor_reading()}
            
            temperature = XSubscriber(
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
            
            # X object reacts to any of them
            def aggregate_data(publisher):
                if publisher is None:
                    return {"count": 0}
                # Can check which publisher triggered the update
                if publisher is source1:
                    return {"count": get_count_from_source1()}
                else:
                    return {"count": get_count_from_others()}
            
            data = XSubscriber(
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
        - The X object can be bound to other X objects like any other X object
    """

    def __init__(
        self,
        publisher: PublisherProtocol|set[PublisherProtocol],
        on_publication_callback: Callable[[None|PublisherProtocol], Mapping[HK, HV]],
        *,
        custom_validator: Optional[Callable[[Mapping[HK, HV]], tuple[bool, str]]] = None,
        raise_submission_error_flag: bool = True,
        logger: Optional[Logger] = None,
        nexus_manager: NexusManager = _DEFAULT_NEXUS_MANAGER
    ) -> None:
        """
        Initialize a new XSubscriber.
        
        The X object automatically subscribes to the provided publisher(s) and updates
        its hook values whenever any of them publishes. The callback function determines
        what values should be set based on which publisher triggered the notification.
        
        Args:
            publisher: Publisher(s) to subscribe to. Can be either:
                - Single Publisher: Subscribe to one data source
                - Set[Publisher]: Subscribe to multiple sources (reacts to any of them)
                The X object will automatically call `publisher.add_subscriber(self)`.
            on_publication_callback: Function that generates X object values when
                publications occur. Signature: (publisher: None|PublisherProtocol) -> Mapping[HK, HV]
                - Called with None during initialization to get initial values
                - Called with the publishing Publisher during updates
                - Must return a mapping where keys are hook keys (type HK) and values
                  are the new values for those hooks (type HV)
                Example: lambda pub: {"temp": 20.0, "humidity": 50.0}
            logger: Optional logger for debugging. If provided, logs X object operations,
                value changes, validation errors, and hook connections. Passed to both
                the BaseXObject and Subscriber base classes. Default is None.
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
                
                x_obj = XSubscriber(
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
                
                x_obj = XSubscriber(
                    publisher={pub1, pub2, pub3},
                    on_publication_callback=get_values,
                    logger=my_logger
                )
        
        Note:
            The callback is immediately called with `None` to get initial values.
            This happens before the X object is fully initialized, so the callback
            should handle the None case appropriately.
        """

        #########################################################
        # Stuff
        #########################################################

        self._on_publication_callback = make_weak_callback(on_publication_callback)
        self._raise_submission_error_flag = raise_submission_error_flag

        if self._on_publication_callback is None:
            raise ValueError("on_publication_callback is None")
        try:
            initial_values: Mapping[HK, HV] = self._on_publication_callback(None)
        except Exception as e:
            raise ValueError(f"Error in on_publication_callback: {e}")

        #########################################################
        # Prepare and initialize base class
        #########################################################

        Subscriber.__init__(self)

        XCompositeBase.__init__( # type: ignore
            self,
            initial_hook_values=initial_values,
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={},
            validate_complete_primary_values_callback=None,
            custom_validator=custom_validator,
            invalidate_after_update_callback=None,
            logger=logger,
            nexus_manager=nexus_manager)

        #########################################################
        # Subscribe to publisher(s)
        #########################################################
        
        # Subscribe to publisher(s)
        if isinstance(publisher, PublisherProtocol):
            publisher.add_subscriber(self)
        else:
            for pub in publisher:
                pub.add_subscriber(self)

    def _react_to_publication(self, publisher: PublisherProtocol, mode: Literal["async", "sync", "direct"]) -> None:
        """
        React to a publication by updating the X object's values.
        
        This method is called asynchronously when any subscribed Publisher publishes.
        It invokes the callback function with the publisher that triggered the update,
        then submits the returned values to update the X object.
        
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
                XSubscriber._react_to_publication(publisher)
                  ↓
                values = on_publication_callback(publisher)
                  ↓
                submit_values(values)
                  ↓
                X object updates, hooks trigger, linking propagates
        
        Note:
            This is an internal method called automatically by the Subscriber
            base class. Users don't need to call it directly.
        """

        if self._on_publication_callback is not None:
            try:
                values: Mapping[HK, HV] = self._on_publication_callback(publisher)
            except Exception as e:
                raise ValueError(f"Error in on_publication_callback: {e}")
            success, msg = self._submit_values(values) # type: ignore
            if not success and self._raise_submission_error_flag:
                raise SubmissionError(msg, values)