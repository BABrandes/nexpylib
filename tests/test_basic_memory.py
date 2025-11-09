"""
Basic memory management tests for the observables library.

These tests verify essential memory management without being too strict
about edge cases that may be implementation-dependent.
"""

import gc
import weakref
from typing import Any
import pytest
from nexpy import (
    XValue, XList, XSet, XDict,
    XDictSelect, XDictSelectOptional
)
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook as ReadOnlyHook
from nexpy import XBase


class TestEssentialMemoryManagement:
    """Test essential memory management scenarios."""

    def test_simple_observable_cleanup(self):
        """Test that simple observables are cleaned up."""
        obs = XValue("test")
        obs_ref = weakref.ref(obs)
        
        del obs
        gc.collect()
        
        assert obs_ref() is None, "Simple observable was not cleaned up"

    def test_observable_with_simple_listeners(self):
        """Test cleanup with simple listeners."""
        obs = XValue("test")
        
        call_count = [0]
        def listener():
            call_count[0] += 1
        
        obs.add_listener(listener)
        obs.value = "modified"
        assert call_count[0] == 1
        
        obs_ref = weakref.ref(obs)
        listener_ref = weakref.ref(listener)
        
        del obs, listener
        gc.collect()
        
        assert obs_ref() is None, "Observable with listener was not cleaned up"
        assert listener_ref() is None, "Listener was not cleaned up"

    def test_simple_binding_cleanup(self):
        """Test cleanup of simply bound observables."""
        obs1 = XValue("value1")
        obs2 = XValue("value2")
        
        # Bind them
        obs1.join(obs2.value_hook, "use_caller_value")  # type: ignore
        
        # Test binding works
        obs1.value = "new_value"
        assert obs2.value == "new_value"
        
        obs1_ref = weakref.ref(obs1)
        obs2_ref = weakref.ref(obs2)
        
        del obs1, obs2
        gc.collect()
        
        assert obs1_ref() is None, "Bound observable 1 was not cleaned up"
        assert obs2_ref() is None, "Bound observable 2 was not cleaned up"

    def test_secondary_hook_basic_cleanup(self):
        """Test basic cleanup of observables with secondary hooks."""
        obs_list = XList([1, 2, 3])
        
        # Access secondary hook
        length_hook = obs_list._get_hook_by_key("length")  # type: ignore
        initial_length = length_hook.value
        assert initial_length == 3
        
        # Modify to trigger secondary hook update
        obs_list.append(4)
        assert length_hook.value == 4
        
        obs_ref = weakref.ref(obs_list)
        
        del obs_list, length_hook
        gc.collect()
        
        assert obs_ref() is None, "Observable with secondary hook was not cleaned up"

    def test_many_simple_xobjects(self):
        """Test that creating many observables doesn't leak memory."""
        # Get baseline
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and destroy many observables
        for batch in range(5):
            observables: list[XValue[Any]] = []
            for i in range(100):
                obs = XValue(f"value_{batch}_{i}")
                observables.append(obs)
            
            # Use the observables
            for obs in observables:
                obs.value = f"modified_{batch}"
            
            # Clear batch
            observables.clear()
            
            # Periodic cleanup
            if batch % 2 == 0:
                gc.collect()
        
        # Final cleanup
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow reasonable growth but not excessive
        growth = final_objects - initial_objects
        assert growth < 2000, f"Excessive memory growth: {growth} objects"

    def test_detached_xobjects_cleanup(self):
        """Test cleanup after detaching bindings."""
        obs1 = XValue("value1")
        obs2 = XValue("value2")
        
        # Bind, test, detach
        obs1.join(obs2.value_hook, "use_caller_value")
        obs1.value = "bound_value"
        assert obs2.value == "bound_value"
        
        obs1.isolate()
        obs1.value = "detached_value"
        assert obs2.value == "bound_value"  # Should not change
        
        obs1_ref = weakref.ref(obs1)
        obs2_ref = weakref.ref(obs2)
        
        del obs1, obs2
        gc.collect()
        
        assert obs1_ref() is None, "Detached observable 1 was not cleaned up"
        assert obs2_ref() is None, "Detached observable 2 was not cleaned up"

    def test_observable_dict_operations(self):
        """Test XDict operations and cleanup."""
        obs_dict = XDict({"a": 1, "b": 2, "c": 3})
        
        # Test basic operations
        assert obs_dict.dict["a"] == 1
        assert obs_dict.length == 3
        assert "b" in obs_dict.keys
        
        # Test modifications
        obs_dict["d"] = 4
        assert obs_dict.length == 4
        
        del obs_dict["a"]
        assert obs_dict.length == 3
        assert "a" not in obs_dict.keys
        
        # Test cleanup
        obs_ref = weakref.ref(obs_dict)
        del obs_dict
        gc.collect()
        
        assert obs_ref() is None, "XDict was not cleaned up"

    def test_x_list_comprehensive_operations(self):
        """Test various XList operations."""
        obs_list = XList([1, 2, 3])
        
        # Test extend
        obs_list.extend([4, 5])
        assert len(obs_list.list) == 5
        assert obs_list.length == 5
        
        # Test insert
        obs_list.insert(0, 0)
        assert obs_list.list[0] == 0
        assert obs_list.length == 6
        
        # Test pop
        popped = obs_list.pop()
        assert popped == 5
        assert obs_list.length == 5
        
        # Test remove
        obs_list.remove(0)
        assert obs_list.length == 4
        
        # Test clear
        obs_list.clear()
        assert obs_list.length == 0
        
        obs_ref = weakref.ref(obs_list)
        del obs_list
        gc.collect()
        
        assert obs_ref() is None, "XList was not cleaned up"

    def test_observable_set_comprehensive_operations(self):
        """Test various XSet operations."""
        obs_set = XSet({1, 2, 3})
        
        # Test add
        obs_set.add(4)
        assert 4 in obs_set.set
        assert obs_set.length == 4
        
        # Test discard
        obs_set.discard(2)
        assert 2 not in obs_set.set
        assert obs_set.length == 3
        
        # Test remove
        obs_set.remove(3)
        assert obs_set.length == 2
        
        # Test clear
        obs_set.clear()
        assert obs_set.length == 0
        
        obs_ref = weakref.ref(obs_set)
        del obs_set
        gc.collect()
        
        assert obs_ref() is None, "XSet was not cleaned up"

    def test_binding_with_target_value_mode(self):
        """Test binding with use_target_value mode."""
        obs1 = XValue("value1")
        obs2 = XValue("value2")
        
        # Bind with use_target_value - obs2's value wins
        obs1.join(obs2.value_hook, "use_target_value")  # type: ignore
        assert obs1.value == "value2"
        
        # Change obs1, both should update
        obs1.value = "new_value"
        assert obs2.value == "new_value"
        
        obs1_ref = weakref.ref(obs1)
        obs2_ref = weakref.ref(obs2)
        
        del obs1, obs2
        gc.collect()
        
        assert obs1_ref() is None
        assert obs2_ref() is None

    def test_multiple_listeners_cleanup(self):
        """Test cleanup with multiple listeners."""
        obs = XValue("test")
        
        call_counts = [0, 0, 0]
        
        def listener1():
            call_counts[0] += 1
        
        def listener2():
            call_counts[1] += 1
        
        def listener3():
            call_counts[2] += 1
        
        obs.add_listener(listener1)
        obs.add_listener(listener2)
        obs.add_listener(listener3)
        
        obs.value = "changed"
        assert call_counts == [1, 1, 1]
        
        obs_ref = weakref.ref(obs)
        listener_refs = [weakref.ref(listener1), weakref.ref(listener2), weakref.ref(listener3)]
        
        del obs, listener1, listener2, listener3
        gc.collect()
        
        assert obs_ref() is None
        for ref in listener_refs:
            assert ref() is None

    def test_secondary_hooks_with_dict(self):
        """Test secondary hooks with XDict."""
        obs_dict = XDict({"x": 1, "y": 2})
        
        # Access secondary hooks
        length_hook = obs_dict._get_hook_by_key("length")  # type: ignore
        keys_hook: ReadOnlyHook[frozenset[str]] = obs_dict._get_hook_by_key("keys")  # type: ignore
        
        assert length_hook.value == 2
        assert "x" in keys_hook.value
        
        # Modify dict
        obs_dict["z"] = 3
        assert length_hook.value == 3
        assert "z" in keys_hook.value
        
        obs_ref = weakref.ref(obs_dict)
        del obs_dict, length_hook, keys_hook
        gc.collect()
        
        assert obs_ref() is None

    def test_selection_dict_cleanup(self):
        """Test cleanup of selection dict observables."""
        sel_dict = XDictSelect({"a": 1, "b": 2}, "a")
        
        assert sel_dict.key == "a"
        assert sel_dict.value == 1
        
        sel_dict.key = "b"
        assert sel_dict.value == 2
        
        sel_dict_ref = weakref.ref(sel_dict)
        del sel_dict
        gc.collect()
        
        assert sel_dict_ref() is None

    def test_optional_selection_dict_cleanup(self):
        """Test cleanup of optional selection dict."""
        opt_sel = XDictSelectOptional({"x": 10, "y": 20}, None)
        
        assert opt_sel.key is None
        assert opt_sel.value is None
        
        opt_sel.key = "x"
        assert opt_sel.value == 10
        
        opt_sel_ref = weakref.ref(opt_sel)
        del opt_sel
        gc.collect()
        
        assert opt_sel_ref() is None

    def test_cross_type_secondary_hooks(self):
        """Test that secondary hooks from different types work correctly."""
        obs_list = XList([1, 2])
        obs_set = XSet({1, 2})
        obs_dict = XDict({"a": 1})
        
        # Get all length hooks
        list_length = obs_list._get_hook_by_key("length")  # type: ignore
        set_length = obs_set._get_hook_by_key("length")  # type: ignore
        dict_length = obs_dict._get_hook_by_key("length")  # type: ignore
        
        assert list_length.value == 2
        assert set_length.value == 2
        assert dict_length.value == 1
        
        # Modify all
        obs_list.append(3)
        obs_set.add(3)
        obs_dict["b"] = 2
        
        assert list_length.value == 3
        assert set_length.value == 3
        assert dict_length.value == 2
        
        # Cleanup
        refs = [weakref.ref(obs_list), weakref.ref(obs_set), weakref.ref(obs_dict)]
        del obs_list, obs_set, obs_dict, list_length, set_length, dict_length
        gc.collect()
        
        for ref in refs:
            assert ref() is None


class TestMemoryStressScenarios:
    """Test memory management under stress."""

    @pytest.mark.slow
    def test_binding_memory_stress(self):
        """Stress test memory with many binding operations."""
        weak_refs: list[weakref.ref[XValue[Any]]] = []
        
        for cycle in range(20):
            # Create observables for this cycle
            cycle_xobjects: list[XValue[Any]] = []
            for i in range(10):
                obs = XValue(f"cycle_{cycle}_value_{i}")
                cycle_xobjects.append(obs)
                weak_refs.append(weakref.ref(obs))
            
            # Create some bindings
            for i in range(len(cycle_xobjects) - 1):
                cycle_xobjects[i].join(  # type: ignore
                    cycle_xobjects[i + 1].value_hook,
                    "use_caller_value"
                )
            
            # Use the chain
            cycle_xobjects[0].value = f"chain_value_{cycle}"
            
            # Clear cycle
            cycle_xobjects.clear()
            
            # Periodic cleanup
            if cycle % 5 == 0:
                gc.collect()
        
        # Final cleanup
        for _ in range(3):
            gc.collect()
        
        # Check that most observables were cleaned up
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        cleanup_rate = (total_count - alive_count) / total_count
        
        # Expect at least 80% cleanup rate
        assert cleanup_rate >= 0.8, f"Poor cleanup rate: {cleanup_rate:.1%} ({alive_count}/{total_count} still alive)"

    def test_mixed_observable_types_memory(self):
        """Test memory management with mixed observable types."""
        observables: list[XBase[Any, Any]] = []
        weak_refs: list[weakref.ref[XBase[Any, Any]]] = []
        
        # Create mixed observable types
        for i in range(20):
            obs_single = XValue(f"single_{i}")
            obs_list = XList([i, i+1])
            obs_set = XSet({i, i+1})
            
            observables.extend([obs_single, obs_list, obs_set])
            weak_refs.extend([
                weakref.ref(obs_single),
                weakref.ref(obs_list),
                weakref.ref(obs_set)
            ])
            
            # Trigger secondary hooks
            obs_list.append(i+2)
            obs_set.add(i+2)
        
        # Clear observables
        observables.clear()
        
        # Cleanup
        for _ in range(3):
            gc.collect()
        
        # Verify cleanup
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        
        # Allow some tolerance for complex scenarios
        assert alive_count <= total_count * 0.2, f"Too many objects alive: {alive_count}/{total_count}"

    def test_dict_operations_stress(self):
        """Stress test with many dict operations."""
        weak_refs: list[weakref.ref[XDict[str, int]]] = []
        
        for cycle in range(15):
            dicts: list[XDict[str, int]] = []
            for i in range(10):
                obs_dict = XDict({"x": i, "y": i * 2})
                dicts.append(obs_dict)
                weak_refs.append(weakref.ref(obs_dict))
                
                # Perform various operations
                obs_dict["z"] = i * 3
                del obs_dict["x"]
                obs_dict.update({"a": i, "b": i + 1})
            
            dicts.clear()
            
            if cycle % 5 == 0:
                gc.collect()
        
        # Cleanup
        for _ in range(3):
            gc.collect()
        
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        cleanup_rate = (total_count - alive_count) / total_count
        
        assert cleanup_rate >= 0.8, f"Poor cleanup rate: {cleanup_rate:.1%}"

    def test_selection_dict_stress(self):
        """Stress test with selection dicts."""
        weak_refs: list[weakref.ref[XDictSelect[str, int]]] = []
        
        for _ in range(10):
            sel_dicts: list[XDictSelect[str, int]] = []
            
            for i in range(15):
                sel_dict = XDictSelect({"a": i, "b": i * 2, "c": i * 3}, "a")
                sel_dicts.append(sel_dict)
                weak_refs.append(weakref.ref(sel_dict))
                
                # Change selections
                sel_dict.key = "b"
                sel_dict.key = "c"
                sel_dict.key = "a"
            
            sel_dicts.clear()
            gc.collect()
        
        # Final cleanup
        for _ in range(3):
            gc.collect()
        
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        
        assert alive_count <= total_count * 0.2, f"Too many objects alive: {alive_count}/{total_count}"

    def test_listener_notification_stress(self):
        """Stress test listener notifications."""
        notification_count = [0]
        
        def counter_listener():
            notification_count[0] += 1
        
        observables: list[XValue[int]] = []
        
        for i in range(50):
            obs = XValue(i)
            obs.add_listener(counter_listener)
            observables.append(obs)
            
            # Trigger notifications (skip j=0 since it's the same as initial value)
            for j in range(1, 6):
                obs.value = i + j
        
        # Should have 50 observables * 5 changes = 250 notifications
        assert notification_count[0] == 250
        
        # Cleanup
        weak_refs = [weakref.ref(obs) for obs in observables]
        observables.clear()
        del counter_listener
        
        for _ in range(3):
            gc.collect()
        
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        assert alive_count <= len(weak_refs) * 0.1

    def test_complex_binding_chains(self):
        """Test complex binding chains cleanup."""
        weak_refs: list[weakref.ref[XValue[str]]] = []
        
        for cycle in range(10):
            # Create a star topology of bindings
            center = XValue(f"center_{cycle}")
            satellites: list[XValue[str]] = []
            
            weak_refs.append(weakref.ref(center))
            
            for i in range(10):
                sat = XValue(f"sat_{cycle}_{i}")
                satellites.append(sat)
                weak_refs.append(weakref.ref(sat))
                
                # Bind satellite to center
                sat.join(center.value_hook, "use_caller_value")  # type: ignore
            
            # Change center, all satellites should update
            center.value = f"broadcast_{cycle}"
            
            # Verify all updated
            for sat in satellites:
                assert sat.value == f"broadcast_{cycle}"
            
            # Clear
            satellites.clear()
            del center
            
            if cycle % 3 == 0:
                gc.collect()
        
        # Final cleanup
        for _ in range(3):
            gc.collect()
        
        alive_count = sum(1 for ref in weak_refs if ref() is not None)
        total_count = len(weak_refs)
        cleanup_rate = (total_count - alive_count) / total_count
        
        assert cleanup_rate >= 0.85, f"Poor cleanup rate: {cleanup_rate:.1%}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
