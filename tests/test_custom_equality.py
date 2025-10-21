"""
Tests for custom equality checks in NexPy.

Based on the documentation in docs/usage.md and docs/api_reference.md.
"""

import nexpy as nx
from typing import Mapping
from nexpy.core.nexus_system.nexus_manager import NexusManager
from test_base import ObservableTestCase


class TestCustomEquality(ObservableTestCase):
    """Test custom equality callbacks for different types."""
    
    def test_float_equality_standard_tolerance(self):
        """Test standard 1e-9 tolerance for floating-point equality."""
        # Configure custom equality on test manager
        def float_eq(a: float, b: float, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), float_eq)
        
        hook = nx.FloatingHook(1.0, nexus_manager=self.test_manager)
        update_count = [0]
        
        def on_update():
            update_count[0] += 1
        
        hook.add_listener(on_update)
        
        # Within tolerance - no update
        hook.value = 1.0 + 1e-15
        assert update_count[0] == 0
        
        # Within tolerance - no update
        hook.value = 1.0 + 1e-10
        assert update_count[0] == 0
        
        # Exceeds tolerance - triggers update
        hook.value = 1.0 + 1e-8
        assert update_count[0] == 1
    
    def test_float_equality_xvalue(self):
        """Test float equality with XValue objects."""
        def float_eq(a: float, b: float, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), float_eq)
        
        temperature = nx.XValue(20.0, nexus_manager=self.test_manager)
        updates: list[float] = []
        temperature.value_hook.add_listener(lambda: updates.append(temperature.value))
        
        # No update for tiny differences
        temperature.value = 20.0000000001
        assert len(updates) == 0
        
        # Update for significant differences
        temperature.value = 20.001
        assert len(updates) == 1
        assert updates[0] == 20.001
    
    def test_cross_type_float_int_equality(self):
        """Test cross-type equality between float and int."""
        def float_int_eq(a: float, b: int, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), lambda a, b, float_accuracy=1e-9: abs(a - b) < float_accuracy)
        self.test_manager.add_value_equality_callback((float, int), float_int_eq)
        self.test_manager.add_value_equality_callback((int, float), lambda a, b, float_accuracy=1e-9: float_int_eq(b, a, float_accuracy))
        
        value = nx.XValue(10.0, nexus_manager=self.test_manager)
        updates: list[float] = []
        value.value_hook.add_listener(lambda: updates.append(value.value))
        
        # int 10 should be equal to float 10.0
        value.value = 10
        assert len(updates) == 0
        
        # float 10.0 should be equal to int 10
        value.value = 10.0
        assert len(updates) == 0
        
        # Significant difference triggers update
        value.value = 10.5
        assert len(updates) == 1
    
    def test_per_manager_custom_equality(self):
        """Test different equality logic for different managers."""
        # High precision manager
        high_precision = NexusManager()
        high_precision.add_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-12
        )
        
        # Low precision manager
        low_precision = NexusManager()
        low_precision.add_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-6
        )
        
        precise = nx.XValue(1.0, nexus_manager=high_precision)
        rough = nx.XValue(1.0, nexus_manager=low_precision)
        
        precise_updates: list[float] = []
        rough_updates: list[float] = []
        
        precise.value_hook.add_listener(lambda: precise_updates.append(precise.value))
        rough.value_hook.add_listener(lambda: rough_updates.append(rough.value))
        
        # Small change
        delta = 1e-9
        precise.value = 1.0 + delta  # Exceeds 1e-12
        rough.value = 1.0 + delta    # Within 1e-6
        
        assert len(precise_updates) == 1
        assert len(rough_updates) == 0
    
    def test_equality_prevents_unnecessary_updates(self):
        """Test that custom equality prevents unnecessary updates."""
        def float_eq(a: float, b: float, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), float_eq)
        
        # Create a fusion domain
        hook1 = nx.FloatingHook(1.0, nexus_manager=self.test_manager)
        hook2 = nx.FloatingHook(1.0, nexus_manager=self.test_manager)
        hook1.join(hook2, "use_caller_value")
        
        updates_1 = []
        updates_2 = []
        
        hook1.add_listener(lambda: updates_1.append(hook1.value))
        hook2.add_listener(lambda: updates_2.append(hook2.value))
        
        # Tiny change - no updates
        hook1.value = 1.0 + 1e-15
        assert len(updates_1) == 0
        assert len(updates_2) == 0
        
        # Significant change - both updated
        hook1.value = 2.0
        assert len(updates_1) == 1
        assert len(updates_2) == 1
    
    def test_equality_with_validation(self):
        """Test that equality checks happen before validation."""
        def float_eq(a: float, b: float, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), float_eq)
        
        validation_count = [0]
        
        def validate(value: float) -> tuple[bool, str]:
            validation_count[0] += 1
            return True, "Valid"
        
        hook = nx.FloatingHook(1.0, isolated_validation_callback=validate, nexus_manager=self.test_manager)
        
        # Tiny change - validation not called (equality check prevents it)
        hook.value = 1.0 + 1e-15
        assert validation_count[0] == 0
        
        # Significant change - validation called
        hook.value = 2.0
        assert validation_count[0] == 1
    
    def test_equality_with_xdict(self):
        """Test custom equality with XDict."""
        from types import MappingProxyType
        
        def dict_eq(a: Mapping[str, int], b: Mapping[str, int], float_accuracy: float = 1e-9) -> bool:
            # Handle MappingProxyType
            if isinstance(a, MappingProxyType):
                a = dict(a)
            if isinstance(b, MappingProxyType):
                b = dict(b)
            # Consider dicts equal if they have the same keys
            return set(a.keys()) == set(b.keys())
        
        self.test_manager.add_value_equality_callback((dict, dict), dict_eq)
        self.test_manager.add_value_equality_callback((MappingProxyType, MappingProxyType), dict_eq)
        self.test_manager.add_value_equality_callback((dict, MappingProxyType), dict_eq)
        self.test_manager.add_value_equality_callback((MappingProxyType, dict), dict_eq)
        
        config = nx.XDict({"a": 1, "b": 2}, nexus_manager=self.test_manager)
        updates = []
        config.dict_hook.add_listener(lambda: updates.append(len(config.dict)))
        
        # Same keys, different values - considered equal by our custom logic
        config.change_dict({"a": 10, "b": 20})
        assert len(updates) == 0
        
        # Different keys - not equal
        config.change_dict({"a": 1, "c": 3})
        assert len(updates) == 1
    
    def test_remove_equality_callback(self):
        """Test removing custom equality callbacks."""
        def float_eq(a: float, b: float, float_accuracy: float = 1e-9) -> bool:
            return abs(a - b) < float_accuracy
        
        self.test_manager.add_value_equality_callback((float, float), float_eq)
        
        hook = nx.FloatingHook(1.0, nexus_manager=self.test_manager)
        updates = []
        hook.add_listener(lambda: updates.append(hook.value))
        
        # With custom equality - no update
        hook.value = 1.0 + 1e-15
        assert len(updates) == 0
        
        # Remove callback
        self.test_manager.remove_value_equality_callback((float, float))
        
        # Without custom equality - update triggered
        hook.value = 1.0 + 1e-15
        assert len(updates) == 1
    
    def test_replace_equality_callback(self):
        """Test replacing custom equality callbacks."""
        # Start with tight tolerance
        self.test_manager.add_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-12
        )
        
        hook = nx.FloatingHook(1.0, nexus_manager=self.test_manager)
        updates: list[float] = []
        hook.add_listener(lambda: updates.append(hook.value))
        
        # Small change triggers update (exceeds 1e-12)
        hook.value = 1.0 + 1e-10
        assert len(updates) == 1
        
        # Replace with loose tolerance
        self.test_manager.replace_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-6
        )
        
        # Same small change now doesn't trigger update
        hook.value = 1.0 + 1e-10
        assert len(updates) == 1  # Still 1, no new update
    
    def test_equality_callback_exists(self):
        """Test checking if equality callback exists."""
        assert not self.test_manager.exists_value_equality_callback((float, float))
        
        self.test_manager.add_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-9
        )
        
        assert self.test_manager.exists_value_equality_callback((float, float))
        
        self.test_manager.remove_value_equality_callback((float, float))
        
        assert not self.test_manager.exists_value_equality_callback((float, float))
    
    def test_types_of_equality_callbacks(self):
        """Test getting all registered equality callback types."""
        types_before = self.test_manager.types_of_value_equality_callbacks()
        
        self.test_manager.add_value_equality_callback(
            (float, float),
            lambda a, b, float_accuracy: abs(a - b) < 1e-9
        )
        self.test_manager.add_value_equality_callback(
            (int, int),
            lambda a, b, float_accuracy: a == b
        )
        
        types_after = self.test_manager.types_of_value_equality_callbacks()
        
        assert (float, float) in types_after
        assert (int, int) in types_after
        assert len(types_after) == len(types_before) + 2

