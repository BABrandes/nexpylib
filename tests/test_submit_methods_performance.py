"""
Performance comparison between internal_submit_1.py and internal_submit_2.py.

This test compares the performance characteristics of both internal submit implementations
to understand their differences and identify optimization opportunities.
"""

import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nexpy import FloatingHook, XValue, XList, XSet
from nexpy.core.nexus_system.nexus_manager import NexusManager
from nexpy.core.nexus_system.internal_submit_methods.internal_submit_1 import internal_submit_values as internal_submit_1
from nexpy.core.nexus_system.internal_submit_methods.internal_submit_2 import internal_submit_values as internal_submit_2
from test_base import ObservableTestCase
import pytest


class TestSubmitMethodsPerformance(ObservableTestCase):
    """Test performance differences between internal submit implementations."""
    
    def setup_method(self):
        super().setup_method()
        self.manager = NexusManager()
    
    def test_small_scale_performance(self):
        """Test performance with small number of hooks (typical use case)."""
        print("\n=== Small Scale Performance Test ===")
        
        # Create 10 hooks
        hooks_1 = [FloatingHook[int](i) for i in range(10)]
        hooks_2 = [FloatingHook[int](i) for i in range(10)]
        
        # Prepare nexus and values for both implementations
        nexus_and_values_1 = {hook._get_nexus(): hook.value + 100 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): hook.value + 100 for hook in hooks_2}
        
        # Test internal_submit_1
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1: {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2: {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == 100
        assert hooks_2[0].value == 100
    
    def test_medium_scale_performance(self):
        """Test performance with medium number of hooks."""
        print("\n=== Medium Scale Performance Test ===")
        
        # Create 100 hooks
        hooks_1 = [FloatingHook[int](i) for i in range(100)]
        hooks_2 = [FloatingHook[int](i) for i in range(100)]
        
        # Prepare nexus and values for both implementations
        nexus_and_values_1 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_2}
        
        # Test internal_submit_1
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1: {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2: {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == 1000
        assert hooks_2[0].value == 1000
    
    def test_large_scale_performance(self):
        """Test performance with large number of hooks."""
        print("\n=== Large Scale Performance Test ===")
        
        # Create 500 hooks
        hooks_1 = [FloatingHook[int](i) for i in range(500)]
        hooks_2 = [FloatingHook[int](i) for i in range(500)]
        
        # Prepare nexus and values for both implementations
        nexus_and_values_1 = {hook._get_nexus(): hook.value + 5000 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): hook.value + 5000 for hook in hooks_2}
        
        # Test internal_submit_1
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1: {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2: {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == 5000
        assert hooks_2[0].value == 5000
    
    def test_complex_objects_performance(self):
        """Test performance with complex objects (lists, sets)."""
        print("\n=== Complex Objects Performance Test ===")
        
        # Create hooks with complex objects
        hooks_1 = [FloatingHook[list]([i, i+1, i+2]) for i in range(50)]
        hooks_2 = [FloatingHook[list]([i, i+1, i+2]) for i in range(50)]
        
        # Prepare nexus and values for both implementations
        nexus_and_values_1 = {hook._get_nexus(): [hook.value[0] + 100, hook.value[1] + 100, hook.value[2] + 100] for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): [hook.value[0] + 100, hook.value[1] + 100, hook.value[2] + 100] for hook in hooks_2}
        
        # Test internal_submit_1
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1: {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2: {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == [100, 101, 102]
        assert hooks_2[0].value == [100, 101, 102]
    
    def test_validation_mode_performance(self):
        """Test performance in validation-only mode."""
        print("\n=== Validation Mode Performance Test ===")
        
        # Create hooks
        hooks_1 = [FloatingHook[int](i) for i in range(100)]
        hooks_2 = [FloatingHook[int](i) for i in range(100)]
        
        # Prepare nexus and values for both implementations
        nexus_and_values_1 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_2}
        
        # Test internal_submit_1 (validation only)
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Check values")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2 (validation only)
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Check values")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1 (validation): {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2 (validation): {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        # Values should be unchanged since we only checked them
        assert hooks_1[0].value == 0
        assert hooks_2[0].value == 0
    
    def test_forced_submission_performance(self):
        """Test performance in forced submission mode."""
        print("\n=== Forced Submission Performance Test ===")
        
        # Create hooks with same values (forced submission should still process)
        hooks_1 = [FloatingHook[int](42) for _ in range(100)]
        hooks_2 = [FloatingHook[int](42) for _ in range(100)]
        
        # Prepare nexus and values for both implementations (same values)
        nexus_and_values_1 = {hook._get_nexus(): 42 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): 42 for hook in hooks_2}
        
        # Test internal_submit_1 (forced submission)
        start_time = time.perf_counter()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Forced submission")
        time_1 = time.perf_counter() - start_time
        
        # Test internal_submit_2 (forced submission)
        start_time = time.perf_counter()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Forced submission")
        time_2 = time.perf_counter() - start_time
        
        print(f"Internal Submit 1 (forced): {time_1:.6f}s - {msg_1}")
        print(f"Internal Submit 2 (forced): {time_2:.6f}s - {msg_2}")
        print(f"Speedup: {time_1/time_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == 42
        assert hooks_2[0].value == 42
    
    def test_memory_usage_comparison(self):
        """Test memory usage patterns between implementations."""
        print("\n=== Memory Usage Comparison ===")
        
        import tracemalloc
        
        # Create hooks
        hooks_1 = [FloatingHook[int](i) for i in range(200)]
        hooks_2 = [FloatingHook[int](i) for i in range(200)]
        
        # Prepare nexus and values
        nexus_and_values_1 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_1}
        nexus_and_values_2 = {hook._get_nexus(): hook.value + 1000 for hook in hooks_2}
        
        # Test internal_submit_1 memory usage
        tracemalloc.start()
        success_1, msg_1 = internal_submit_1(self.manager, nexus_and_values_1, "Normal submission")
        current_1, peak_1 = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Test internal_submit_2 memory usage
        tracemalloc.start()
        success_2, msg_2 = internal_submit_2(self.manager, nexus_and_values_2, "Normal submission")
        current_2, peak_2 = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"Internal Submit 1 - Peak memory: {peak_1 / 1024:.2f} KB")
        print(f"Internal Submit 2 - Peak memory: {peak_2 / 1024:.2f} KB")
        print(f"Memory ratio: {peak_1/peak_2:.2f}x")
        
        assert success_1 and success_2
        assert hooks_1[0].value == 1000
        assert hooks_2[0].value == 1000


if __name__ == "__main__":
    # Run the performance tests
    test_instance = TestSubmitMethodsPerformance()
    test_instance.setup_method()
    
    print("=" * 60)
    print("PERFORMANCE COMPARISON: Internal Submit Methods")
    print("=" * 60)
    
    test_instance.test_small_scale_performance()
    test_instance.test_medium_scale_performance()
    test_instance.test_large_scale_performance()
    test_instance.test_complex_objects_performance()
    test_instance.test_validation_mode_performance()
    test_instance.test_forced_submission_performance()
    test_instance.test_memory_usage_comparison()
    
    print("\n" + "=" * 60)
    print("PERFORMANCE ANALYSIS COMPLETE")
    print("=" * 60)
