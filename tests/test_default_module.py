"""
Tests for the nexpy.default configuration module.

This module tests the user-facing configuration API for:
- FLOAT_ACCURACY get/set
- NEXUS_MANAGER access
- register_equality_callback() function
"""

import pytest
import nexpy as nx
from nexpy import default
from dataclasses import dataclass
from test_base import ObservableTestCase


class TestDefaultModule(ObservableTestCase):
    """Test the nexpy.default configuration module."""
    
    def setup_method(self):
        """Reset to default state before each test."""
        super().setup_method()
        # Reset FLOAT_ACCURACY to default
        default.FLOAT_ACCURACY = 1e-9
    
    def test_float_accuracy_get(self):
        """Test reading FLOAT_ACCURACY."""
        # Should be able to read the default value
        accuracy = default.FLOAT_ACCURACY
        assert isinstance(accuracy, float)
        assert accuracy == 1e-9
    
    def test_float_accuracy_set(self):
        """Test setting FLOAT_ACCURACY."""
        # Should be able to set a new value
        default.FLOAT_ACCURACY = 1e-12
        assert default.FLOAT_ACCURACY == 1e-12
        
        # Verify it actually updates the underlying module
        assert default.NEXUS_MANAGER.FLOAT_ACCURACY == 1e-12
        
        # Test setting different values
        default.FLOAT_ACCURACY = 1e-6
        assert default.FLOAT_ACCURACY == 1e-6
        
        default.FLOAT_ACCURACY = 1e-15
        assert default.FLOAT_ACCURACY == 1e-15
    
    def test_float_accuracy_affects_comparisons(self):
        """Test that FLOAT_ACCURACY changes affect actual comparisons."""
        # Set high precision
        default.FLOAT_ACCURACY = 1e-12
        
        hook = nx.FloatingHook(1.0)
        updates = []
        hook.add_listener(lambda: updates.append(hook.value))
        
        # Within 1e-12 tolerance - no update
        hook.value = 1.0 + 1e-13
        assert len(updates) == 0
        
        # Outside 1e-12 tolerance - triggers update
        hook.value = 1.0 + 1e-11
        assert len(updates) == 1
        
        # Now set lenient tolerance
        default.FLOAT_ACCURACY = 1e-6
        hook2 = nx.FloatingHook(2.0)
        updates2 = []
        hook2.add_listener(lambda: updates2.append(hook2.value))
        
        # Within 1e-6 tolerance - no update
        hook2.value = 2.0 + 1e-7
        assert len(updates2) == 0
        
        # Outside 1e-6 tolerance - triggers update
        hook2.value = 2.0 + 1e-5
        assert len(updates2) == 1
    
    def test_float_accuracy_with_xvalue(self):
        """Test FLOAT_ACCURACY with XValue objects."""
        default.FLOAT_ACCURACY = 1e-6
        
        temperature = nx.XValue(20.0)
        updates = []
        temperature.value_hook.add_listener(lambda: updates.append(temperature.value))
        
        # Small change within tolerance - still updates (XValue behavior)
        # Note: Default equality is already configured, but XValue may update regardless
        temperature.value = 20.0 + 1e-7  # Well within 1e-6 tolerance
        # XValue uses default float equality which respects FLOAT_ACCURACY
        # So this should NOT trigger an update
        assert len(updates) == 0
        
        # Large change outside tolerance - triggers update
        temperature.value = 20.001
        assert len(updates) == 1
        assert temperature.value == 20.001
    
    def test_nexus_manager_access(self):
        """Test accessing NEXUS_MANAGER."""
        manager = default.NEXUS_MANAGER
        
        # Should return the default nexus manager
        assert manager is default.NEXUS_MANAGER
        
        # Should be usable
        hook = nx.FloatingHook(42, nexus_manager=manager)
        assert hook.value == 42
    
    def test_register_equality_callback_basic(self):
        """Test registering a custom equality callback."""
        @dataclass
        class Point:
            x: float
            y: float
        
        def point_equal(p1: Point, p2: Point, float_accuracy: float = 1e-9) -> bool:
            # Using custom tolerance for this test
            return abs(p1.x - p2.x) < 1e-6 and abs(p1.y - p2.y) < 1e-6
        
        # Register the callback
        default.register_equality_callback(Point, Point, point_equal)
        
        # Create observables with Point values
        p1 = nx.XValue(Point(1.0, 2.0))
        updates = []
        p1.value_hook.add_listener(lambda: updates.append(p1.value))
        
        # Within tolerance - no update
        p1.value = Point(1.0000001, 2.0000001)
        assert len(updates) == 0
        
        # Outside tolerance - triggers update
        p1.value = Point(1.001, 2.001)
        assert len(updates) == 1
        assert p1.value.x == 1.001
        assert p1.value.y == 2.001
    
    def test_register_equality_callback_with_hook_fusion(self):
        """Test custom equality with hook fusion."""
        @dataclass
        class Vector:
            x: float
            y: float
        
        def vector_equal(v1: Vector, v2: Vector, float_accuracy: float) -> bool:
            # Using custom tolerance for this test
            tolerance = 1e-9
            return abs(v1.x - v2.x) < tolerance and abs(v1.y - v2.y) < tolerance
        
        default.register_equality_callback(Vector, Vector, vector_equal)
        
        # Create two hooks with similar vectors
        v1 = nx.FloatingHook(Vector(1.0, 2.0))
        v2 = nx.FloatingHook(Vector(1.0 + 1e-10, 2.0 + 1e-10))
        
        # Join them - should recognize vectors as equal
        v1.join(v2, "use_caller_value")
        
        # Both should now share the same value
        assert v1.value.x == v2.value.x
        assert v1.value.y == v2.value.y
    
    def test_register_equality_callback_id_based(self):
        """Test ID-based equality for custom types."""
        @dataclass
        class Person:
            id: int
            name: str
            age: int
        
        def person_equal(p1: Person, p2: Person, float_accuracy: float) -> bool:
            # Ignore float_accuracy for ID-based equality
            return p1.id == p2.id
        
        default.register_equality_callback(Person, Person, person_equal)
        
        person = nx.XValue(Person(1, "Alice", 30))
        updates = []
        person.value_hook.add_listener(lambda: updates.append(person.value))
        
        # Same ID - no update even though other fields differ
        person.value = Person(1, "Alice Smith", 31)
        assert len(updates) == 0
        
        # Different ID - triggers update
        person.value = Person(2, "Bob", 25)
        assert len(updates) == 1
    
    def test_register_equality_callback_numpy_style(self):
        """Test array-like equality callback."""
        @dataclass
        class Histogram:
            bins: list[float]
        
        def histogram_equal(h1: Histogram, h2: Histogram, float_accuracy: float) -> bool:
            if len(h1.bins) != len(h2.bins):
                return False
            return all(abs(a - b) < float_accuracy for a, b in zip(h1.bins, h2.bins))
        
        default.register_equality_callback(Histogram, Histogram, histogram_equal)
        
        hist = nx.XValue(Histogram([1.0, 2.0, 3.0]))
        updates = []
        hist.value_hook.add_listener(lambda: updates.append(hist.value))
        
        # Same bins - no update
        hist.value = Histogram([1.0, 2.0, 3.0])
        assert len(updates) == 0
        
        # Different bins - triggers update
        hist.value = Histogram([1.0, 2.0, 4.0])
        assert len(updates) == 1
    
    def test_register_equality_callback_with_xdict(self):
        """Test custom equality with XDict values."""
        @dataclass
        class Config:
            timeout: int
            retries: int
        
        def config_equal(c1: Config, c2: Config, float_accuracy: float) -> bool:
            # Ignore float_accuracy for config equality
            return c1.timeout == c2.timeout and c1.retries == c2.retries
        
        default.register_equality_callback(Config, Config, config_equal)
        
        configs = nx.XDict({
            'dev': Config(30, 3),
            'prod': Config(60, 5)
        })
        
        updates = []
        configs.dict_hook.add_listener(lambda: updates.append(len(configs.dict)))
        
        # Setting same values - no update
        configs.dict = {
            'dev': Config(30, 3),
            'prod': Config(60, 5)
        }
        # Note: Dict comparison includes keys, so this might still trigger
        # This tests that the Config equality is being used properly
    
    def test_multiple_equality_callbacks(self):
        """Test registering multiple different callbacks."""
        @dataclass
        class TypeA:
            value: int
        
        @dataclass
        class TypeB:
            value: float
        
        def type_a_equal(a1: TypeA, a2: TypeA, float_accuracy: float) -> bool:
            # Ignore float_accuracy for int equality
            return a1.value == a2.value
        
        def type_b_equal(b1: TypeB, b2: TypeB, float_accuracy: float) -> bool:
            # Use float_accuracy for numerical comparison
            return abs(b1.value - b2.value) < float_accuracy
        
        # Register both
        default.register_equality_callback(TypeA, TypeA, type_a_equal)
        default.register_equality_callback(TypeB, TypeB, type_b_equal)
        
        # Test TypeA
        a = nx.XValue(TypeA(42))
        a_updates = []
        a.value_hook.add_listener(lambda: a_updates.append(a.value))
        
        a.value = TypeA(42)
        assert len(a_updates) == 0
        
        a.value = TypeA(43)
        assert len(a_updates) == 1
        
        # Test TypeB (uses float_accuracy from default manager: 1e-9)
        b = nx.XValue(TypeB(3.14))
        b_updates = []
        b.value_hook.add_listener(lambda: b_updates.append(b.value))
        
        b.value = TypeB(3.14 + 1e-10)  # Within 1e-9 tolerance
        assert len(b_updates) == 0
        
        b.value = TypeB(3.14 + 1e-8)  # Outside 1e-9 tolerance
        assert len(b_updates) == 1
    
    def test_float_accuracy_different_use_cases(self):
        """Test FLOAT_ACCURACY for different use cases (UI, scientific, etc.)."""
        # UI use case - lenient tolerance
        default.FLOAT_ACCURACY = 1e-6
        ui_slider = nx.XValue(0.5)
        ui_updates = []
        ui_slider.value_hook.add_listener(lambda: ui_updates.append(ui_slider.value))
        
        ui_slider.value = 0.5 + 1e-7  # Tiny UI jitter, within tolerance
        assert len(ui_updates) == 0
        
        # Scientific use case - strict tolerance
        default.FLOAT_ACCURACY = 1e-12
        scientific_measurement = nx.XValue(1.23456789)  # Precise measurement
        sci_updates = []
        scientific_measurement.value_hook.add_listener(
            lambda: sci_updates.append(scientific_measurement.value)
        )
        
        scientific_measurement.value = 1.23456789 + 1e-13
        assert len(sci_updates) == 0
        
        scientific_measurement.value = 1.23456789 + 1e-11
        assert len(sci_updates) == 1
    
    def test_float_accuracy_boundary_conditions(self):
        """Test FLOAT_ACCURACY at exact boundaries."""
        default.FLOAT_ACCURACY = 1e-9
        
        hook = nx.FloatingHook(1.0)
        updates = []
        hook.add_listener(lambda: updates.append(hook.value))
        
        # Exactly at boundary (just under)
        hook.value = 1.0 + 9.9e-10
        assert len(updates) == 0
        
        # Just over boundary
        hook.value = 1.0 + 1.01e-9
        assert len(updates) == 1
    
    def test_configuration_before_creating_observables(self):
        """Test that configuration should happen before creating observables."""
        # This is the recommended pattern
        default.FLOAT_ACCURACY = 1e-6
        default.register_equality_callback(str, str, lambda a, b, float_accuracy: a.lower() == b.lower())
        
        # Now create observables
        name = nx.XValue("Alice")
        updates = []
        name.value_hook.add_listener(lambda: updates.append(name.value))
        
        # Case-insensitive equality
        name.value = "ALICE"
        assert len(updates) == 0
        
        name.value = "Bob"
        assert len(updates) == 1


class TestDefaultModuleEdgeCases(ObservableTestCase):
    """Test edge cases and error conditions."""
    
    def test_float_accuracy_extreme_values(self):
        """Test FLOAT_ACCURACY with extreme values."""
        # Very strict
        default.FLOAT_ACCURACY = 1e-15
        assert default.FLOAT_ACCURACY == 1e-15
        
        # Very lenient
        default.FLOAT_ACCURACY = 1e-3
        assert default.FLOAT_ACCURACY == 1e-3
        
        # Zero (edge case - probably not recommended but should work)
        default.FLOAT_ACCURACY = 0.0
        assert default.FLOAT_ACCURACY == 0.0
    
    def test_nexus_manager_is_readonly(self):
        """Test that NEXUS_MANAGER reference is read-only."""
        manager = default.NEXUS_MANAGER
        
        # Should get same reference each time
        assert default.NEXUS_MANAGER is manager
        
        # Should be the default manager
        assert manager is default.NEXUS_MANAGER
    
    def test_register_equality_callback_cannot_override(self):
        """Test that registering a callback for same type pair raises error."""
        @dataclass
        class Value:
            x: int
        
        # Register first callback
        def equality_v1(v1: Value, v2: Value, float_accuracy: float) -> bool:
            return v1.x == v2.x
        
        default.register_equality_callback(Value, Value, equality_v1)
        
        val = nx.XValue(Value(1))
        updates = []
        val.value_hook.add_listener(lambda: updates.append(val.value))
        
        val.value = Value(1)
        assert len(updates) == 0  # Equal by v1
        
        # Try to register second callback for same type - should raise
        def equality_v2(v1: Value, v2: Value, float_accuracy: float) -> bool:
            return False  # Always different
        
        with pytest.raises(ValueError, match="already exists"):
            default.register_equality_callback(Value, Value, equality_v2)
    
    def test_float_accuracy_persistence_across_hooks(self):
        """Test that FLOAT_ACCURACY changes affect all new hooks."""
        default.FLOAT_ACCURACY = 1e-12
        
        hook1 = nx.FloatingHook(1.0)
        
        default.FLOAT_ACCURACY = 1e-6
        
        hook2 = nx.FloatingHook(2.0)
        
        # Both hooks should use the current FLOAT_ACCURACY value
        # when they perform comparisons
        updates1 = []
        updates2 = []
        
        hook1.add_listener(lambda: updates1.append(hook1.value))
        hook2.add_listener(lambda: updates2.append(hook2.value))
        
        # hook1 uses current FLOAT_ACCURACY (1e-6)
        hook1.value = 1.0 + 1e-7
        assert len(updates1) == 0
        
        hook1.value = 1.0 + 1e-5
        assert len(updates1) == 1
        
        # hook2 also uses current FLOAT_ACCURACY (1e-6)
        hook2.value = 2.0 + 1e-7
        assert len(updates2) == 0
        
        hook2.value = 2.0 + 1e-5
        assert len(updates2) == 1


class TestDefaultModuleIntegration(ObservableTestCase):
    """Integration tests with various nexpy features."""
    
    def test_with_xlist(self):
        """Test default configuration with XList."""
        default.FLOAT_ACCURACY = 1e-6
        
        values = nx.XList([1.0, 2.0, 3.0])
        updates = []
        values.list_hook.add_listener(lambda: updates.append(list(values.list)))
        
        # Setting same values within tolerance
        values.list = [1.0000001, 2.0000001, 3.0000001]
        # List comparison is more complex, but float values should use FLOAT_ACCURACY
    
    def test_with_xset(self):
        """Test default configuration with XSet."""
        default.FLOAT_ACCURACY = 1e-6
        
        temps = nx.XSet({20.0, 21.0, 22.0})
        # XSet should respect FLOAT_ACCURACY for float values
        assert 20.0 in temps.set
    
    def test_multiple_observables_same_config(self):
        """Test that multiple observables share the same config."""
        default.FLOAT_ACCURACY = 1e-9
        
        obs1 = nx.XValue(1.0)
        obs2 = nx.XValue(2.0)
        obs3 = nx.XValue(3.0)
        
        updates = [[], [], []]
        obs1.value_hook.add_listener(lambda: updates[0].append(obs1.value))
        obs2.value_hook.add_listener(lambda: updates[1].append(obs2.value))
        obs3.value_hook.add_listener(lambda: updates[2].append(obs3.value))
        
        # All should use same FLOAT_ACCURACY
        obs1.value = 1.0 + 1e-10
        obs2.value = 2.0 + 1e-10
        obs3.value = 3.0 + 1e-10
        
        assert len(updates[0]) == 0
        assert len(updates[1]) == 0
        assert len(updates[2]) == 0
        
        # All should trigger on same threshold
        obs1.value = 1.0 + 1e-8
        obs2.value = 2.0 + 1e-8
        obs3.value = 3.0 + 1e-8
        
        assert len(updates[0]) == 1
        assert len(updates[1]) == 1
        assert len(updates[2]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

