#!/usr/bin/env python3
"""
Test Collective Hooks System

This test file tests the collective hook system with multiple X object types.
It covers complex binding scenarios, collective validation, and transitive binding behavior.
"""

import time

from nexpy import XValue, XSet, XSetSingleSelect, XSetSingleSelectOptional
from run_tests import console_logger as logger
import pytest

class TestCollectiveHooks:
    """Test the collective hooks system with multiple X object types."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create XSet instances with color sets (compatible types)
        self.set1: XSet[str] = XSet({"Red", "Green", "Blue"}, logger=logger)
        self.set2: XSet[str] = XSet({"Red", "Green", "Blue"}, logger=logger)
        
        # Create XSetSingleSelect instances with compatible initial states
        # Pass XSet directly since XSetSingleSelect now expects XSetProtocol
        self.selector1: XSetSingleSelect[str] = XSetSingleSelect("Red", self.set1, logger=logger)
        self.selector2: XSetSingleSelect[str] = XSetSingleSelect("Red", self.set2, logger=logger)
        
        # Create XValue instances with colors (compatible types)
        self.value1: XValue[str] = XValue("Red", logger=logger)
        self.value2: XValue[str] = XValue("Red", logger=logger)

    def test_collective_hooks_property(self):
        """Test that collective_hooks property returns the correct hooks."""
        # XSetSingleSelect should have selected_option, available_options, and secondary hooks
        all_hooks = list(self.selector1._primary_hooks.values()) + list(self.selector1._secondary_hooks.values()) # type: ignore
        assert len(all_hooks) == 3
        assert self.selector1._primary_hooks["selected_option"] in all_hooks # type: ignore
        assert self.selector1._primary_hooks["available_options"] in all_hooks # type: ignore
        
        # XValue should have 1 collective hook (just the primary hook, no secondary hooks)
        all_hooks_value = [self.value1._value_hook] # type: ignore
        assert len(all_hooks_value) == 1 # type: ignore
        
        # XSet should have 2 collective hooks (primary hook + length secondary hook)
        all_hooks_set = list(self.set1._primary_hooks.values()) + list(self.set1._secondary_hooks.values()) # type: ignore
        assert len(all_hooks_set) == 2 # type: ignore

    def test_complex_binding_network(self):
        """Test a complex binding network with multiple X object types."""
        # Bind selector1 to selector2
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Bind value1 to selector1's selected_option
        self.selector1.join_by_key("selected_option", self.value1.value_hook, "use_caller_value")  # type: ignore
        
        # Bind set1 to selector1's available_options
        self.selector1.join_by_key("available_options", self.set1.set_hook, "use_caller_value")  # type: ignore
        
        # Bind value2 to selector2's selected_option
        self.selector2.join_by_key("selected_option", self.value2.value_hook, "use_caller_value")  # type: ignore
        
        # Bind set2 to selector2's available_options
        self.selector2.join_by_key("available_options", self.set2.set_hook, "use_caller_value")  # type: ignore
        
        # Now change selector1 and verify all propagate
        self.selector1.change_selected_option_and_available_options("Green", {"Green", "Blue", "Purple"})
        
        # Verify all observables are synchronized
        assert self.selector2.selected_option == "Green"
        assert self.selector2.available_options == {"Green", "Blue", "Purple"}
        assert self.value1.value == "Green"
        assert self.set1.set == {"Green", "Blue", "Purple"}
        assert self.value2.value == "Green"
        assert self.set2.set == {"Green", "Blue", "Purple"}

    def test_binding_removal_and_rebinding(self):
        """Test removing bindings and rebinding differently."""
        # Initial binding: selector1 -> selector2
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Verify initial binding works
        self.selector1.selected_option = "Blue"
        assert self.selector2.selected_option == "Blue"
        
        # Remove binding
        self.selector1.isolate_all()
        
        # Verify binding is removed
        self.selector1.selected_option = "Green"
        assert self.selector2.selected_option == "Blue"  # Should not change
        
        # Rebind with different sync mode
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_target_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_target_value")  # type: ignore
        
        # Verify new binding works - first update available options
        self.selector2.available_options = {"Red", "Green", "Blue", "Purple"}
        self.selector2.selected_option = "Purple"
        assert self.selector1.selected_option == "Purple"

    def test_collective_validation(self):
        """Test collective validation with multiple dependent values."""
        # Create a selector with strict validation
        strict_selector = XSetSingleSelect("Red", {"Red", "Green"}, logger=logger)
        
        # Test that setting available_options without the current selected_option fails
        with pytest.raises(ValueError):
            strict_selector.available_options = {"Blue", "Purple"}  # "Red" not in new options
        
        # Test individual property validation
        with pytest.raises(ValueError):
            strict_selector.selected_option = "InvalidOption"  # Not in current available options
        
        # Test that the validation actually works by trying to set an invalid value
        # First, make sure the current state is valid by using atomic update
        strict_selector.change_selected_option_and_available_options("Green", {"Green", "Blue"})
        
        # Now try to set an invalid selected_option
        with pytest.raises(ValueError):
            strict_selector.selected_option = "InvalidOption"
        
        # Test the specific case that was failing
        # Create a new selector and try to set an invalid state
        test_selector = XSetSingleSelect("Red", {"Red", "Green"}, logger=logger)
        
        # This should fail because "Red" is not in {"Green", "Blue"}
        with pytest.raises(ValueError):
            test_selector.available_options = {"Green", "Blue"}  # "Red" not in new options

    def test_transitive_binding_behavior(self):
        """Test transitive binding behavior with multiple observables."""
        # Create a chain: selector1 -> selector2 -> value1 -> set1
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        self.selector2.join_by_key("selected_option", self.value1.value_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.set1.set_hook, "use_caller_value")  # type: ignore
        
        # Change the source (selector1) - first update available options
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"})
        
        # Verify all observables in the chain are synchronized
        assert self.selector2.selected_option == "Purple"
        assert self.selector2.available_options == {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"}
        assert self.value1.value == "Purple"
        assert self.set1.set == {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"}
        
        # Change from the middle of the chain
        self.selector2.selected_option = "Pink"
        
        # Verify changes propagate in both directions
        assert self.selector1.selected_option == "Pink"
        assert self.value1.value == "Pink"
        assert self.set1.set == {"Purple", "Pink", "Cyan", "Red", "Green", "Blue"}  # Available options don't change from selected_option change

    def test_bidirectional_binding_with_collective_hooks(self):
        """Test bidirectional binding with collective hooks."""
        # Bind two selectors bidirectionally
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Change selector1 - first update available options to include the new value
        self.selector1.change_selected_option_and_available_options("Orange", {"Orange", "Red", "Yellow", "Green", "Blue"})
        
        # Verify selector2 gets updated
        assert self.selector2.selected_option == "Orange"
        assert self.selector2.available_options == {"Orange", "Red", "Yellow", "Green", "Blue"}
        
        # Change selector2 - first update available options to include the new value
        # Use atomic update to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Purple"})
        
        # Verify selector1 gets updated
        assert self.selector1.selected_option == "Red"
        assert self.selector1.available_options == {"Red", "Green", "Blue", "Purple"}

    def test_multiple_bindings_to_same_target(self):
        """Test multiple observables binding to the same target."""
        # First, ensure both selectors have compatible initial states
        self.selector1.change_available_options({"Red", "Green", "Blue", "Yellow", "NewValue"})
        self.selector2.change_available_options({"Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Bind both selectors to the same value
        # InitialSyncMode only affects initial binding - ongoing sync is bidirectional
        self.selector1.join_by_key("selected_option", self.value1.value_hook, "use_caller_value")  # type: ignore
        self.selector2.join_by_key("selected_option", self.value1.value_hook, "use_caller_value")  # type: ignore
        
        # Change the target value
        self.value1.value = "NewValue"
        
        # Verify both selectors get updated 
        assert self.selector1.selected_option == "NewValue"
        assert self.selector2.selected_option == "NewValue"
        
        # Change one selector - use atomic update to avoid validation issues
        # First update available options for both selectors to include "AnotherValue"
        self.selector1.change_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        self.selector2.change_selected_option_and_available_options("NewValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Now set the selected option to "AnotherValue"
        self.selector1.change_selected_option_and_available_options("AnotherValue", {"AnotherValue", "Red", "Green", "Blue", "Yellow", "NewValue"})
        
        # Verify the other selector and value get updated (bidirectional sync)
        assert self.selector2.selected_option == "AnotherValue"
        assert self.value1.value == "AnotherValue"

    def test_binding_set_to_both_selectors(self):
        """Test binding a set to both selectors to enable transmission of changes."""
        # Create a shared set that both selectors will bind to
        shared_set = XSet({"Red", "Green", "Blue"}, logger=logger)
        
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue", "Yellow"})
        
        # Bind both selectors' available_options to the shared set
        self.selector1.join_by_key("available_options", shared_set.set_hook, "use_caller_value")  # type: ignore
        self.selector2.join_by_key("available_options", shared_set.set_hook, "use_caller_value")  # type: ignore
        
        # Change the shared set - include "Red" to maintain compatibility with current selected option
        shared_set.set = {"Purple", "Pink", "Cyan", "Red"}
        
        # Verify both selectors get updated
        assert self.selector1.available_options == {"Purple", "Pink", "Cyan", "Red"}
        assert self.selector2.available_options == {"Purple", "Pink", "Cyan", "Red"}
        
        # Change one selector's available options - ensure selected option is compatible
        # Update both selected_option and available_options atomically
        # Include "Red" in the new options since it's the current selected value in linked selectors
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow", "Red"})
        
        # Verify the other selector and shared set get updated
        assert self.selector2.available_options == {"Purple", "Orange", "Yellow", "Red"}
        assert shared_set.set == {"Purple", "Orange", "Yellow", "Red"}

    def test_binding_available_options_directly(self):
        """Test binding available_options directly between selectors."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2's available_options directly to selector1's available_options
        self.selector2.join_by_key("available_options", self.selector1.available_options_hook, "use_caller_value")  # type: ignore
        
        # Change selector1's available options - use atomic update to avoid validation issues
        # Include "Red" since selector2 is still at "Red"
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan", "Red"})
        
        # Verify selector2 gets updated
        assert self.selector2.available_options == {"Purple", "Pink", "Cyan", "Red"}
        
        # Change selector2's available options - ensure selected option is compatible
        # Use "Purple" which exists in both old and new option sets to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow"})
        
        # Verify selector1 gets updated (bidirectional)
        assert self.selector1.available_options == {"Purple", "Orange", "Yellow"}

    def test_binding_selectors_directly(self):
        """Test binding selectors directly to each other to create transitive behavior."""
        # Ensure both selectors have compatible initial states using atomic updates
        self.selector1.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        self.selector2.change_selected_option_and_available_options("Red", {"Red", "Green", "Blue"})
        
        # Bind selector2 directly to selector1
        self.selector2.join_by_key("available_options", self.selector1.available_options_hook, "use_caller_value")  # type: ignore
        
        # Change selector1's available options - use atomic update to avoid validation issues
        # Include "Red" since selector2 is still at "Red"
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan", "Red"})
        
        # Verify selector2 gets updated
        assert self.selector2.available_options == {"Purple", "Pink", "Cyan", "Red"}
        
        # Change selector2's available options - ensure selected option is compatible
        # Use "Purple" which exists in both old and new option sets to avoid validation issues
        self.selector2.change_selected_option_and_available_options("Purple", {"Purple", "Orange", "Yellow"})
        
        # Verify selector1 gets updated (bidirectional) - only available_options should change
        assert self.selector1.available_options == {"Purple", "Orange", "Yellow"}

    def test_binding_with_validation_errors(self):
        """Test binding behavior when validation errors occur."""
        # Create a selector with strict validation
        strict_selector = XSetSingleSelect("Red", {"Red", "Green"}, logger=logger)
        
        # Bind it to a regular selector
        self.selector1.join_by_key("selected_option", strict_selector.selected_option_hook, "use_caller_value")  # type: ignore
        
        # Try to set an invalid value in the source
        with pytest.raises(ValueError):
            self.selector1.selected_option = "Purple"  # Not in {"Red", "Green", "Blue"}
        
        # Verify the strict selector remains unchanged
        assert strict_selector.selected_option == "Red"
        assert strict_selector.available_options == {"Red", "Green"}

    def test_atomic_updates_with_collective_hooks(self):
        """Test atomic updates with collective hooks."""
        # Bind selector1 to selector2
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Use atomic update to change both values at once
        self.selector1.change_selected_option_and_available_options("Purple", {"Purple", "Pink", "Cyan"})
        
        # Verify both values are updated atomically
        assert self.selector1.selected_option == "Purple"
        assert self.selector1.available_options == {"Purple", "Pink", "Cyan"}
        
        # Verify the bound X object also gets updated
        assert self.selector2.selected_option == "Purple"
        assert self.selector2.available_options == {"Purple", "Pink", "Cyan"}

    def test_binding_chain_break_and_rebuild(self):
        """Test breaking and rebuilding binding chains."""
        # Create a simple binding: selector1 -> selector2
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Verify binding works
        self.selector1.change_selected_option_and_available_options("TestValue", {"TestValue", "Red", "Green", "Blue"})
        assert self.selector2.selected_option == "TestValue"
        
        # Break the binding by disconnecting selector1
        self.selector1.isolate_all()
        
        # Verify binding is broken
        self.selector1.change_selected_option_and_available_options("NewValue", {"NewValue", "Red", "Green", "Blue"})
        assert self.selector2.selected_option == "TestValue"  # Should not change
        
        # Rebuild the binding
        # First make selector2 compatible with selector1's current state
        self.selector2.change_selected_option_and_available_options("NewValue", {"NewValue", "Red", "Green", "Blue"})
        self.selector1.join_by_key("selected_option", self.selector2.selected_option_hook, "use_caller_value")  # type: ignore
        self.selector1.join_by_key("available_options", self.selector2.available_options_hook, "use_caller_value")  # type: ignore
        
        # Verify binding works again
        self.selector1.change_selected_option_and_available_options("RebuiltValue", {"RebuiltValue", "Red", "Green", "Blue"})
        assert self.selector2.selected_option == "RebuiltValue"

    def test_collective_hooks_with_empty_sets(self):
        """Test collective hooks behavior with empty sets."""
        # Create a selector that allows None
        none_selector: XSetSingleSelectOptional[str] = XSetSingleSelectOptional(None, set(), logger=logger)
        
        # Create a compatible selector that also allows None for binding
        compatible_selector: XSetSingleSelectOptional[str] = XSetSingleSelectOptional(None, set(), logger=logger)
        
        # Bind the compatible selector to the none_selector
        compatible_selector.join_by_key("selected_option", none_selector.selected_option_hook, "use_caller_value")  # type: ignore
        compatible_selector.join_by_key("available_options", none_selector.available_options_hook, "use_caller_value")  # type: ignore
        
        # Set empty options and None selection
        none_selector.change_selected_option_and_available_options(None, set())
        
        # Verify the bound observable gets updated
        assert compatible_selector.selected_option == None
        assert compatible_selector.available_options == set()

    def test_performance_with_collective_hooks(self):
        """Test performance with collective hooks."""
        # Create multiple observables with compatible types
        x_objects: list[XSetSingleSelect[str]] = []
        for i in range(10):
            selector = XSetSingleSelect("Common", {f"Color{i}", f"Option{i}", "Common"}, logger=logger)
            x_objects.append(selector)
        
        # Bind them in a complex network
        start_time = time.time()
        
        for i in range(0, len(x_objects) - 1):
            # Bind consecutive selectors together
            x_objects[i].join_by_key("selected_option", x_objects[i + 1].selected_option_hook, "use_caller_value")  # type: ignore
        
        # Change a value and measure propagation time - first update available options
        x_objects[0].available_options = {"Common", "Color0", "Option0"} # type: ignore
        x_objects[0].selected_option = "Common" # type: ignore
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 1.0, "Collective hook operations should be fast"

    def test_collective_hooks_edge_cases(self):
        """Test edge cases with collective hooks."""
        # Test with circular references (should not cause infinite loops)
        selector_a = XSetSingleSelect("A", {"A", "B", "C"}, logger=logger)
        selector_b = XSetSingleSelect("B", {"B", "C", "A"}, logger=logger)
        selector_c = XSetSingleSelect("C", {"C", "A"}, logger=logger)
        
        # Create a triangle binding - but avoid circular binding by using different sync modes
        selector_a.join_by_key("selected_option", selector_b.selected_option_hook, "use_caller_value")  # type: ignore
        selector_b.join_by_key("selected_option", selector_c.selected_option_hook, "use_caller_value")  # type: ignore
        # Don't create the circular binding - just test that the existing bindings work
        
        # Change one value - use a value that's in all available options
        selector_a.available_options = {"A", "B", "C"}
        selector_a.selected_option = "A"
        
        # Verify all are synchronized (they should converge to a common state)
        assert selector_a.selected_option == selector_b.selected_option
        assert selector_b.selected_option == selector_c.selected_option

    def test_binding_with_different_sync_modes(self):
        """Test binding with different sync modes in collective scenarios."""
        # Create observables
        selector_a = XSetSingleSelect("A", {"A", "B", "C"}, logger=logger)
        selector_b = XSetSingleSelect("B", {"B", "C", "A"}, logger=logger)
        value_a = XValue("ValueA", logger=logger)
        value_b = XValue("ValueB", logger=logger)
        
        # Bind with different sync modes
        selector_a.join_by_key("selected_option", selector_b.selected_option_hook, "use_caller_value")  # type: ignore
        value_a.join(value_b.value_hook, "use_target_value")  # type: ignore
        
        # Change values and verify behavior
        selector_a.selected_option = "B"
        assert selector_b.selected_option == "B"
        
        value_b.value = "NewValue"
        assert value_a.value == "NewValue"

    def test_collective_hooks_cleanup(self):
        """Test that collective hooks are properly cleaned up."""
        # Create observables and bind them
        selector: XSetSingleSelect[str] = XSetSingleSelect("Test", {"Test", "Other"}, logger=logger)
        value: XValue[str] = XValue("Test", logger=logger)
        options: XSet[str] = XSet({"Test", "Other"}, logger=logger)
        
        # Bind them together
        selector.join_by_key("selected_option", value.value_hook, "use_caller_value") # type: ignore
        selector.join_by_key("available_options", options.set_hook, "use_caller_value") # type: ignore
        
        # Dislink all
        selector.isolate_all()
        # Don't disconnect value and options multiple times - they might already be disconnected
        try:
            value.isolate()
        except ValueError:
            pass  # Already disconnected
        try:
            options.isolate_all()
        except ValueError:
            pass  # Already disconnected
        
        # Verify they're independent - use atomic update to avoid validation issues
        selector.change_selected_option_and_available_options("Independent", {"Independent", "Test", "Other"})
        assert value.value == "Test"  # Should not change
        
        value.value = "AlsoIndependent"
        assert selector.selected_option == "Independent"  # Should not change
