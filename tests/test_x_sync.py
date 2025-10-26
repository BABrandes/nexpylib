from typing import Any, Optional, Self, Mapping
from logging import basicConfig, getLogger, DEBUG

import pytest

from nexpy import XFunction, XValue, FunctionValues
from nexpy import XBase
from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook as OwnedHook

basicConfig(level=DEBUG)
logger = getLogger(__name__)

class MockObservable(XBase[str, int]):
    """Mock observable that implements the required interface."""
    
    def __init__(self, name: str):
        self.name = name
        self._hooks: dict[str, OwnedHook[int, Self]] = {}
        
        # Initialize BaseCarriesHooks
        super().__init__()
        
        # Attach hooks to the mock observable
        for key, hook in self._hooks.items():
            hook._owner = self  # type: ignore
    
    def _get_hook_by_key(self, key: str) -> OwnedHook[int, Self]:
        return self._hooks[key]
    
    def _get_value_by_key(self, key: str) -> int:
        return self._hooks[key].value
    
    def _get_hook_keys(self) -> set[str]:
        return set(self._hooks.keys())
    
    def _get_key_by_hook_or_nexus(self, hook_or_nexus: Any) -> str:
        for key, hook in self._hooks.items():
            if hook is hook_or_nexus or hook._get_nexus() is hook_or_nexus:  # type: ignore
                return key
        raise ValueError(f"Hook {hook_or_nexus} not found")
    
    def add_hook(self, key: str, hook: OwnedHook[int, Self]) -> None:
        """Add a hook to the mock observable."""
        self._hooks[key] = hook

    def get_values_for_serialization(self) -> Mapping[str, int]:
        return {key: hook._get_value() for key, hook in self._hooks.items()} # type: ignore
    
    def set_values_from_serialization(self, values: Mapping[str, int]) -> None:
        values_to_submit: dict[str, int] = {}
        for key, value in values.items():
            values_to_submit[key] = value
        self._submit_values(values_to_submit)


class TestXFunction:
    """Test XFunction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_owner = MockObservable("test_owner")

    def test_basic_creation_with_values(self):
        """Test basic XFunction creation with initial values."""
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through valid values."""
            # Just return the submitted values as-is
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 5, "b": 3, "c": 0},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created correctly
        assert sync.hook("a").value == 5  # Original value
        assert sync.hook("b").value == 3  # Original value
        assert sync.hook("c").value == 0   # Original value

        # Check hook keys
        assert sync.keys() == {"a", "b", "c"}

    def test_basic_creation_with_hooks(self):
        """Test basic XFunction creation with initial values (no longer supports hooks)."""
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through values."""
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 10, "b": 20},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Check that sync hooks were created with initial values
        assert sync.hook("a").value == 10  # Original value
        assert sync.hook("b").value == 20  # Original value

    def test_hook_access_methods(self):
        """Test hook access methods."""
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 5, "b": 10},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Test _get_hook
        hook_a = sync.hook("a")
        assert hook_a.value == 5

        # Test _get_value_reference_of_hook
        value_a = sync.value("a")
        assert value_a == 5

        # Test _get_hook_key
        hook_key = sync.key(hook_a)
        assert hook_key == "a"

        # Test error cases
        with pytest.raises(ValueError):
            sync.hook("nonexistent")

        with pytest.raises(ValueError):
            sync.value("nonexistent")

    def test_basic_sync(self):
        """Test basic XFunction with simple pass-through callback."""
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 5, "b": 10},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Should have sync hooks
        assert sync.keys() == {"a", "b"}
        assert len(sync.hooks()) == 2

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty sync hooks
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={},
            completing_function_callable=sync_callback,
            logger=logger
        )

        assert sync.keys() == set()

        # None values
        def sync_callback_with_none(values: FunctionValues[str, Optional[int]]) -> tuple[bool, dict[str, Optional[int]]]:
            return (True, dict(values.submitted))

        sync_with_none = XFunction[str, Optional[int]](
            complete_variables_per_key={"a": None, "b": 5},
            completing_function_callable=sync_callback_with_none,
            logger=logger
        )

        assert sync_with_none.hook("a").value is None
        assert sync_with_none.hook("b").value == 5


    def test_listener_notification(self):
        """Test that listeners are notified when values change."""
        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 5},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Add a listener
        notifications: list[str] = []
        def listener():
            notifications.append("notified")

        sync.add_listener(listener)

        # Change a value
        sync.hook("a").change_value(10)

        # Check that listener was notified
        assert len(notifications) > 0

    def test_integration_with_observable_single_value(self):
        """Test integration with XValue by connecting after initialization."""
        # Create external observables
        external_a = XValue[int](5, logger=logger)
        external_b = XValue[int](10, logger=logger)

        def sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            """Simple sync callback that passes through values."""
            return (True, dict(values.submitted))

        sync = XFunction[str, int](
            complete_variables_per_key={"a": 5, "b": 10},
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Check initial state
        assert sync.hook("a").value == 5  # Original value
        assert sync.hook("b").value == 10  # Original value

        # Now connect to external observables after initialization
        sync.hook("a").join(external_a.value_hook, "use_caller_value")
        sync.hook("b").join(external_b.value_hook, "use_caller_value")

        # Check that external values are updated to match sync values
        assert external_a.value == 5  # Matches sync value
        assert external_b.value == 10  # Matches sync value

    def test_combination_validation(self):
        """Test that sync callback is validated with every combination of given values."""
        def valid_sync_callback(values: FunctionValues[str, int]) -> tuple[bool, dict[str, int]]:
            """Valid callback that passes through submitted values."""
            return (True, dict(values.submitted))

        # This should work - callback handles all combinations correctly
        sync = XFunction[str, int](
            complete_variables_per_key={"a": 1, "b": 2, "c": 3},
            completing_function_callable=valid_sync_callback,
            logger=logger
        )

        # Check that values are preserved during initialization
        assert sync.hook("a").value == 1  # Original value
        assert sync.hook("b").value == 2  # Original value
        assert sync.hook("c").value == 3  # Original value

    def test_square_root_constraint(self):
        """Test square root constraint - showcases the power of XFunction.
        
        This test demonstrates a mathematical constraint where:
        - square_value = root_value²
        - domain selects between positive and negative root solutions
        
        Any of the three values can be changed, and the others sync automatically.
        """
        def sync_callback(values: FunctionValues[str, float | str]) -> tuple[bool, dict[str, float | str]]:
            """Sync callback that maintains the constraint: square_value = root_value².
            
            Args:
                values: FunctionValues containing submitted (changed) and current (complete state) values
            """
            result: dict[str, float | str] = {}
            
            # Extract submitted values
            root = values.submitted.get("root_value")
            square = values.submitted.get("square_value")
            submitted_domain = values.submitted.get("domain")
            
            # Get current domain from complete current state
            current_domain = values.current.get("domain", "positive")
            
            # When all three values are present (validation mode), check consistency
            if all(k in values.submitted for k in ["root_value", "square_value", "domain"]):
                # Validate that the values are consistent
                if not isinstance(root, (int, float)) or not isinstance(square, (int, float)):
                    return (False, {})
                
                # Check: square = root²
                if abs(square - root * root) > 1e-10:
                    return (False, {})
                
                # Check: domain matches sign of root
                expected_domain = "positive" if root >= 0 else "negative"
                if submitted_domain != expected_domain:
                    return (False, {})
                
                # All consistent, no changes needed
                return (True, {})
            
            # Case 1: root_value was submitted (primary value)
            if "root_value" in values.submitted and isinstance(root, (int, float)):
                # Calculate square from root
                result["square_value"] = root * root
                # Update domain to match the sign of the root
                result["domain"] = "positive" if root >= 0 else "negative"
            
            # Case 2: square_value was submitted (use current or submitted domain)
            elif "square_value" in values.submitted:
                if not isinstance(square, (int, float)):
                    return (False, {})
                if square < 0:
                    return (False, {})  # Invalid: can't take square root of negative number
                
                # Use submitted domain if provided, otherwise use current domain
                domain_to_use = submitted_domain if submitted_domain is not None else current_domain
                
                sqrt_val = square ** 0.5
                # Use domain to determine the sign of the root
                result["root_value"] = -sqrt_val if domain_to_use == "negative" else sqrt_val
            
            # Case 3: Only domain was submitted
            elif "domain" in values.submitted:
                # Can't change domain without knowing current root
                # Return no changes; this will be checked during validation
                pass
            
            return (True, result)

        # Create XFunction with initial valid state
        # Initial state: √4 = 2 (positive domain)
        sync = XFunction[str, float | str](
            complete_variables_per_key= {
                "square_value": 4.0,
                "root_value": 2.0,
                "domain": "positive"
            },
            completing_function_callable=sync_callback,
            logger=logger
        )

        # Verify initial state
        assert sync.hook("square_value").value == 4.0
        assert sync.hook("root_value").value == 2.0
        assert sync.hook("domain").value == "positive"

        # Test 1: Change root_value → square_value should update
        sync.hook("root_value").change_value(3.0)
        assert sync.hook("square_value").value == 9.0  # 3² = 9
        assert sync.hook("root_value").value == 3.0
        assert sync.hook("domain").value == "positive"  # Still positive

        # Test 2: Change root_value to negative → domain should update
        sync.hook("root_value").change_value(-4.0)
        assert sync.hook("square_value").value == 16.0  # (-4)² = 16
        assert sync.hook("root_value").value == -4.0
        assert sync.hook("domain").value == "negative"  # Now negative

        # Test 3: Change to a positive root → square_value and domain should update
        sync.hook("root_value").change_value(5.0)
        assert sync.hook("square_value").value == 25.0  # 5² = 25
        assert sync.hook("root_value").value == 5.0
        assert sync.hook("domain").value == "positive"  # Positive root

        # Test 4: Change square_value alone → root_value should be positive (default)
        sync.hook("square_value").change_value(36.0)
        assert sync.hook("square_value").value == 36.0
        assert sync.hook("root_value").value == 6.0  # √36 = 6 (positive default)
        assert sync.hook("domain").value == "positive"

        # Test 5: Change back to negative root → demonstrates both solutions
        sync.hook("root_value").change_value(-6.0)
        assert sync.hook("square_value").value == 36.0  # (-6)² = 36
        assert sync.hook("root_value").value == -6.0
        assert sync.hook("domain").value == "negative"  # Negative root

        # Test 6: Edge case - square root of 0
        sync.hook("root_value").change_value(0.0)
        assert sync.hook("square_value").value == 0.0
        assert sync.hook("root_value").value == 0.0
        assert sync.hook("domain").value == "positive"  # 0 is considered positive
        
        # Test 7: Large values
        sync.hook("root_value").change_value(-10.0)
        assert sync.hook("square_value").value == 100.0
        assert sync.hook("root_value").value == -10.0
        assert sync.hook("domain").value == "negative"

        # Test 8: Submit multiple values at once - square_value and domain together
        # This demonstrates the power of coordinated updates!
        sync.change_values({
            "square_value": 49.0,
            "domain": "negative"
        })
        assert sync.hook("square_value").value == 49.0
        assert sync.hook("root_value").value == -7.0  # √49 = -7 (negative domain)
        assert sync.hook("domain").value == "negative"

        # Test 9: Submit square_value and domain (positive) together
        sync.change_values({
            "square_value": 64.0,
            "domain": "positive"
        })
        assert sync.hook("square_value").value == 64.0
        assert sync.hook("root_value").value == 8.0  # √64 = 8 (positive domain)
        assert sync.hook("domain").value == "positive"

        # Test 10: Submit all three values at once (they must be consistent)
        sync.change_values({
            "square_value": 81.0,
            "root_value": 9.0,
            "domain": "positive"
        })
        assert sync.hook("square_value").value == 81.0
        assert sync.hook("root_value").value == 9.0
        assert sync.hook("domain").value == "positive"

        # Test 11: Submit all three values with negative root
        sync.change_values({
            "square_value": 121.0,
            "root_value": -11.0,
            "domain": "negative"
        })
        assert sync.hook("square_value").value == 121.0
        assert sync.hook("root_value").value == -11.0
        assert sync.hook("domain").value == "negative"

        # Test 12: Try to submit inconsistent values - should fail
        with pytest.raises(ValueError):
            sync.change_values({
                "square_value": 100.0,
                "root_value": 5.0,  # Inconsistent! 5² ≠ 100
                "domain": "positive"
            })
