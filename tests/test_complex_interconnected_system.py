"""
Complex interconnected reactive system test.

This test demonstrates a sophisticated reactive system with:
1. XDictSelect with 4 letter keys and set values
2. Values connected to XSet through XSetSequenceAdapter
3. Keys sourced from XSetSelect
4. Full reactive updates across the entire system

To run this test:
1. Install dependencies: pip install typing-extensions
2. Install the package: pip install -e .
3. Run: python tests/test_complex_interconnected_system.py
"""

from typing import Set, Dict, List
from collections.abc import Set as AbstractSet

try:
    from nexpy import XDictSelect, XSetSingleSelect, XSet, XSetSequenceAdapter
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install dependencies: pip install typing-extensions")
    print("Then install the package: pip install -e .")
    exit(1)


class TestComplexInterconnectedSystem:
    """Test complex interconnected reactive system with multiple X objects."""
    
    def test_complex_interconnected_system(self):
        """
        Test a complex reactive system with:
        - XDictSelect with 4 letter keys and set values
        - Values connected to XSet through XSetSequenceAdapter
        - Keys sourced from XSetSelect
        - Full reactive updates across the entire system
        """
        
        # Step 1: Create the base dictionary with 4 letter keys and set values
        base_dict: Dict[str, Set[int]] = {
            'A': {1, 2, 3},
            'B': {4, 5, 6},
            'C': {7, 8, 9},
            'D': {10, 11, 12}
        }
        
        # Step 2: Create XSetSelect for managing the dictionary keys
        # This will control which key is selected in the dictionary
        key_selector = XSetSingleSelect[str](
            selected_option='A',  # Start with 'A'
            available_options={'A', 'B', 'C', 'D'}
        )
        
        # Verify initial state
        assert key_selector.selected_option == 'A'
        assert key_selector.available_options == {'A', 'B', 'C', 'D'}
        assert key_selector.number_of_available_options == 4
        
        # Step 3: Create XDictSelect that uses the key from XSetSelect
        # The dictionary values are sets of numbers
        dict_selector = XDictSelect[str, Set[int]](
            dict_hook=base_dict,
            key_hook=key_selector.selected_option_hook  # Connect to the key selector
        )
        
        # Verify initial state
        assert dict_selector.key == 'A'
        assert dict_selector.value == {1, 2, 3}
        assert dict_selector.dict == base_dict
        
        # Step 4: Create XSetSequenceAdapter to connect the dict value to XSet
        # This adapter will convert between set and sequence representations
        set_adapter = XSetSequenceAdapter[int](
            hook_set_or_value=dict_selector.value_hook,  # type: ignore[arg-type]
            hook_sequence=None,
            sort_callable=lambda s: sorted(s)  # Custom sorting for predictable order
        )
        
        # Step 5: Create XSet that receives the adapted value
        reactive_set = XSet[int](
            value=set_adapter.hook_set
        )
        
        # Verify initial interconnected state
        assert reactive_set.set == {1, 2, 3}
        assert set_adapter.hook_sequence.value == [1, 2, 3]  # Sorted sequence
        assert set_adapter.hook_set.value == {1, 2, 3}
        
        # Step 6: Test reactive updates - Change the selected key
        print("Testing key change from 'A' to 'B'...")
        key_selector.change_selected_option('B')
        
        # Verify all components updated reactively
        assert key_selector.selected_option == 'B'
        assert dict_selector.key == 'B'
        assert dict_selector.value == {4, 5, 6}
        assert reactive_set.set == {4, 5, 6}
        assert set_adapter.hook_sequence.value == [4, 5, 6]
        
        # Step 7: Test reactive updates - Change the selected key to 'C'
        print("Testing key change from 'B' to 'C'...")
        key_selector.change_selected_option('C')
        
        # Verify all components updated reactively
        assert key_selector.selected_option == 'C'
        assert dict_selector.key == 'C'
        assert dict_selector.value == {7, 8, 9}
        assert reactive_set.set == {7, 8, 9}
        assert set_adapter.hook_sequence.value == [7, 8, 9]
        
        # Step 8: Test reactive updates - Change the selected key to 'D'
        print("Testing key change from 'C' to 'D'...")
        key_selector.change_selected_option('D')
        
        # Verify all components updated reactively
        assert key_selector.selected_option == 'D'
        assert dict_selector.key == 'D'
        assert dict_selector.value == {10, 11, 12}
        assert reactive_set.set == {10, 11, 12}
        assert set_adapter.hook_sequence.value == [10, 11, 12]
        
        # Step 9: Test modifying the reactive set directly
        print("Testing direct modification of reactive set...")
        reactive_set.add(13)
        
        # Verify the change propagated back through the adapter to the dict
        assert reactive_set.set == {10, 11, 12, 13}
        assert dict_selector.value == {10, 11, 12, 13}
        assert set_adapter.hook_sequence.value == [10, 11, 12, 13]
        
        # Step 10: Test modifying the dict value directly
        print("Testing direct modification of dict value...")
        dict_selector.change_value({14, 15, 16})
        
        # Verify the change propagated through the adapter to the set
        assert dict_selector.value == {14, 15, 16}
        assert reactive_set.set == {14, 15, 16}
        assert set_adapter.hook_sequence.value == [14, 15, 16]
        
        # Step 11: Test adding new key to the key selector
        print("Testing addition of new key 'E'...")
        key_selector.add_available_option('E')
        
        # Update the base dictionary to include the new key
        base_dict['E'] = {17, 18, 19}
        dict_selector.change_dict(base_dict)
        
        # Change to the new key
        key_selector.change_selected_option('E')
        
        # Verify all components updated reactively
        assert key_selector.selected_option == 'E'
        assert dict_selector.key == 'E'
        assert dict_selector.value == {17, 18, 19}
        assert reactive_set.set == {17, 18, 19}
        assert set_adapter.hook_sequence.value == [17, 18, 19]
        
        # Step 12: Test complex operations on the reactive set
        print("Testing complex set operations...")
        
        # Test union operation
        reactive_set.update({20, 21})
        assert reactive_set.set == {17, 18, 19, 20, 21}
        assert dict_selector.value == {17, 18, 19, 20, 21}
        
        # Test intersection operation
        reactive_set.intersection_update({17, 18, 19, 22, 23})
        assert reactive_set.set == {17, 18, 19}
        assert dict_selector.value == {17, 18, 19}
        
        # Test difference operation
        reactive_set.difference_update({18})
        assert reactive_set.set == {17, 19}
        assert dict_selector.value == {17, 19}
        
        # Step 13: Test edge cases and error conditions
        print("Testing edge cases...")
        
        # Test removing a key from available options (change selection first)
        key_selector.change_selected_option('A')  # Change away from 'E' first
        key_selector.remove_available_option('E')
        assert 'E' not in key_selector.available_options
        
        # Test trying to select a non-existent key (should raise error)
        try:
            key_selector.change_selected_option('Z')
            assert False, "Expected an error when selecting non-existent key"
        except Exception:
            pass  # Expected error
        
        # Test trying to select a removed key (should raise error)
        try:
            key_selector.change_selected_option('E')
            assert False, "Expected an error when selecting removed key"
        except Exception:
            pass  # Expected error
        
        # Step 14: Test the adapter's sequence validation
        print("Testing adapter sequence validation...")
        
        # Test that the adapter correctly handles set-to-sequence conversion
        test_set = {1, 3, 2, 5, 4}
        set_adapter.submit_values_by_keys({"left": test_set})
        assert set_adapter.hook_sequence.value == [1, 2, 3, 4, 5]  # Sorted
        
        # Test that the adapter rejects sequences with duplicates
        try:
            set_adapter.submit_values_by_keys({"right": [1, 2, 2, 3]})
            assert False, "Expected an error when submitting sequence with duplicates"
        except Exception:
            pass  # Expected error
        
        # Step 15: Test the complete system state
        print("Testing final system state...")
        
        # Verify the current state is consistent across all components
        current_key = key_selector.selected_option
        current_dict_value = dict_selector.value
        current_set_value = reactive_set.set
        current_adapter_set = set_adapter.hook_set.value
        current_adapter_sequence = set_adapter.hook_sequence.value
        
        assert current_dict_value == current_set_value
        assert current_set_value == current_adapter_set
        assert set(current_adapter_sequence) == current_adapter_set
        assert current_key in key_selector.available_options
        assert current_key in dict_selector.dict
        
        print(f"Final system state:")
        print(f"  Selected key: {current_key}")
        print(f"  Dict value: {current_dict_value}")
        print(f"  Set value: {current_set_value}")
        print(f"  Adapter sequence: {current_adapter_sequence}")
        print(f"  Available keys: {key_selector.available_options}")
        
        # Step 16: Test performance with rapid changes
        print("Testing rapid changes...")
        
        # Rapidly change between keys to test system stability
        for key in ['A', 'B', 'C', 'D']:
            if key in key_selector.available_options:
                key_selector.change_selected_option(key)
                assert dict_selector.key == key
                assert reactive_set.set == dict_selector.value
        
        print("Complex interconnected system test completed successfully!")
    
    def test_complex_system_with_custom_adapters(self):
        """
        Test the complex system with custom adapter configurations.
        """
        
        # Create a custom sorting function that reverses the order
        def reverse_sort(s: AbstractSet[int]) -> List[int]:
            return sorted(s, reverse=True)
        
        # Set up the system with custom adapter
        base_dict = {'X': {1, 2, 3}, 'Y': {4, 5, 6}}
        
        key_selector = XSetSingleSelect[str](
            selected_option='X',
            available_options={'X', 'Y'}
        )
        
        dict_selector = XDictSelect[str, Set[int]](
            dict_hook=base_dict,
            key_hook=key_selector.selected_option_hook
        )
        
        # Use custom sorting in the adapter
        set_adapter = XSetSequenceAdapter[int](
            hook_set_or_value=dict_selector.value_hook,  # type: ignore[arg-type]
            hook_sequence=None,
            sort_callable=reverse_sort
        )
        
        reactive_set = XSet[int](value=set_adapter.hook_set)
        
        # Test that custom sorting works
        assert reactive_set.set == {1, 2, 3}
        assert set_adapter.hook_sequence.value == [3, 2, 1]  # Reverse sorted
        
        # Change key and verify custom sorting persists
        key_selector.change_selected_option('Y')
        assert reactive_set.set == {4, 5, 6}
        assert set_adapter.hook_sequence.value == [6, 5, 4]  # Reverse sorted
        
        print("Custom adapter test completed successfully!")
    
    def test_complex_system_error_handling(self):
        """
        Test error handling in the complex interconnected system.
        """
        
        base_dict = {'A': {1, 2, 3}}
        
        key_selector = XSetSingleSelect[str](
            selected_option='A',
            available_options={'A'}
        )
        
        dict_selector = XDictSelect[str, Set[int]](
            dict_hook=base_dict,
            key_hook=key_selector.selected_option_hook
        )
        
        set_adapter = XSetSequenceAdapter[int](
            hook_set_or_value=dict_selector.value_hook,  # type: ignore[arg-type]
            hook_sequence=None
        )
        
        _ = XSet[int](value=set_adapter.hook_set)
        
        # Test error when trying to select non-existent key
        try:
            key_selector.change_selected_option('B')
            assert False, "Expected an error when selecting non-existent key"
        except Exception:
            pass  # Expected error
        
        # Test error when trying to submit invalid sequence to adapter
        try:
            set_adapter.submit_values_by_keys({"right": [1, 2, 2, 3]})  # Duplicates
            assert False, "Expected an error when submitting sequence with duplicates"
        except Exception:
            pass  # Expected error
        
        # Test error when trying to change dict to invalid state
        try:
            dict_selector.change_dict({'B': {4, 5, 6}})  # Key 'A' not in new dict
            assert False, "Expected an error when changing dict to invalid state"
        except Exception:
            pass  # Expected error
        
        print("Error handling test completed successfully!")


if __name__ == "__main__":
    # Run the test
    test_instance = TestComplexInterconnectedSystem()
    test_instance.test_complex_interconnected_system()
    test_instance.test_complex_system_with_custom_adapters()
    test_instance.test_complex_system_error_handling()
    print("All complex interconnected system tests passed!")
