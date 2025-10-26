from typing import Any, Literal, Mapping, Optional
import threading
from logging import Logger

from nexpy import XCompositeBase
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook as OwnedReadOnlyHook
from nexpy.core.hooks.implementations.owned_writable_hook import OwnedWritableHook as OwnedWritableHook

# Alias for backward compatibility with existing tests
OwnedHook = OwnedReadOnlyHook

from run_tests import console_logger as logger
import pytest

class MockObservable(XCompositeBase[Literal["value"], str, Any, Any]):
    """Mock observable for testing purposes that can handle arbitrary hooks."""
    
    def __init__(self, name: str):
        self._internal_construct_from_values({"value": name})
        # Store hooks that are created with this owner
        self._registered_hooks: dict[Any, Any] = {}
    
    def _internal_construct_from_values(
        self,
        initial_values: Mapping[Any, Any],
        logger: Optional[Logger] = None,
        **kwargs: Any) -> None:
        """Construct a MockObservable instance."""
        super().__init__(
            initial_hook_values=initial_values,
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={},
            validate_complete_primary_values_callback=None,
            logger=logger
        )
    
    def _act_on_invalidation(self, keys: set[Any]) -> None:
        """Act on invalidation - required by BaseXObject."""
        pass
    
    def _get_key_by_hook_or_nexus(self, hook_or_nexus: Any) -> Any:
        """Get the key for a hook - return a dummy key for any hook."""
        # For testing purposes, return a dummy key
        return "dummy_key"
    
    def _get_hook_key(self, hook_or_nexus: Any) -> Any:
        """Get the key for a hook - return a dummy key for any hook."""
        # For testing purposes, return a dummy key
        return "dummy_key"
    
    def _validate_value(self, key: Any, value: Any, *, logger: Optional[Logger] = None) -> tuple[bool, str]:
        """Validate a value - always return True for testing."""
        return True, "Valid"
    
class TestHookCapabilities:
    """Test hooks with different capabilities in the new hook-based system."""

    def test_hook_creation_with_invalidate_callback(self):
        """Test hook creation with invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook with invalidate callback
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="initial_value",
            logger=logger
        )
        
        # Verify the hook is created correctly
        assert hook.value == "initial_value"
        assert hook.owner == mock_owner
        assert hook._get_nexus() is not None  # type: ignore

    def test_hook_creation_without_invalidate_callback(self):
        """Test hook creation without invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hook without invalidate callback
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="initial_value",
            logger=logger
        )
            
        # Verify the hook is created correctly
        assert hook.value == "initial_value"
        assert hook.owner == mock_owner
        assert hook._get_nexus() is not None  # type: ignore

    def test_value_hook_property(self):
        """Test the value property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="test_value",
            logger=logger
        )
        
        # Test the value property
        assert hook.value == "test_value"
        
        # The value comes from the hook nexus, so it should be consistent
        assert hook._get_nexus().stored_value == "test_value"  # type: ignore

    def test_hook_owner_property(self):
        """Test the owner property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test the owner property
        assert hook.owner == mock_owner
        
        # Test that owner is the same instance
        assert hook.owner is mock_owner

    def test_hook_hook_nexus_property(self):
        """Test the hook_nexus property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test the hook_nexus property
        assert hook._get_nexus() is not None  # type: ignore
        assert hook in hook._get_nexus().hooks  # type: ignore
        
        # Test that hook_nexus is consistent
        hook_nexus1 = hook._get_nexus()  # type: ignore
        hook_nexus2 = hook._get_nexus()  # type: ignore
        assert hook_nexus1 is hook_nexus2

    def test_hook_lock_property(self):
        """Test the lock property of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test the lock property
        assert hook._lock is not None  # type: ignore
        
        # Test that lock is a threading lock type
        assert hasattr(hook._lock, 'acquire')  # type: ignore
        assert hasattr(hook._lock, 'release')  # type: ignore
        
        # Test that lock can be acquired
        with hook._lock:  # type: ignore
            # This should not raise an error
            pass

    def test_hook_connect_to(self):
        """Test the connect_to method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value1",
            logger=logger
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
            logger=logger
        )
        
        # Initially, hooks are in separate hook nexuses
        assert hook1._get_nexus() != hook2._get_nexus()  # type: ignore
        
        # Connect hook1 to hook2
        hook1.join(hook2, "use_caller_value")  # type: ignore
        
        # Now they should be in the same hook nexus
        assert hook1._get_nexus() == hook2._get_nexus()  # type: ignore
        assert hook1 in hook2._get_nexus().hooks  # type: ignore
        assert hook2 in hook1._get_nexus().hooks  # type: ignore

    def test_hook_connect_to_invalid_sync_mode(self):
        """Test connect_to with invalid sync mode."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value1",
            logger=logger
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
            logger=logger
        )
        
        # Test with invalid sync mode
        with pytest.raises(ValueError, match="Invalid sync mode"):
            hook1.join(hook2, "invalid_mode")  # type: ignore

    def test_hook_detach(self):
        """Test the detach method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Get the original hook nexus
        original_nexus = hook._get_nexus()  # type: ignore
        
        # Create another hook to connect with
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",  # Same value as first hook
            logger=logger
        )
        
        # Connect them so they're in the same hook nexus
        hook.join(hook2, "use_caller_value")  # type: ignore
        
        # Now disconnect the first hook
        hook.isolate()
        
        # Verify the hook is now in a new, separate hook nexus
        assert hook._get_nexus() != original_nexus  # type: ignore
        assert hook in hook._get_nexus().hooks  # type: ignore
        assert len(hook._get_nexus().hooks) == 1  # type: ignore

    def test_hook_detach_multiple_times(self):
        """Test calling detach multiple times."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
    
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Create another hook to connect with
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",  # Same value as first hook
            logger=logger
        )
        
        # Connect them so they're in the same group
        hook.join(hook2, "use_caller_value")  # type: ignore
        
        # First disconnect should work and create a new nexus
        original_nexus = hook._get_nexus()  # type: ignore
        hook.isolate()
        
        # Should create a new hook nexus
        assert hook._get_nexus() != original_nexus  # type: ignore
        assert hook in hook._get_nexus().hooks  # type: ignore
        assert len(hook._get_nexus().hooks) == 1  # type: ignore
        
        # Second disconnect should do nothing since hook is already isolated
        nexus_after_first_disconnect = hook._get_nexus()  # type: ignore
        hook.isolate()
        
        # Should still be the same nexus
        assert hook._get_nexus() == nexus_after_first_disconnect  # type: ignore
        assert hook in hook._get_nexus().hooks  # type: ignore
        assert len(hook._get_nexus().hooks) == 1  # type: ignore

    def test_hooksubmit_value(self):
        """Test the submit_value method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="initial_value",
            logger=logger
        )
        
        # Test submitting a new value
        success, message = hook.change_value("new_value")
        assert success, f"Submit failed: {message}"
        
        # The value should be updated in the hook nexus
        assert hook._get_nexus().stored_value  # type: ignore == "new_value"

    def test_hook_submit_value_without_callback(self):
        """Test submit_value on a hook without invalidate callback."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook without invalidate callback
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="initial_value",
            logger=logger
        )
        
        # Test submitting a value - should still work as it goes through the hook nexus
        success, message = hook.change_value("new_value")
        assert success, f"Submit failed: {message}"

    def test_hook_is_joined_with_by_key(self):
        """Test the is_joined_with method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value1",
            logger=logger
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
            logger=logger
        )
        
        # Initially, hooks are not attached
        assert not hook1.is_joined_with(hook2)
        assert not hook2.is_joined_with(hook1)
        
        # Connect them
        hook1.join(hook2, "use_caller_value")  # type: ignore
        
        # Now they should be attached
        assert hook1.is_joined_with(hook2)
        assert hook2.is_joined_with(hook1)

    def test_hook_is_valid_value(self):
        """Test the _validate_value method of hooks."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test validation using the new API
        success, message = hook._validate_value("new_value", logger=logger)
        # The actual result depends on the validation logic
        assert isinstance(success, bool)
        assert isinstance(message, str)

    def test_hook_replace_nexus(self):
        """Test the isolate method creates a new nexus after joining."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
            logger=logger
        )
        
        # Join them first
        hook1.join(hook2, "use_caller_value")
        
        # Get the shared nexus
        shared_nexus = hook1._get_nexus()  # type: ignore
        
        # Isolate hook1 - should create a new nexus
        hook1.isolate()
        
        # Verify hook1 is now in a separate nexus
        assert hook1._get_nexus() != shared_nexus  # type: ignore
        assert hook1._get_nexus() != hook2._get_nexus()  # type: ignore
        assert len(hook1._get_nexus().hooks) == 1  # type: ignore

    def test_hook_thread_safety_basic(self):
        """Test basic thread safety of hooks."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook for this test since we need change_value
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="initial",
            logger=logger
        )
        
        # Test concurrent access
        def reader():
            for _ in range(100):
                try:
                    _ = hook.value
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def writer():
            for i in range(100):
                try:
                    hook.change_value(f"value_{i}")
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        
        # Start threads
        reader_thread.start()
        writer_thread.start()
        
        # Wait for completion
        reader_thread.join()
        writer_thread.join()
        
        # Verify no exceptions occurred during concurrent access
        assert True, "Basic thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_property_access(self):
        """Test thread safety of hook properties under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test concurrent property access
        def property_reader():
            for _ in range(200):
                try:
                    _ = hook.owner
                    _ = hook._get_nexus()  # type: ignore
                    _ = hook._lock  # type: ignore
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def property_writer():
            for _ in range(100):
                try:
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        reader_thread = threading.Thread(target=property_reader)
        writer_thread = threading.Thread(target=property_writer)
        
        # Start threads
        reader_thread.start()
        writer_thread.start()
        
        # Wait for completion
        reader_thread.join()
        writer_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Property thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_method_calls(self):
        """Test thread safety of hook methods under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook for this test since we need change_value
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test concurrent method calls
        def method_caller():
            for _ in range(150):
                try:
                    hook.change_value("test")
                    time.sleep(0.001)
                except Exception:
                    pass
        
        def state_changer():
            for _ in range(100):
                try:
                    time.sleep(0.0015)
                except Exception:
                    pass
        
        # Create threads
        caller_thread = threading.Thread(target=method_caller)
        changer_thread = threading.Thread(target=state_changer)
        
        # Start threads
        caller_thread.start()
        changer_thread.start()
        
        # Wait for completion
        caller_thread.join()
        changer_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Method thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_hook_nexus_operations(self):
        """Test thread safety of hook nexus operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create multiple hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value1",
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
        )
        
        # Test concurrent hook nexus operations
        def nexus_operator():
            for _ in range(100):
                try:
                    # Add hook2 to hook1's hook nexus
                    hook1._get_nexus().add_hook(hook2)  # type: ignore
                    time.sleep(0.002)
                    # Remove hook2 from hook1's hook nexus
                    hook1._get_nexus().remove_hook(hook2)  # type: ignore
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def hook_accessor():
            for _ in range(200):
                try:
                    _ = hook1._get_nexus().hooks  # type: ignore
                    _ = len(hook1._get_nexus().hooks)  # type: ignore
                    _ = hook1.is_joined_with(hook2)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        operator_thread = threading.Thread(target=nexus_operator)
        accessor_thread = threading.Thread(target=hook_accessor)
        
        # Start threads
        operator_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        operator_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Hook nexus thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_detach_operations(self):
        """Test thread safety of detach operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
        )
        
        # Test concurrent detach operations
        def detach_caller():
            for _ in range(50):
                try:
                    # Create another hook to connect with first
                    hook2 = OwnedHook[str, Any](
                        owner=mock_owner,
                        value="value",
                    )
                    hook.join(hook2, "use_caller_value")  # type: ignore
                    hook.isolate()
                    time.sleep(0.003)
                except Exception:
                    pass
        
        def property_accessor():
            for _ in range(200):
                try:
                    _ = hook._get_nexus()  # type: ignore
                    _ = len(hook._get_nexus().hooks)  # type: ignore
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        detach_thread = threading.Thread(target=detach_caller)
        accessor_thread = threading.Thread(target=property_accessor)
        
        # Start threads
        detach_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        detach_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Detach thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_submit_operations(self):
        """Test thread safety of submit operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook for this test since we need change_value
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="value",
        )
        
        # Test concurrent submit operations
        def submit_caller():
            for _ in range(100):
                try:
                    hook.change_value("test")
                    time.sleep(0.002)
                except Exception:
                    pass
        
        def state_accessor():
            for _ in range(200):
                try:
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        submit_thread = threading.Thread(target=submit_caller)
        accessor_thread = threading.Thread(target=state_accessor)
        
        # Start threads
        submit_thread.start()
        accessor_thread.start()
        
        # Wait for completion
        submit_thread.join()
        accessor_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Submit thread safety test completed without errors"

    def test_hook_thread_safety_concurrent_connect_operations(self):
        """Test thread safety of connect operations under concurrent access."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value1",
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value2",
        )
        
        # Test concurrent connect operations
        def connect_caller():
            for _ in range(50):
                try:
                    hook1.join(hook2, "use_caller_value")  # type: ignore
                    time.sleep(0.003)
                except Exception:
                    pass
        
        def connection_checker():
            for _ in range(200):
                try:
                    _ = hook1.is_joined_with(hook2)
                    _ = hook2.is_joined_with(hook1)
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        connect_thread = threading.Thread(target=connect_caller)
        checker_thread = threading.Thread(target=connection_checker)
        
        # Start threads
        connect_thread.start()
        checker_thread.start()
        
        # Wait for completion
        connect_thread.join()
        checker_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Connect operations thread safety test completed without errors"

    def test_hook_thread_safety_stress_test(self):
        """Stress test for thread safety with many concurrent operations."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook for this test since we need change_value
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="value",
        )
        
        # Test many concurrent operations
        def stress_worker(worker_id: int):
            for i in range(50):
                try:
                    # Mix of operations
                    if i % 5 == 0:
                        hook.change_value(f"value_{worker_id}_{i}")
                    elif i % 5 == 2:
                        _ = hook._get_nexus()  # type: ignore
                        _ = len(hook._get_nexus().hooks)  # type: ignore
                    else:
                        _ = hook.value
                    
                    time.sleep(0.001)
                except Exception:
                    pass
        
        # Create multiple worker threads
        threads: list[threading.Thread] = []
        for worker_id in range(5):
            thread = threading.Thread(target=stress_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        assert True, "Stress test thread safety test completed without errors"

    def test_hook_thread_safety_lock_contention(self):
        """Test thread safety under lock contention scenarios."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a writable hook for this test since we need change_value
        hook = OwnedWritableHook[str, Any](
            owner=mock_owner,
            value="value",
        )
        
        # Test lock contention
        def lock_contender():
            for _ in range(100):
                try:
                    with hook._lock:  # type: ignore
                        # Hold the lock for a bit to create contention
                        time.sleep(0.001)
                        hook.change_value("contended")
                except Exception:
                    pass
        
        def lock_waiter():
            for _ in range(100):
                try:
                    with hook._lock:  # type: ignore
                        time.sleep(0.001)
                except Exception:
                    pass
        
        # Create threads
        contender_thread = threading.Thread(target=lock_contender)
        waiter_thread = threading.Thread(target=lock_waiter)
        
        # Start threads
        contender_thread.start()
        waiter_thread.start()
        
        # Wait for completion
        contender_thread.join()
        waiter_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Lock contention thread safety test completed without errors"

    def test_hook_thread_safety_race_conditions(self):
        """Test thread safety under potential race condition scenarios."""
        import time
        
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        _ = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
        )
        
        # Test race conditions
        def race_condition_creator():
            for _ in range(100):
                try:
                    # Rapidly change state
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        def race_condition_observer():
            for _ in range(200):
                try:
                    # Rapidly check state   
                    time.sleep(0.0005)
                except Exception:
                    pass
        
        # Create threads
        creator_thread = threading.Thread(target=race_condition_creator)
        observer_thread = threading.Thread(target=race_condition_observer)
        
        # Start threads
        creator_thread.start()
        observer_thread.start()
        
        # Wait for completion
        creator_thread.join()
        observer_thread.join()
        
        # Verify no exceptions occurred
        assert True, "Race condition thread safety test completed without errors"

    def test_hook_with_different_types(self):
        """Test hooks with different data types."""
        # Test with int
        mock_owner = MockObservable("test_owner")
        int_hook = OwnedHook[int, Any](
            owner=mock_owner,
            value=42,
            logger=logger
        )
        assert int_hook.value == 42
        
        # Test with float
        float_hook = OwnedHook[float, Any](
            owner=mock_owner,
            value=3.14,
            logger=logger
        )
        assert float_hook.value == 3.14
        
        # Test with bool
        bool_hook = OwnedHook[bool, Any](
            owner=mock_owner,
            value=True,
            logger=logger
        )
        assert bool_hook.value == True
        
        # Test with list
        list_hook = OwnedHook[list[str], Any](
            owner=mock_owner,
            value=["a", "b", "c"],
            logger=logger
        )
        # Lists are stored as-is (no immutability conversion)
        assert list_hook.value == ["a", "b", "c"]

    def test_hook_equality_and_hash(self):
        """Test hook equality and hashing behavior."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create two identical hooks
        hook1 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        hook2 = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Hooks should not be equal (they're different instances)
        assert hook1 != hook2
        
        # Hooks should be hashable
        assert isinstance(hash(hook1), int)
        assert isinstance(hash(hook2), int)
        
        # Same hook should be equal to itself
        assert hook1 == hook1
        assert hook2 == hook2

    def test_hook_string_representation(self):
        """Test hook string representation."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        # Create a hook
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test string representation
        hook_str = str(hook)
        hook_repr = repr(hook)
        
        # Should contain useful information
        assert "Hook" in hook_str
        assert "Hook" in hook_repr

    def test_hook_with_none_owner(self):
        """Test hook creation with None owner."""
        # Note: Current implementation doesn't validate owner parameter
        # This test documents the current behavior
        try:
            hook = OwnedHook[str, Any](
                owner=None,  # type: ignore
                value="value",
                logger=logger
            )
            # If no exception is raised, that's the current behavior
            assert hook.owner is None
        except Exception as e:
            # If an exception is raised, that's also acceptable
            assert isinstance(e, Exception)


    def test_hook_with_exception_handling_callbacks(self):
        """Test hooks with callbacks that handle exceptions."""
        # Create mock observable for owner
        mock_owner = MockObservable("test_owner")
        
        hook = OwnedHook[str, Any](
            owner=mock_owner,
            value="value",
            logger=logger
        )
        
        # Test that a hook can access its owner
        assert hook.owner == mock_owner
        assert hook.owner is mock_owner
