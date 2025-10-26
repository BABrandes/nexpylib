"""
Tests for Publisher publish modes: async, sync, and direct.

This module tests the three different publication modes available in the Publisher class:
- async: Non-blocking, creates asyncio tasks
- sync: Blocking, waits for asyncio tasks to complete
- direct: Synchronous, no asyncio, callbacks only
"""

from typing import Literal, Any
from logging import basicConfig, getLogger, DEBUG

import asyncio

from nexpy.core.publisher_subscriber.value_publisher import ValuePublisher as Publisher
from nexpy.core import Subscriber
import pytest

basicConfig(level=DEBUG)
logger = getLogger(__name__)


class TestPublishModes:
    """Test all three publish modes: async, sync, and direct."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = logger
    
    def test_direct_mode_with_sync_callback(self):
        """Test direct mode with synchronous callbacks."""
        publisher = Publisher(0, "sync")
        results: list[str] = []
        
        def sync_callback():
            results.append("executed")
        
        publisher.add_subscriber(sync_callback)
        
        # Direct mode should execute callback immediately
        publisher.publish(mode="direct")
        
        assert len(results) == 1, "Callback should execute immediately in direct mode"
        assert results[0] == "executed"
    
    def test_direct_mode_with_multiple_callbacks(self):
        """Test direct mode with multiple synchronous callbacks."""
        publisher = Publisher(0, "sync")
        results: list[int] = []
        
        def callback1():
            results.append(1)
        
        def callback2():
            results.append(2)
        
        def callback3():
            results.append(3)
        
        publisher.add_subscriber(callback1)
        publisher.add_subscriber(callback2)
        publisher.add_subscriber(callback3)
        
        # All callbacks should execute (order not guaranteed - set storage)
        publisher.publish(mode="direct")
        
        assert len(results) == 3
        assert set(results) == {1, 2, 3}
    
    def test_direct_mode_skips_async_callbacks(self):
        """Test that direct mode skips async callbacks with error."""
        publisher = Publisher(0, "sync", logger=self.logger)
        results: list[str] = []
        
        async def async_callback() -> None:
            results.append("async")
        
        publisher.add_subscriber(async_callback) # type: ignore
        
        # Direct mode should skip async callback
        publisher.publish(mode="direct")
        
        # Async callback should not have executed
        assert len(results) == 0, "Async callback should be skipped in direct mode"
    
    def test_direct_mode_mixed_callbacks(self):
        """Test direct mode with mix of sync and async callbacks."""
        publisher = Publisher(0, "sync", logger=self.logger)
        results: list[str] = []
        
        def sync_callback1():
            results.append("sync1")
        
        async def async_callback() -> None:
            results.append("async")
        
        def sync_callback2():
            results.append("sync2")
        
        publisher.add_subscriber(sync_callback1)
        publisher.add_subscriber(async_callback) # type: ignore
        publisher.add_subscriber(sync_callback2)
        
        # Only sync callbacks should execute
        publisher.publish(mode="direct")
        
        assert len(results) == 2
        assert "sync1" in results
        assert "sync2" in results
        assert "async" not in results
    
    def test_direct_mode_with_sync_subscriber(self):
        """Test that direct mode works with synchronous subscribers."""
        publisher = Publisher(0, "sync", logger=self.logger)
        results: list[str] = []
        
        class SyncSubscriber(Subscriber):
            def _react_to_publication(self, publisher: Publisher[Any], mode: Literal["async", "sync", "direct"]) -> None:
                # Synchronous method (not async)
                results.append(f"subscriber_reacted_{mode}")
        
        subscriber = SyncSubscriber()
        publisher.add_subscriber(subscriber)
        
        # Should execute subscriber synchronously
        publisher.publish(mode="direct")
        
        assert len(results) == 1
        assert results[0] == "subscriber_reacted_direct"
    
    def test_direct_mode_callback_error_handling(self):
        """Test error handling in direct mode callbacks."""
        publisher = Publisher(0, "sync")
        results: list[str] = []
        
        def callback_that_fails():
            results.append("before_error")
            raise ValueError("Test error")
        
        publisher.add_subscriber(callback_that_fails)
        
        # Should raise the error since no logger
        with pytest.raises(RuntimeError):
            publisher.publish(mode="direct")
        
        # Callback should have executed before raising
        assert len(results) == 1
        assert results[0] == "before_error"
    
    def test_direct_mode_callback_error_with_logger(self):
        """Test error handling with logger doesn't stop other callbacks."""
        publisher = Publisher(0, "sync", logger=self.logger)
        results: list[str] = []
        
        def callback_that_fails():
            results.append("before_error")
            raise ValueError("Test error")
        
        def callback_after_error():
            results.append("after_error")
        
        publisher.add_subscriber(callback_that_fails)
        publisher.add_subscriber(callback_after_error)
        
        # With logger, should not raise
        publisher.publish(mode="direct")
        
        # Both callbacks should have been attempted
        assert len(results) == 2
    
    def test_sync_mode_with_sync_callback(self):
        """Test sync mode with synchronous callbacks."""
        publisher = Publisher(0, "sync")
        results: list[str] = []
        
        def sync_callback() -> None:
            results.append("executed")
        
        publisher.add_subscriber(sync_callback)
        
        # Sync mode should execute and wait for completion
        publisher.publish(mode="sync")
        
        assert len(results) == 1
    
    def test_async_mode_comparison(self):
        """Test that async mode returns before callback completes."""
        async def test():
            publisher = Publisher(0, "sync")
            results: list[int | str] = []
            
            def callback() -> None:
                results.append("executed")
            
            publisher.add_subscriber(callback)
            
            # Async mode should return immediately
            publisher.publish(mode="async")
            
            # Callback hasn't executed yet
            assert len(results) == 0, "Async mode should return before callback"
            
            # Wait for task to complete
            await asyncio.sleep(0.01)
            
            # Now callback should have executed
            assert len(results) == 1, "Callback should execute eventually"
        
        asyncio.run(test())
    
    def test_mode_comparison_all_three(self):
        """Compare behavior of all three modes."""
        async def test():
            # Async mode
            publisher_async = Publisher(0, "sync")
            results_async: list[int] = []
            
            def callback_async():
                results_async.append(1)
            
            publisher_async.add_subscriber(callback_async)
            publisher_async.publish(mode="async")
            assert len(results_async) == 0, "Async: immediate return"
            await asyncio.sleep(0.01)
            assert len(results_async) == 1, "Async: eventually completes"
            
            # Sync mode
            publisher_sync = Publisher(0, "sync")
            results_sync: list[int] = []
            
            def callback_sync():
                results_sync.append(1)
            
            publisher_sync.add_subscriber(callback_sync)
            publisher_sync.publish(mode="sync")
            assert len(results_sync) == 1, "Sync: waits for completion"
            
            # Direct mode
            publisher_direct = Publisher(0, "sync")
            results_direct: list[int] = []
            
            def callback_direct():
                results_direct.append(1)
            
            publisher_direct.add_subscriber(callback_direct)
            publisher_direct.publish(mode="direct")
            assert len(results_direct) == 1, "Direct: immediate execution"
        
        asyncio.run(test())
    
    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        publisher = Publisher(0, "sync")
        
        with pytest.raises(ValueError):
            publisher.publish(mode="invalid")  # type: ignore
    
    def test_off_mode_disables_publishing(self):
        """Test that off mode disables all notifications."""
        publisher = Publisher(0, "sync")
        results: list[str] = []
        
        def callback():
            results.append("executed")
        
        class TestSubscriber(Subscriber):
            def _react_to_publication(self, publisher: Publisher[Any], mode: Literal["async", "sync", "direct"]) -> None:
                results.append("subscriber")
        
        publisher.add_subscriber(callback)
        publisher.add_subscriber(TestSubscriber())
        
        # Off mode should not execute anything
        publisher.publish(mode="off")
        
        assert len(results) == 0, "Off mode should not notify anyone"
    
    def test_none_mode_uses_preferred(self):
        """Test that None mode uses preferred_publish_mode."""
        # Test with async preferred
        publisher_async = Publisher(0, "async")
        assert publisher_async.preferred_publish_mode == "async"
        
        # Test with sync preferred
        publisher_sync = Publisher(0, "sync")
        assert publisher_sync.preferred_publish_mode == "sync"
        
        # Test with direct preferred
        publisher_direct = Publisher(0, "direct")
        results: list[str] = []
        
        def callback():
            results.append("direct")
        
        publisher_direct.add_subscriber(callback)
        
        # mode=None should use preferred (direct)
        publisher_direct.publish(mode=None)
        assert len(results) == 1
        
        # mode=None is also the default
        publisher_direct.publish()
        assert len(results) == 2
    
    def test_preferred_mode_change_at_runtime(self):
        """Test changing preferred_publish_mode at runtime."""
        publisher = Publisher(0, "off")
        results: list[str] = []
        
        def callback():
            results.append("executed")
        
        publisher.add_subscriber(callback)
        
        # Initially off
        publisher.publish()  # Uses preferred (off)
        assert len(results) == 0
        
        # Change to direct
        publisher.preferred_publish_mode = "direct"
        publisher.publish()  # Now uses direct
        assert len(results) == 1
        
        # Override with explicit mode (ignores preferred)
        publisher.preferred_publish_mode = "off"
        publisher.publish(mode="direct")  # Explicit mode overrides
        assert len(results) == 2
    
    def test_direct_mode_no_asyncio_needed(self):
        """Test that direct mode works without event loop."""
        # This test runs in regular unittest context (no event loop)
        publisher = Publisher(0, "sync")
        results: list[str] = []
        
        def callback():
            results.append("no_event_loop_needed")
        
        publisher.add_subscriber(callback)
        
        # Should work fine without event loop
        publisher.publish(mode="direct")
        
        assert len(results) == 1
        assert results[0] == "no_event_loop_needed"
    
    def test_direct_mode_performance_no_overhead(self):
        """Test that direct mode has minimal overhead."""
        publisher = Publisher(0, "sync")
        call_count: list[int] = [0]
        
        def fast_callback():
            call_count[0] += 1
        
        publisher.add_subscriber(fast_callback)
        
        # Should be very fast (no asyncio overhead)
        import time
        start = time.perf_counter()
        for _ in range(1000):
            publisher.publish(mode="direct")
        elapsed = time.perf_counter() - start
        
        assert call_count[0] == 1000
        # Should complete very quickly (under 0.1 seconds for 1000 calls)
        assert elapsed < 0.1, f"Direct mode took {elapsed}s for 1000 calls"


class TestPublishModesWithSubscribers:
    """Test publish modes with Subscriber objects."""
    
    def test_async_mode_with_subscriber(self):
        """Test async mode properly handles subscribers."""
        async def test():
            publisher = Publisher(0, "sync")
            reactions: list[str] = []
            
            class TestSubscriber(Subscriber):
                def _react_to_publication(self, publisher: Publisher[Any], mode: Literal["async", "sync", "direct"]) -> None:
                    # In async mode, this gets wrapped in async
                    reactions.append(f"reacted_{mode}")
            
            subscriber = TestSubscriber()
            publisher.add_subscriber(subscriber)
            
            # Async mode
            publisher.publish(mode="async")
            assert len(reactions) == 0, "Should return immediately"
            
            await asyncio.sleep(0.02)
            assert len(reactions) == 1, "Subscriber should react"
            assert reactions[0] == "reacted_async"
        
        asyncio.run(test())
    
    def test_sync_mode_with_subscriber(self):
        """Test sync mode waits for subscriber reactions."""
        publisher = Publisher(0, "sync")
        reactions: list[str] = []
        
        class TestSubscriber(Subscriber):
            def _react_to_publication(self, publisher: Publisher[Any], mode: Literal["async", "sync", "direct"]) -> None:
                reactions.append(f"reacted_{mode}")
        
        subscriber = TestSubscriber()
        publisher.add_subscriber(subscriber)
        
        # Sync mode should wait
        publisher.publish(mode="sync")
        assert len(reactions) == 1, "Should wait for subscriber"
        assert reactions[0] == "reacted_sync"
    
    def test_direct_mode_with_subscriber(self):
        """Test that direct mode notifies subscribers synchronously."""
        publisher = Publisher(0, "sync")
        reactions: list[str] = []
        
        class TestSubscriber(Subscriber):
            def _react_to_publication(self, publisher: Publisher[Any], mode: Literal["async", "sync", "direct"]) -> None:
                reactions.append(f"reacted_{mode}")
        
        subscriber = TestSubscriber()
        publisher.add_subscriber(subscriber)
        
        # Direct mode should notify subscribers synchronously
        publisher.publish(mode="direct")
        
        assert len(reactions) == 1, "Subscribers should be notified in direct mode"
        assert reactions[0] == "reacted_direct"

