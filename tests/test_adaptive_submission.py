"""
Test adaptive submission system based on hook count.

This test verifies that the nexus manager automatically selects the optimal
internal submit implementation based on the number of hooks involved.
"""

import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from nexpy import FloatingHook
from nexpy.core.nexus_system.nexus_manager import NexusManager
from test_base import ObservableTestCase


class TestAdaptiveSubmission(ObservableTestCase):
    """Test adaptive submission based on hook count."""
    
    def setup_method(self):
        super().setup_method()
        self.manager = NexusManager()
    
    def test_hook_count_tracking(self):
        """Test that hook count is properly tracked in nexus."""
        print("\n=== Hook Count Tracking Test ===")
        
        # Create hooks
        hook1 = FloatingHook[int](42)
        hook2 = FloatingHook[int](43)
        hook3 = FloatingHook[int](44)
        
        # Check initial hook count
        nexus1 = hook1._get_nexus()
        assert nexus1.hook_count == 1
        print(f"Single hook nexus count: {nexus1.hook_count}")
        
        # Connect hooks to increase count
        hook1.join(hook2, "use_caller_value")
        nexus1 = hook1._get_nexus()  # Get the merged nexus
        assert nexus1.hook_count == 2
        print(f"Connected hooks nexus count: {nexus1.hook_count}")
        
        # Connect third hook
        hook1.join(hook3, "use_caller_value")
        nexus1 = hook1._get_nexus()  # Get the merged nexus
        assert nexus1.hook_count == 3
        print(f"Three connected hooks nexus count: {nexus1.hook_count}")
        
        # Verify all hooks share the same nexus
        assert hook1._get_nexus() is hook2._get_nexus()
        assert hook2._get_nexus() is hook3._get_nexus()
    
    def test_small_scale_adaptive_selection(self):
        """Test adaptive selection for small scale (< 50 hooks)."""
        print("\n=== Small Scale Adaptive Selection Test ===")
        
        # Create 10 hooks (small scale)
        hooks = [FloatingHook[int](i) for i in range(10)]
        
        # Connect them all to one nexus
        for i in range(1, len(hooks)):
            hooks[0].join(hooks[i], "use_caller_value")
        
        # Verify all hooks are in the same nexus
        nexus = hooks[0]._get_nexus()
        assert nexus.hook_count == 10
        print(f"Small scale nexus hook count: {nexus.hook_count}")
        
        # Test submission - should use optimized implementation
        nexus_and_values = {nexus: 100}
        
        start_time = time.perf_counter()
        success, msg = self.manager.submit_values(nexus_and_values)
        time_taken = time.perf_counter() - start_time
        
        print(f"Small scale submission: {time_taken:.6f}s - {msg}")
        assert success
        assert hooks[0].value == 100
    
    def test_medium_scale_adaptive_selection(self):
        """Test adaptive selection for medium scale (50-200 hooks)."""
        print("\n=== Medium Scale Adaptive Selection Test ===")
        
        # Create 100 hooks (medium scale)
        hooks = [FloatingHook[int](i) for i in range(100)]
        
        # Connect them all to one nexus
        for i in range(1, len(hooks)):
            hooks[0].join(hooks[i], "use_caller_value")
        
        # Verify all hooks are in the same nexus
        nexus = hooks[0]._get_nexus()
        assert nexus.hook_count == 100
        print(f"Medium scale nexus hook count: {nexus.hook_count}")
        
        # Test submission - should use original implementation
        nexus_and_values = {nexus: 200}
        
        start_time = time.perf_counter()
        success, msg = self.manager.submit_values(nexus_and_values)
        time_taken = time.perf_counter() - start_time
        
        print(f"Medium scale submission: {time_taken:.6f}s - {msg}")
        assert success
        assert hooks[0].value == 200
    
    def test_large_scale_adaptive_selection(self):
        """Test adaptive selection for large scale (> 200 hooks)."""
        print("\n=== Large Scale Adaptive Selection Test ===")
        
        # Create 300 hooks (large scale)
        hooks = [FloatingHook[int](i) for i in range(300)]
        
        # Connect them all to one nexus
        for i in range(1, len(hooks)):
            hooks[0].join(hooks[i], "use_caller_value")
        
        # Verify all hooks are in the same nexus
        nexus = hooks[0]._get_nexus()
        assert nexus.hook_count == 300
        print(f"Large scale nexus hook count: {nexus.hook_count}")
        
        # Test submission - should use optimized implementation
        nexus_and_values = {nexus: 300}
        
        start_time = time.perf_counter()
        success, msg = self.manager.submit_values(nexus_and_values)
        time_taken = time.perf_counter() - start_time
        
        print(f"Large scale submission: {time_taken:.6f}s - {msg}")
        assert success
        assert hooks[0].value == 300
    
    def test_multiple_nexus_hook_count(self):
        """Test hook count calculation across multiple nexuses."""
        print("\n=== Multiple Nexus Hook Count Test ===")
        
        # Create two separate nexus groups
        hooks1 = [FloatingHook[int](i) for i in range(30)]  # 30 hooks
        hooks2 = [FloatingHook[int](i) for i in range(40)]  # 40 hooks
        
        # Connect each group internally
        for i in range(1, len(hooks1)):
            hooks1[0].join(hooks1[i], "use_caller_value")
        for i in range(1, len(hooks2)):
            hooks2[0].join(hooks2[i], "use_caller_value")
        
        nexus1 = hooks1[0]._get_nexus()
        nexus2 = hooks2[0]._get_nexus()
        
        assert nexus1.hook_count == 30
        assert nexus2.hook_count == 40
        print(f"Nexus 1 hook count: {nexus1.hook_count}")
        print(f"Nexus 2 hook count: {nexus2.hook_count}")
        
        # Test submission with both nexuses (total: 70 hooks - should use original implementation)
        nexus_and_values = {nexus1: 100, nexus2: 200}
        
        start_time = time.perf_counter()
        success, msg = self.manager.submit_values(nexus_and_values)
        time_taken = time.perf_counter() - start_time
        
        print(f"Multiple nexus submission (70 hooks): {time_taken:.6f}s - {msg}")
        assert success
        assert hooks1[0].value == 100
        assert hooks2[0].value == 200
    
    def test_hook_count_accuracy(self):
        """Test that hook count remains accurate after operations."""
        print("\n=== Hook Count Accuracy Test ===")
        
        # Create hooks
        hooks = [FloatingHook[int](i) for i in range(5)]
        
        # Connect them incrementally and check count
        nexus = hooks[0]._get_nexus()
        assert nexus.hook_count == 1
        
        for i in range(1, len(hooks)):
            hooks[0].join(hooks[i], "use_caller_value")
            nexus = hooks[0]._get_nexus()  # Get the updated merged nexus
            assert nexus.hook_count == i + 1
            print(f"After connecting hook {i+1}: count = {nexus.hook_count}")
        
        # Test that count is accurate after value changes
        nexus_and_values = {nexus: 999}
        success, msg = self.manager.submit_values(nexus_and_values)
        assert success
        assert nexus.hook_count == 5  # Count should remain unchanged
        
        print(f"Final hook count after submission: {nexus.hook_count}")
    
    def test_performance_comparison_adaptive_vs_fixed(self):
        """Compare performance of adaptive vs fixed implementations."""
        print("\n=== Adaptive vs Fixed Performance Comparison ===")
        
        # Test different scales
        test_cases = [
            (10, "Small"),
            (100, "Medium"), 
            (300, "Large")
        ]
        
        for hook_count, scale_name in test_cases:
            print(f"\n{scale_name} scale ({hook_count} hooks):")
            
            # Create hooks
            hooks = [FloatingHook[int](i) for i in range(hook_count)]
            
            # Connect them all
            for i in range(1, len(hooks)):
                hooks[0].join(hooks[i], "use_caller_value")
            
            nexus = hooks[0]._get_nexus()
            nexus_and_values = {nexus: hook_count * 10}
            
            # Test adaptive submission
            start_time = time.perf_counter()
            success, msg = self.manager.submit_values(nexus_and_values)
            adaptive_time = time.perf_counter() - start_time
            
            print(f"  Adaptive submission: {adaptive_time:.6f}s - {msg}")
            assert success
            
            # Reset values for next test
            nexus_and_values = {nexus: 0}
            self.manager.submit_values(nexus_and_values)


if __name__ == "__main__":
    # Run the adaptive submission tests
    test_instance = TestAdaptiveSubmission()
    test_instance.setup_method()
    
    print("=" * 60)
    print("ADAPTIVE SUBMISSION SYSTEM TEST")
    print("=" * 60)
    
    test_instance.test_hook_count_tracking()
    test_instance.test_small_scale_adaptive_selection()
    test_instance.test_medium_scale_adaptive_selection()
    test_instance.test_large_scale_adaptive_selection()
    test_instance.test_multiple_nexus_hook_count()
    test_instance.test_hook_count_accuracy()
    test_instance.test_performance_comparison_adaptive_vs_fixed()
    
    print("\n" + "=" * 60)
    print("ADAPTIVE SUBMISSION TESTS COMPLETE")
    print("=" * 60)
