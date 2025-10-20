"""
Tests for Nexus fusion and transitive synchronization.

Based on the documentation in docs/usage.md and docs/concepts.md.
"""

import pytest
import nexpy as nx
from test_base import ObservableTestCase


class TestNexusFusion(ObservableTestCase):
    """Test Nexus fusion mechanics."""
    
    def test_basic_join(self):
        """Test basic join operation between two hooks."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(20)
        
        assert A.value == 10
        assert B.value == 20
        
        # Join - B adopts A's value
        A.join(B, "use_caller_value")
        
        assert A.value == 10
        assert B.value == 10
        
        # Now synchronized
        A.value = 30
        assert B.value == 30
    
    def test_join_is_symmetric(self):
        """Test that joining creates bidirectional synchronization."""
        A1 = nx.FloatingHook(10)
        B1 = nx.FloatingHook(20)
        A1.join(B1, "use_caller_value")
        
        A2 = nx.FloatingHook(10)
        B2 = nx.FloatingHook(20)
        B2.join(A2, "use_caller_value")
        
        # After join, both hooks in each pair are synchronized
        # Caller's value is preserved: A1 for first pair, B2 for second pair
        assert A1.value == B1.value == 10
        assert A2.value == B2.value == 20
        
        # After join, updates propagate symmetrically in both directions
        A1.value = 100
        assert B1.value == 100
        
        A2.value = 200
        assert B2.value == 200
    
    def test_transitive_synchronization(self):
        """Test transitive synchronization: A→B + B→C = A→B→C."""
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(2)
        C = nx.FloatingHook(3)
        D = nx.FloatingHook(4)
        
        # Create first fusion domain
        A.join(B, "use_caller_value")
        assert A.value == 1 and B.value == 1
        
        # Create second fusion domain
        C.join(D, "use_caller_value")
        assert C.value == 3 and D.value == 3
        
        # Fuse both domains
        B.join(C, "use_caller_value")
        
        # All four hooks now share the same value
        assert A.value == B.value == C.value == D.value
        
        # Verify transitivity: A and D were never joined directly
        A.value = 999
        assert D.value == 999
    
    def test_transitive_with_xvalue(self):
        """Test transitive synchronization with XValue objects."""
        temp1 = nx.XValue(20.0)
        temp2 = nx.XValue(21.0)
        temp3 = nx.XValue(22.0)
        
        temp1.value_hook.join(temp2.value_hook, "use_caller_value")
        temp2.value_hook.join(temp3.value_hook, "use_caller_value")
        
        # All synchronized
        assert temp1.value == temp2.value == temp3.value
        
        temp3.value = 25.0
        assert temp1.value == 25.0
    
    def test_basic_isolate(self):
        """Test isolate operation."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        C = nx.FloatingHook(10)
        
        A.join(B, "use_caller_value")
        B.join(C, "use_caller_value")
        
        # All joined
        A.value = 20
        assert B.value == 20 and C.value == 20
        
        # Isolate B
        B.isolate()
        
        # B is now independent
        A.value = 30
        assert A.value == 30
        assert B.value == 20  # Unchanged
        assert C.value == 30  # Still joined with A
    
    def test_isolate_preserves_value(self):
        """Test that isolate preserves the current value."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        
        A.join(B, "use_caller_value")
        A.value = 50
        
        assert B.value == 50
        
        # Isolate B with current value
        B.isolate()
        
        assert B.value == 50  # Value preserved
        
        # Now independent
        A.value = 100
        assert B.value == 50  # B unchanged
    
    def test_is_joined_with(self):
        """Test is_joined_with method."""
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(2)
        C = nx.FloatingHook(3)
        
        assert not A.is_joined_with(B)
        assert not B.is_joined_with(C)
        
        A.join(B, "use_caller_value")
        assert A.is_joined_with(B)
        assert B.is_joined_with(A)
        assert not A.is_joined_with(C)
        
        B.join(C, "use_caller_value")
        assert A.is_joined_with(C)  # Transitive
        assert C.is_joined_with(A)
    
    def test_fusion_domain_size(self):
        """Test creating large fusion domains."""
        hooks = [nx.FloatingHook(i) for i in range(100)]
        
        # Join all to first hook
        for hook in hooks[1:]:
            hooks[0].join(hook, "use_caller_value")
        
        # All should share the same value
        hooks[0].value = 999
        for hook in hooks:
            assert hook.value == 999
    
    def test_fusion_with_listeners(self):
        """Test that fusion triggers listeners on all hooks."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        
        a_updates: list[int] = []
        b_updates: list[int] = []
        
        A.add_listener(lambda: a_updates.append(A.value))
        B.add_listener(lambda: b_updates.append(B.value))
        
        A.join(B, "use_caller_value")
        
        # Update through A
        A.value = 20
        assert len(a_updates) == 1
        assert len(b_updates) == 1
        
        # Update through B
        B.value = 30
        assert len(a_updates) == 2
        assert len(b_updates) == 2
    
    def test_multiple_isolate_idempotent(self):
        """Test that multiple isolate calls are idempotent."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        
        A.join(B, "use_caller_value")
        
        # First isolate
        A.isolate()
        assert not A.is_joined_with(B)
        
        # Second isolate (should be no-op)
        A.isolate()
        assert not A.is_joined_with(B)
        
        # Values still independent
        A.value = 20
        B.value = 30
        assert A.value == 20
        assert B.value == 30
    
    def test_rejoin_after_isolate(self):
        """Test joining again after isolate."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        
        A.join(B, "use_caller_value")
        A.isolate()
        
        assert not A.is_joined_with(B)
        
        # Join again
        A.value = 100
        B.value = 200
        A.join(B, "use_caller_value")
        
        assert A.is_joined_with(B)
        assert A.value == 100
        assert B.value == 100
    
    def test_fusion_with_xdict(self):
        """Test fusion with XDict objects."""
        dict1 = nx.XDict({"a": 1, "b": 2})
        dict2 = nx.XDict({"c": 3, "d": 4})
        
        dict1.dict_hook.join(dict2.dict_hook, "use_caller_value")
        
        # Synchronized
        dict1["e"] = 5
        assert "e" in dict2.dict
        assert dict2["e"] == 5
    
    def test_fusion_with_xlist(self):
        """Test fusion with XList objects."""
        list1 = nx.XList([1, 2, 3])
        list2 = nx.XList([4, 5, 6])
        
        list1.list_hook.join(list2.list_hook, "use_caller_value")
        
        # Synchronized
        assert list1.list == list2.list
        
        list1.append(7)
        assert 7 in list2.list
    
    def test_fusion_validation_failure(self):
        """Test that fusion fails if validation fails."""
        def validate_positive(value: int):
            if value > 0:
                return True, "Valid"
            return False, "Must be positive"
        
        A = nx.FloatingHook(10, isolated_validation_callback=validate_positive)
        B = nx.FloatingHook(-5)
        
        # Join with use_other_value should fail because B's value is negative
        with pytest.raises(Exception):  # ValueError or SubmissionError
            A.join(B, "use_target_value")  # Tries to use B's negative value
    
    def test_complex_fusion_network(self):
        """Test complex fusion network with multiple merge operations."""
        # Create 4 separate domains
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(2)
        C = nx.FloatingHook(3)
        D = nx.FloatingHook(4)
        E = nx.FloatingHook(5)
        F = nx.FloatingHook(6)
        
        # Domain 1: A-B
        A.join(B, "use_caller_value")
        # Domain 2: C-D
        C.join(D, "use_caller_value")
        # Domain 3: E-F
        E.join(F, "use_caller_value")
        
        # Merge domains 1 and 2
        B.join(C, "use_caller_value")
        # Now A,B,C,D share same nexus
        
        # Merge with domain 3
        D.join(E, "use_caller_value")
        # Now all 6 share same nexus
        
        assert A.is_joined_with(F)  # Never joined directly!
        
        F.value = 999
        assert A.value == 999

