"""
Thread safety tests for the observables library.

These tests verify that the library is safe to use in multi-threaded environments
and that no race conditions exist in critical operations.
"""

from typing import Any
import threading
import time
import pytest

from unittest.mock import Mock

from nexpy import XValue, XList
from nexpy import XBase



class TestThreadSafety:
    """Test thread safety of core observable operations."""

    def test_concurrent_value_modifications(self):
        """Test that concurrent value modifications are thread-safe."""
        obs = XValue("initial")
        errors: list[str] = []
        num_threads = 5
        iterations_per_thread = 100
        
        def modifier_thread(thread_id: int):
            """Modify values from a specific thread."""
            try:
                for i in range(iterations_per_thread):
                    value = f"thread_{thread_id}_value_{i}"
                    obs.value = value
                    # Verify we can read it back
                    read_value = obs.value
                    assert isinstance(read_value, str), f"Expected string, got {type(read_value)}"
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Start multiple threads
        threads: list[threading.Thread] = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=modifier_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        
        # Verify final state is consistent
        final_value = obs.value
        assert isinstance(final_value, str)
        assert "thread_" in final_value

    def test_concurrent_binding_operations(self):
        """Test thread safety of binding operations."""
        errors: list[str] = []
        
        def binding_worker(worker_id: int):
            """Worker that creates and destroys bindings."""
            try:
                for i in range(50):
                    obs1 = XValue(f"worker_{worker_id}_obs1_{i}")
                    obs2 = XValue(f"worker_{worker_id}_obs2_{i}")
                    
                    # Bind them
                    obs1.join(obs2.value_hook, "use_caller_value")
                    
                    # Modify values
                    obs1.value = f"modified_{i}"
                    
                    # Read synchronized value
                    _ = obs2.value
                    
                    # Detach
                    obs1.isolate()
                    
                    time.sleep(0.001)  # Small delay
                    
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        # Start multiple binding workers
        threads: list[threading.Thread] = []
        num_workers = 3
        
        for worker_id in range(num_workers):
            thread = threading.Thread(target=binding_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"Binding thread safety issues: {errors}"

    def test_listener_thread_safety(self):
        """Test thread safety of listener notifications."""
        obs = XValue("initial")
        listener_calls: list[str] = []
        errors: list[str] = []
        listener_lock = threading.Lock()
        
        def listener():
            """Listener that records calls."""
            try:
                value = obs.value
                with listener_lock:
                    listener_calls.append(value)
            except Exception as e:
                errors.append(f"Listener error: {e}")
        
        def modifier_thread(thread_id: int):
            """Thread that modifies values."""
            try:
                for i in range(100):
                    obs.value = f"thread_{thread_id}_value_{i}"
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Modifier {thread_id} error: {e}")
        
        def listener_manager_thread():
            """Thread that adds/removes listeners."""
            try:
                for _ in range(25):
                    obs.add_listener(listener)
                    time.sleep(0.01)
                    obs.remove_listener(listener)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Listener manager error: {e}")
        
        # Start threads
        modifier1 = threading.Thread(target=modifier_thread, args=(1,))
        modifier2 = threading.Thread(target=modifier_thread, args=(2,))
        listener_mgr = threading.Thread(target=listener_manager_thread)
        
        modifier1.start()
        modifier2.start()
        listener_mgr.start()
        
        modifier1.join()
        modifier2.join()
        listener_mgr.join()
        
        assert len(errors) == 0, f"Listener thread safety issues: {errors}"
        # Listener calls count is non-deterministic but should be > 0
        assert len(listener_calls) > 0, "Listeners should have been called"

    def test_x_list_thread_safety(self):
        """Test thread safety specific to XList operations."""
        obs_list = XList([1, 2, 3])
        errors: list[str] = []
        
        def list_modifier(thread_id: int):
            """Thread that modifies the list."""
            try:
                for i in range(50):
                    base_value = thread_id * 1000 + i
                    obs_list.append(base_value)
                    obs_list.extend([base_value + 1, base_value + 2])
                    
                    # Read operations
                    _ = len(obs_list.list)
                    _ = obs_list.length_hook.value
                    
                    # Remove some elements if list is large enough
                    if len(obs_list.list) > 10:
                        try:
                            obs_list.remove(obs_list.list[0])
                        except (ValueError, IndexError):
                            pass  # Element might have been removed by another thread
                    
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"List modifier {thread_id} error: {e}")
        
        # Start multiple list modifier threads
        threads: list[threading.Thread] = []
        for thread_id in range(3):
            thread = threading.Thread(target=list_modifier, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"XList thread safety issues: {errors}"
        
        # Verify final list is in a consistent state
        final_list = obs_list.list
        final_length = obs_list.length_hook.value
        assert len(final_list) == final_length, "List length secondary hook should match actual length"


class TestThreadSafetyEdgeCases:
    """Test edge cases and stress scenarios for thread safety."""

    def test_rapid_hook_replacement_during_binding(self):
        """Test hook nexus replacement during rapid binding operations."""
        errors: list[str] = []
        
        def rapid_binder():
            """Rapidly create and destroy bindings."""
            try:
                for i in range(100):
                    obs1 = XValue(f"value1_{i}")
                    obs2 = XValue(f"value2_{i}")
                    obs3 = XValue(f"value3_{i}")
                    
                    # Create a chain: obs1 -> obs2 -> obs3
                    obs1.join(obs2.value_hook, "use_caller_value")
                    obs2.join(obs3.value_hook, "use_caller_value")
                    
                    # Modify the chain
                    obs1.value = f"new_value_{i}"
                    
                    # Break the chain
                    obs1.isolate()
                    obs2.isolate()
                    
            except Exception as e:
                errors.append(f"Rapid binder error: {e}")
        
        # Start multiple rapid binder threads
        threads: list[threading.Thread] = []
        for _ in range(3):
            thread = threading.Thread(target=rapid_binder)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"Rapid binding thread safety issues: {errors}"

    def test_concurrent_secondary_hook_access(self):
        """Test concurrent access to secondary hooks."""
        obs_list = XList(list(range(100)))
        errors: list[str] = []
        length_values: list[int] = []
        length_lock = threading.Lock()
        
        def length_reader():
            """Thread that continuously reads the length secondary hook."""
            try:
                for _ in range(200):
                    length = obs_list.length_hook.value
                    with length_lock:
                        length_values.append(length)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Length reader error: {e}")
        
        def list_modifier():
            """Thread that modifies the list."""
            try:
                for i in range(100):
                    obs_list.append(100 + i)
                    if i % 10 == 0 and len(obs_list.list) > 50:
                        obs_list.remove(obs_list.list[0])
                    time.sleep(0.002)
            except Exception as e:
                errors.append(f"List modifier error: {e}")
        
        # Start threads
        reader1 = threading.Thread(target=length_reader)
        reader2 = threading.Thread(target=length_reader)
        modifier = threading.Thread(target=list_modifier)
        
        reader1.start()
        reader2.start()
        modifier.start()
        
        reader1.join()
        reader2.join()
        modifier.join()
        
        assert len(errors) == 0, f"Emitter hook concurrency issues: {errors}"
        
        # Verify we got length readings
        assert len(length_values) > 0, "Should have recorded length values"
        
        # Verify final consistency
        final_length = obs_list.length_hook.value
        actual_length = len(obs_list.list)
        assert final_length == actual_length, "Final secondary hook value should match actual length"

    @pytest.mark.slow
    @pytest.mark.skip(reason="Test hangs intermittently - needs further investigation")
    def test_stress_test_thread_safety(self):
        """Stress test with many concurrent operations."""
        errors: list[str] = []
        observables: list[XBase[Any, Any, Any]] = []
        
        # Create shared observables
        for i in range(10):
            obs: XValue[Any] = XValue[Any](f"initial_{i}")
            observables.append(obs)
        
        def stress_worker(worker_id: int):
            """Worker that performs many different operations."""
            try:
                for i in range(100):
                    # Pick random observables
                    obs1: XValue[Any] = observables[i % len(observables)] # type: ignore
                    obs2 = observables[(i + 1) % len(observables)]
                    
                    # Perform various operations
                    if i % 4 == 0:
                        # Binding operations
                        obs1.join(obs2.value_hook, "use_caller_value") # type: ignore
                        obs1.value = f"worker_{worker_id}_value_{i}"
                        obs1.isolate()
                    elif i % 4 == 1:
                        # Listener operations
                        listener = Mock()
                        obs1.add_listener(listener)
                        obs1.value = f"worker_{worker_id}_listen_{i}"
                        obs1.remove_listener(listener)
                    elif i % 4 == 2:
                        # Hook operations
                        hook = obs1.value_hook
                        hook.change_value(f"worker_{worker_id}_hook_{i}")
                    else:
                        # Direct value operations
                        obs1.value = f"worker_{worker_id}_direct_{i}"
                    
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append(f"Stress worker {worker_id} error: {e}")
        
        # Start many worker threads
        threads: list[threading.Thread] = []
        num_workers = 8
        
        for worker_id in range(num_workers):
            thread = threading.Thread(target=stress_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0, f"Stress test thread safety issues: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
