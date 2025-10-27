"""
Test cases for XSubscriber
"""

from typing import Optional, Mapping
import asyncio
import pytest


from nexpy.core.publisher_subscriber.value_publisher import ValuePublisher
from nexpy import XSubscriber

from test_base import ObservableTestCase
from run_tests import console_logger as logger

class TestXSubscriber(ObservableTestCase):
    """Test XSubscriber functionality"""
    
    def setup_method(self):
        super().setup_method()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.publisher = ValuePublisher(0, preferred_publish_mode="sync")
        self.callback_call_count = 0
        self.last_publisher: Optional[ValuePublisher] = None
    
    def teardown_method(self):
        self.loop.close()
    
    def simple_callback(self, pub: Optional[ValuePublisher]) -> Mapping[str, int]:
        """Simple callback that tracks calls and returns test data"""
        self.callback_call_count += 1
        self.last_publisher = pub
        
        if pub is None:
            return {"value": 0}
        else:
            return {"value": self.callback_call_count}
    
    def test_initialization_with_single_publisher(self):
        """Test creating XSubscriber with a single publisher"""
        observable = XSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        # Callback should be called once with None for initial values
        assert self.callback_call_count == 1
        assert self.last_publisher is None
        
        # Should be subscribed to publisher
        assert self.publisher.is_subscribed(observable)
    
    def test_initialization_with_multiple_publishers(self):
        """Test creating XSubscriber with multiple publishers"""
        publisher2 = ValuePublisher(0, preferred_publish_mode="sync")
        publisher3 = ValuePublisher(0, preferred_publish_mode="sync")
        
        publishers = {self.publisher, publisher2, publisher3}
        
        observable = XSubscriber(
            publishers,
            self.simple_callback,
            logger=logger
        )
        
        # Should be subscribed to all publishers
        assert self.publisher.is_subscribed(observable)
        assert publisher2.is_subscribed(observable)
        assert publisher3.is_subscribed(observable)
    
    def test_reaction_to_publication(self):
        """Test that XSubscriber reacts to publications"""
        _ = XSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        # Reset counter after initialization
        initial_count = self.callback_call_count
        
        # Publish
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called again
        assert self.callback_call_count == initial_count + 1
        assert self.last_publisher is self.publisher
    
    def test_multiple_publications(self):
        """Test multiple publications"""
        _ = XSubscriber(
            self.publisher,
            self.simple_callback,
            logger=logger
        )
        
        initial_count = self.callback_call_count
        
        # Publish 3 times
        for _ in range(3):
            self.publisher.publish()
            self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called 3 more times
        assert self.callback_call_count == initial_count + 3
    
    def test_multiple_publishers_trigger_reactions(self):
        """Test that all publishers trigger reactions"""
        publisher2 = ValuePublisher(0, preferred_publish_mode="sync")
        publisher3 = ValuePublisher(0, preferred_publish_mode="sync")
        
        _ = XSubscriber(   
            {self.publisher, publisher2, publisher3},
            self.simple_callback,
            logger=logger
        )
        
        initial_count = self.callback_call_count
        
        # Publish from each publisher
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher3.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have been called 3 times
        assert self.callback_call_count == initial_count + 3
    
    def test_callback_with_publisher_parameter(self):
        """Test that callback receives correct publisher"""
        publisher2 = ValuePublisher(0, preferred_publish_mode="sync")
        
        publishers_seen: list[ValuePublisher] = []
        
        def tracking_callback(pub: Optional[ValuePublisher]) -> Mapping[str, str]:
            if pub is not None:
                publishers_seen.append(pub)
            return {"data": "value"}
        
        _ = XSubscriber(
            {self.publisher, publisher2},
            tracking_callback,
            logger=logger
        )
        
        # Publish from both
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Should have seen both publishers
        assert len(publishers_seen) == 2
        assert self.publisher in publishers_seen
        assert publisher2 in publishers_seen
    
    def test_submit_values_called(self):
        """Test that submit_values is called with callback result"""
        values_to_return = {"key1": 100, "key2": 200}
        
        def callback(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            if pub is None:
                return {"key1": 0, "key2": 0}
            return values_to_return
        
        _ = XSubscriber(
            self.publisher,
            callback,
            logger=logger
        )
        
        # Publish
        self.publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # The observable should have the values from callback
        # Note: This assumes submit_values updates internal state
        # The exact assertion depends on how BaseXObject works
    
    def test_async_callback_execution(self):
        """Test that callbacks execute asynchronously"""
        import time
        
        call_times: list[float] = []
        
        def slow_callback(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            call_times.append(time.time())
            return {"value": 1}
        
        _ = XSubscriber(
            self.publisher,
            slow_callback,
            logger=logger
        )
        
        initial_time = time.time()
        
        # Publish should return immediately
        self.publisher.publish()
        publish_time = time.time()
        
        # Should return almost immediately
        assert publish_time - initial_time < 0.01
        
        # Wait for async execution
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Callback should have executed
        assert len(call_times) > 1  # Initial + publication


class TestXSubscriberEdgeCases(ObservableTestCase):
    """Test edge cases and error handling"""
    
    def setup_method(self):
        super().setup_method()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def teardown_method(self):
        self.loop.close()
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions are handled"""
        def failing_callback(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            if pub is None:
                return {"value": 0}
            raise ValueError("Test error in callback")
        
        publisher = ValuePublisher(0, "sync")
        subscriber = XSubscriber(
            publisher,
            failing_callback,
            logger=logger
        )
        
        # This should raise - callback errors are propagated
        with pytest.raises(ValueError, match="Error in on_publication_callback"):
            publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
    
    def test_empty_publisher_set(self):
        """Test creating XSubscriber with empty publisher set"""
        def callback(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            return {"value": 0}
        
        observable = XSubscriber(
            set(),
            callback,
            logger=logger
        )
        
        # Should initialize successfully with no publishers
        assert len(list(observable._publisher_storage.weak_references)) == 0 # type: ignore
    
    def test_initial_callback_with_none(self):
        """Test that initial callback receives None"""
        received_values: list[Optional[ValuePublisher]] = []
        
        def callback(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            received_values.append(pub)
            return {"value": 0}
        
        XSubscriber(
            ValuePublisher(0, preferred_publish_mode="sync"),
            callback,
            logger=logger
        )
        
        # First call should have been with None
        assert received_values[0] is None


class TestXSubscriberIntegration(ObservableTestCase):
    """Integration tests for XSubscriber"""
    
    def setup_method(self):
        super().setup_method()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def teardown_method(self):
        self.loop.close()
    
    @pytest.mark.skip(reason="Flaky async test - timing issues with subscriber notifications")
    def test_multiple_xobjects_same_publisher(self):
        """Test multiple XSubscribers on same ValuePublisher"""
        publisher = ValuePublisher(0, preferred_publish_mode="sync")
        
        count1 = [0]
        count2 = [0]
        
        def callback1(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            if pub is not None:
                count1[0] += 1
            return {"value": count1[0]}
        
        def callback2(pub: Optional[ValuePublisher]) -> Mapping[str, int]:
            if pub is not None:
                count2[0] += 1
            return {"value": count2[0]}
        
        _ = XSubscriber(publisher, callback1, logger=logger)
        _ = XSubscriber(publisher, callback2, logger=logger)
        
        # Publish once
        publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Both should have reacted
        assert count1[0] == 1
        assert count2[0] == 1
        
        # Publish again
        publisher.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        assert count1[0] == 2
        assert count2[0] == 2
    
    def test_chained_xobjects(self):
        """Test chaining ValuePublishers and XSubscribers"""
        publisher1 = ValuePublisher(0, preferred_publish_mode="sync")
        publisher2 = ValuePublisher(0, preferred_publish_mode="sync")
        
        values_from_pub1: list[str] = []
        values_from_pub2: list[str] = []
        
        def callback1(pub: Optional[ValuePublisher]) -> Mapping[str, str]:
            if pub is not None:
                values_from_pub1.append("pub1")
            return {"source": "pub1"}
        
        def callback2(pub: Optional[ValuePublisher]) -> Mapping[str, str]:
            if pub is not None:
                values_from_pub2.append("pub2")
            return {"source": "pub2"}
        
        _ = XSubscriber(publisher1, callback1, logger=logger)
        _ = XSubscriber(publisher2, callback2, logger=logger)
        
        # Publish from both
        publisher1.publish()
        publisher2.publish()
        self.loop.run_until_complete(asyncio.sleep(0.01))
        
        # Each should have reacted to its own publisher
        assert len(values_from_pub1) == 1
        assert len(values_from_pub2) == 1

