"""
Performance tests for the observables library.

These tests verify that performance optimizations (especially O(1) cache lookups)
are working correctly and detect performance regressions.
"""

from typing import Any, Callable
from logging import basicConfig, getLogger, DEBUG

import time
import gc
import pytest   

from nexpy import XValue, XList, XDictSelect
from nexpy import XBase

basicConfig(level=DEBUG)
logger = getLogger(__name__)

def time_operation(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Time the execution of a function."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    return result, end - start


class TestCachePerformance:
    """Test performance of the O(1) cache optimizations."""

    def setup_method(self):
        """Clean up before each test for consistent performance measurements."""
        # Force garbage collection to clear any accumulated objects
        gc.collect()
        # Small delay to let system stabilize
        time.sleep(0.01)

    def test_get_key_cache_performance(self):
        """Test that get_key operations use O(1) cache after first access."""
        # Create an observable with a moderate number of hooks via binding
        main_obs: XValue[Any] = XValue("main")
        bound_xobjects: list[XBase[Any, Any, Any]] = []
        
        # Create bound observables to populate the hook nexus
        for i in range(50):
            obs: XValue[Any] = XValue[Any](f"value_{i}")
            obs.join(main_obs.value_hook, "use_caller_value")
            bound_xobjects.append(obs)
        
        # Now main_obs's hook nexus has many hooks
        hook = main_obs.value_hook
        
        # Time the first call (should do linear search + populate cache)
        def first_call() -> str:
            return main_obs._get_key_by_hook_or_nexus(hook) # type: ignore
        
        result1, time1 = time_operation(first_call)
        assert result1 == "value"
        
        # Time subsequent calls (should use cache)
        times: list[float] = []
        for _ in range(10):
            def cached_call() -> str:
                return main_obs._get_key_by_hook_or_nexus(hook) # type: ignore
            
            result, elapsed = time_operation(cached_call)
            assert result == "value"
            times.append(elapsed)
        
        _ = sum(times) / len(times)
        
        # Cached calls should be consistently fast
        # (Even if times are too small to measure precisely, they should be consistent)
        assert all(t <= time1 * 2 for t in times), "Cached calls should not be slower than first call"
        
        # Clean up
        for obs in bound_xobjects: # type: ignore
            obs.isolate()

    def test_secondary_hook_cache_performance(self):
        """Test that secondary hook lookups are cached."""
        obs_list: XList[Any] = XList[Any](list(range(100)))
        
        # Get the length secondary hook
        length_hook = obs_list.length_hook
        
        # Time first access to secondary hook key lookup
        def first_secondary_lookup() -> str:
            return obs_list._get_key_by_hook_or_nexus(length_hook) # type: ignore
        
        result1, time1 = time_operation(first_secondary_lookup)
        assert result1 == "length"
        
        # Time subsequent accesses
        times: list[float] = []
        for _ in range(10):
            def cached_secondary_lookup() -> str:
                return obs_list._get_key_by_hook_or_nexus(length_hook) # type: ignore
            
            result, elapsed = time_operation(cached_secondary_lookup)
            assert result == "length"
            times.append(elapsed)
        
        # All cached calls should be fast and consistent
        _ = sum(times) / len(times)
        assert all(t <= time1 * 2 for t in times), "Cached secondary hook calls should not be slower"

    def test_cache_effectiveness_across_operations(self):
        """Test that cache is effective across different operations that use get_key."""
        obs = XValue("test")
        
        # Perform operations that internally use get_key
        operations: list[tuple[int, float, str]] = []
        
        def operation1():
            obs.value = "modified1"
            return obs.value
        
        def operation2():
            hook = obs.value_hook
            hook.change_value("modified2")
            return hook.value
        
        def operation3():
            obs.value = "modified3"
            return obs.value
        
        # Time each operation
        for i, op in enumerate([operation1, operation2, operation3]):
            result, elapsed = time_operation(op)
            operations.append((i, elapsed, result))
        
        # All operations should complete successfully
        assert all(result.startswith("modified") for _, _, result in operations)
        
        # Operations should be consistently fast (cache working)
        times: list[float] = [elapsed for _, elapsed, _ in operations]
        avg_time = sum(times) / len(times)
        
        # No operation should be significantly slower than average
        # (indicating cache misses or performance regression)
        assert all(t <= avg_time * 3 for t in times), "Operations should have consistent performance"


class TestScalabilityPerformance:
    """Test that performance scales appropriately with observable complexity."""

    def setup_method(self):
        """Clean up before each test for consistent performance measurements."""
        gc.collect()
        time.sleep(0.01)

    @pytest.mark.slow
    def test_binding_operation_scalability(self):
        """
        Test that binding operations scale reasonably with more hooks.
        
        This test creates a star topology where all hooks connect to one central observable.
        This pattern naturally results in O(n²) behavior because:
        - Each new hook joins an increasingly large nexus
        - Each join triggers notifications to all existing hooks
        - Each new hook must synchronize with all existing hooks
        
        This is expected behavior for this specific pattern, not a performance bug.
        """
        # Test different scales
        scales = [10, 50, 100]
        binding_times: list[tuple[int, float]] = []
        
        for scale in scales:
            # Create observables
            main_obs = XValue(f"main_{scale}")
            bound_xobjects: list[XValue[Any]] = []
            
            # Time the binding operations
            start_time = time.perf_counter()
            
            for i in range(scale):
                obs = XValue(f"value_{i}")
                obs.join(main_obs.value_hook, "use_caller_value")
                bound_xobjects.append(obs)
            
            binding_time = time.perf_counter() - start_time
            binding_times.append((scale, binding_time))
            
            # Test that the binding network works
            main_obs.value = f"test_{scale}"
            for obs in bound_xobjects[:5]:  # Check a few
                assert obs.value == f"test_{scale}"
            
            # Clean up
            for obs in bound_xobjects:
                obs.isolate()
        
        # Performance should scale at most quadratically with size
        # This is expected for star topology connections
        for i in range(1, len(binding_times)):
            prev_scale, prev_time = binding_times[i-1]
            curr_scale, curr_time = binding_times[i]
            
            # Time should scale no worse than quadratically with size
            # (allowing for some overhead and measurement noise)
            time_ratio = curr_time / prev_time if prev_time > 0 else 1
            scale_ratio = curr_scale / prev_scale
            
            # Allow for O(n²) behavior with some tolerance
            max_expected_ratio = scale_ratio ** 2 + 2  # +2 for measurement noise
            
            assert time_ratio <= max_expected_ratio, \
                f"Performance degraded too much: scale {prev_scale}->{curr_scale}, time {prev_time:.4f}->{curr_time:.4f}, ratio {time_ratio:.2f} > {max_expected_ratio:.2f}"

    def test_secondary_hook_update_performance(self):
        """Test that secondary hook updates are efficient."""
        scales = [100, 500, 1000]
        update_times: list[tuple[int, float]] = []
        
        for scale in scales:
            obs_list = XList(list(range(scale)))
            
            # Time operations that trigger secondary hook updates
            start_time = time.perf_counter()
            
            # Perform operations that update length secondary hook
            for i in range(10):
                obs_list.append(scale + i)
                obs_list.extend([scale + i + 1000, scale + i + 2000])
                _ = obs_list.length_hook.value  # Access secondary hook
            
            update_time = time.perf_counter() - start_time
            update_times.append((scale, update_time))
        
        # Updates should not degrade dramatically with list size
        # (secondary hooks should be O(1) to compute and access)
        for i in range(1, len(update_times)):
            prev_scale, prev_time = update_times[i-1]
            curr_scale, curr_time = update_times[i]
            
            # Time should not increase dramatically with scale
            if prev_time > 0:
                time_ratio = curr_time / prev_time
                scale_ratio = curr_scale / prev_scale
                
                # Allow some variance but prevent quadratic or worse degradation
                assert time_ratio <= scale_ratio * 2, \
                    f"Emitter hook update performance degraded: scale {prev_scale}->{curr_scale}, time {prev_time:.4f}->{curr_time:.4f}"

    def test_complex_operation_performance(self):
        """Test performance of complex operations involving multiple observables."""
        # Create a complex scenario with multiple observable types
        obs_single = XValue("single")
        obs_list = XList([1, 2, 3])
        obs_dict = XDictSelect({"key": "value"}, "key")
        
        # Create a simpler binding pattern that avoids nexus conflicts
        # Connect obs_single to obs_list.length_hook
        obs_single.join(obs_list.length_hook, "use_target_value")  # type: ignore
        
        # Create a separate binding for obs_dict to avoid conflicts
        # Use a different approach: bind obs_dict.length_hook to a new observable
        obs_dict_tracker = XValue(1)
        obs_dict_tracker.join(obs_dict.length_hook, "use_target_value")
        
        # Time complex operations
        def complex_operation():
            # Modify list (triggers length update)
            obs_list.extend([4, 5, 6])
            
            # Access various values (triggers cache lookups)
            single_val = obs_single.value
            list_len = obs_list.length_hook.value
            dict_len = obs_dict.length_hook.value
            
            # Modify dict by adding a key
            current_dict = dict(obs_dict.dict_hook.value)
            current_dict["new_key"] = "new_value"
            obs_dict.change_dict(current_dict)
            obs_dict.key = "new_key"
            
            return single_val, list_len, dict_len
        
        # Run the operation multiple times and measure
        times: list[float] = []
        for _ in range(10):
            _, elapsed = time_operation(complex_operation)
            times.append(elapsed)
        
        # Operations should be consistently fast
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # No single operation should be dramatically slower than average (allow more variance for timing variations)
        assert max_time <= avg_time * 10 + 0.001, f"Complex operation had inconsistent performance: avg={avg_time:.4f}, max={max_time:.4f}"
        
        # All operations should complete in reasonable time
        assert avg_time < 0.01, f"Complex operations too slow: {avg_time:.4f} seconds average"


class TestPerformanceRegression:
    """Test for performance regressions in core operations."""

    def setup_method(self):
        """Clean up before each test for consistent performance measurements."""
        gc.collect()
        time.sleep(0.01)

    def test_value_setting_performance(self):
        """Test that basic value setting operations are fast."""
        obs = XValue("initial")
        
        # Time many value setting operations
        num_operations = 1000
        start_time = time.perf_counter()
        
        for i in range(num_operations):
            obs.value = f"value_{i}"
        
        total_time = time.perf_counter() - start_time
        avg_time_per_op = total_time / num_operations
        
        # Each operation should be very fast
        assert avg_time_per_op < 0.001, f"Value setting too slow: {avg_time_per_op:.6f} seconds per operation"

    def test_hook_access_performance(self):
        """Test that hook access operations are fast."""
        obs = XValue("test")
        
        # Time many hook access operations
        num_operations = 1000
        start_time = time.perf_counter()
        
        for _ in range(num_operations):
            hook = obs.value_hook
            _ = hook.value
        
        total_time = time.perf_counter() - start_time
        avg_time_per_op = total_time / num_operations
        
        # Hook access should be very fast
        assert avg_time_per_op < 0.001, f"Hook access too slow: {avg_time_per_op:.6f} seconds per operation"

    def test_listener_notification_performance(self):
        """Test that listener notifications don't cause performance regression."""
        obs = XValue("initial")
        
        # Add multiple listeners
        call_counts: list[list[int]] = []
        for i in range(10):
            count = [0]
            call_counts.append(count)
            
            def make_listener(counter: list[int]):
                def listener():
                    counter[0] += 1
                return listener
            
            obs.add_listener(make_listener(count))
        
        # Time operations with listener notifications
        num_operations = 100
        start_time = time.perf_counter()
        
        for i in range(num_operations):
            obs.value = f"value_{i}"
        
        total_time = time.perf_counter() - start_time
        avg_time_per_op = total_time / num_operations
        
        # Operations with listeners should still be reasonably fast
        assert avg_time_per_op < 0.01, f"Operations with listeners too slow: {avg_time_per_op:.6f} seconds per operation"
        
        # Verify listeners were called
        total_calls = sum(count[0] for count in call_counts)
        expected_calls = num_operations * len(call_counts)
        assert total_calls == expected_calls, f"Expected {expected_calls} listener calls, got {total_calls}"

    @pytest.mark.slow
    def test_memory_usage_stability(self):
        """Test that memory usage remains stable during repeated operations."""
        import gc
        
        # Get initial memory baseline
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform many operations that should not accumulate memory
        for cycle in range(100):
            obs = XValue(f"cycle_{cycle}")
            
            # Perform various operations
            obs.value = f"modified_{cycle}"
            hook = obs.value_hook
            _ = hook.value
            
            # Add and remove listener
            listener = lambda: None
            obs.add_listener(listener)
            obs.remove_listener(listener)
            
            # Clean up explicitly
            del obs, hook, listener
            
            # Periodic garbage collection
            if cycle % 20 == 0:
                gc.collect()
        
        # Final cleanup
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not have grown significantly
        growth = final_objects - initial_objects
        assert growth < 500, f"Memory usage grew too much: {growth} objects accumulated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
