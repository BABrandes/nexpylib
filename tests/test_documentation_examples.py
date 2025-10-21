"""
Tests that verify examples from the documentation work correctly.

Based on examples in README.md, docs/usage.md, and docs/examples.md.
"""

import pytest
import nexpy as nx
from test_base import ObservableTestCase


class TestREADMEExamples(ObservableTestCase):
    """Test examples from README.md."""
    
    def test_transitive_synchronization_example(self):
        """Test the transitive synchronization example from README."""
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(2)
        C = nx.FloatingHook(3)
        D = nx.FloatingHook(4)
        
        # Create first fusion domain
        A.join(B, "use_caller_value")
        
        # Create second fusion domain
        C.join(D, "use_caller_value")
        
        # Fuse both domains
        B.join(C, "use_caller_value")
        
        # All four hooks now share the same Nexus
        assert A.value == B.value == C.value == D.value
        
        # Changing any hook updates all hooks
        A.value = 42
        assert B.value == 42
        assert C.value == 42
        assert D.value == 42
    
    def test_hook_isolation_example(self):
        """Test the isolation example from README."""
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(1)
        C = nx.FloatingHook(1)
        
        A.join(B, "use_caller_value")
        B.join(C, "use_caller_value")
        
        # Isolate B
        B.isolate()
        
        # A and C still joined, B is independent
        A.value = 10
        assert A.value == 10
        assert B.value == 1
        assert C.value == 10
    
    def test_simple_reactive_value(self):
        """Test simple reactive value example."""
        temperature = nx.XValue(20.0)
        
        assert temperature.value == 20.0
        
        temperature.value = 25.5
        assert temperature.value == 25.5
    
    def test_hook_fusion_across_objects(self):
        """Test hook fusion across independent objects."""
        sensor_reading = nx.XValue(20.0)
        display_value = nx.XValue(0.0)
        
        sensor_reading.value_hook.join(display_value.value_hook, "use_caller_value")
        
        assert sensor_reading.value == display_value.value
        
        sensor_reading.value = 25.5
        assert display_value.value == 25.5
    
    def test_reactive_list_example(self):
        """Test reactive list example."""
        numbers = nx.XList([1, 2, 3])
        
        assert numbers.list == [1, 2, 3]
        assert numbers.length == 3
        
        numbers.append(4)
        assert numbers.list == [1, 2, 3, 4]
        assert numbers.length == 4
    
    def test_reactive_dict_example(self):
        """Test reactive dictionary example."""
        config = nx.XDict({"debug": False, "version": "1.0"})
        
        config["debug"] = True
        assert config.dict == {"debug": True, "version": "1.0"}
    
    def test_xdict_select_example(self):
        """Test XDictSelect example from README."""
        options = nx.XDictSelect(
            dict_hook={"low": 1, "medium": 5, "high": 10},
            key_hook="medium",
            value_hook=None
        )
        
        assert options.key == "medium"
        assert options.value == 5
        
        # Change key → value automatically updated
        options.change_key("high")
        assert options.value == 10
        
        # Change value → dict automatically updated
        options.change_value(15)
        assert options.dict_hook.value["high"] == 15
    
    def test_listener_example(self):
        """Test listener example."""
        counter = nx.XValue(0)
        updates: list[int] = []
        
        counter.value_hook.add_listener(lambda: updates.append(counter.value))
        
        counter.value = 1
        counter.value = 2
        counter.value = 3
        
        assert updates == [1, 2, 3]


class TestUsageGuideExamples(ObservableTestCase):
    """Test examples from docs/usage.md."""
    
    def test_floating_hook_creation(self):
        """Test FloatingHook creation and usage."""
        sensor1 = nx.FloatingHook(18.0)
        sensor2 = nx.FloatingHook(22.0)
        sensor3 = nx.FloatingHook(20.0)
        
        assert sensor1.value == 18.0
        assert sensor2.value == 22.0
        assert sensor3.value == 20.0
        
        sensor1.value = 19.5
        assert sensor1.value == 19.5
        assert sensor2.value == 22.0  # Unchanged
    
    def test_join_with_value_adoption(self):
        """Test that target adopts source value on join."""
        source = nx.FloatingHook(100)
        target = nx.FloatingHook(0)
        
        source.join(target, "use_caller_value")
        
        assert source.value == 100
        assert target.value == 100
        
        source.value = 200
        assert target.value == 200
    
    def test_two_separate_fusion_domains(self):
        """Test creating and then fusing two separate domains."""
        A = nx.FloatingHook(1)
        B = nx.FloatingHook(2)
        C = nx.FloatingHook(3)
        D = nx.FloatingHook(4)
        
        A.join(B, "use_caller_value")
        C.join(D, "use_caller_value")
        
        # Two separate domains
        assert A.value == 1 and B.value == 1
        assert C.value == 3 and D.value == 3
        
        # Fuse domains
        B.join(C, "use_caller_value")
        
        assert A.value == B.value == C.value == D.value
        
        A.value = 999
        assert D.value == 999  # Even though A and D never joined directly
    
    def test_validation_rejection(self):
        """Test that invalid updates are rejected."""
        def validate_range(value: int):
            if 0 <= value <= 100:
                return True, "Valid"
            return False, "Value out of range"
        
        hook = nx.FloatingHook(50, isolated_validation_callback=validate_range)
        
        hook.value = 75
        assert hook.value == 75
        
        with pytest.raises(ValueError):
            hook.value = 150
        
        assert hook.value == 75  # Unchanged
    
    def test_multiple_listeners(self):
        """Test multiple listeners on same hook."""
        temperature = nx.XValue(20.0)
        
        log: list[str] = []
        alerts: list[str] = []
        
        def logger():
            log.append(f"Temperature: {temperature.value}")
        
        def alert_high():
            if temperature.value > 30:
                alerts.append("HIGH")
        
        def alert_low():
            if temperature.value < 10:
                alerts.append("LOW")
        
        temperature.value_hook.add_listener(logger)
        temperature.value_hook.add_listener(alert_high)
        temperature.value_hook.add_listener(alert_low)
        
        temperature.value = 35.0
        assert len(log) == 1
        assert "HIGH" in alerts
        
        temperature.value = 5.0
        assert len(log) == 2
        assert "LOW" in alerts
    
    def test_listeners_in_fusion_domains(self):
        """Test that each hook maintains its own listeners."""
        A = nx.FloatingHook(10)
        B = nx.FloatingHook(10)
        
        a_called = [False]
        b_called = [False]
        
        A.add_listener(lambda: a_called.__setitem__(0, True))
        B.add_listener(lambda: b_called.__setitem__(0, True))
        
        A.join(B, "use_caller_value")
        
        A.value = 20
        assert a_called[0]
        assert b_called[0]


class TestInternalSyncExamples(ObservableTestCase):
    """Test internal synchronization examples from docs/internal_sync.md."""
    
    def test_xdict_select_automatic_completion(self):
        """Test automatic value completion when key changes."""
        options = nx.XDictSelect(
            dict_hook={"small": 10, "medium": 20, "large": 30},
            key_hook="medium",
            value_hook=None
        )
        
        assert options.key == "medium"
        assert options.value == 20
        
        # Update only key - value automatically completed
        options.change_key("large")
        assert options.key == "large"
        assert options.value == 30  # Automatically updated
    
    def test_xdict_select_value_updates_dict(self):
        """Test that updating value updates dict atomically."""
        options = nx.XDictSelect(
            dict_hook={"small": 10, "medium": 20, "large": 30},
            key_hook="large",
            value_hook=None
        )
        
        options.change_value(35)
        assert options.dict_hook.value["large"] == 35
    
    def test_atomic_multi_hook_updates(self):
        """Test that multi-hook updates are atomic."""
        select = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2, "c": 3},
            key_hook="a",
            value_hook=None
        )
        
        updates: list[tuple[str, int]] = []
        
        def track_update():
            updates.append((select.key, select.value))
        
        select.key_hook.add_listener(track_update)
        
        select.change_key("c")
        
        # Both key and value updated together
        assert ("c", 3) in updates
    
    def test_cross_object_internal_sync(self):
        """Test internal sync across joined objects."""
        select1 = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="a",
            value_hook=None
        )
        select2 = nx.XDictSelect(
            dict_hook={"a": 1, "b": 2},
            key_hook="b",
            value_hook=None
        )
        
        # Join their dict hooks
        select1.dict_hook.join(select2.dict_hook, "use_caller_value")
        
        # Update value in select1
        select1.change_value(10)
        
        # Dict is shared
        assert select1.dict_hook.value == select2.dict_hook.value
        assert select1.dict_hook.value["a"] == 10
        assert select2.dict_hook.value["a"] == 10
        
        # But values are different (different keys)
        assert select1.value == 10
        assert select2.value == 2


class TestAdvancedExamples(ObservableTestCase):
    """Test advanced examples from docs/examples.md."""
    
    def test_gui_data_binding_pattern(self):
        """Test GUI data binding pattern."""
        # Model
        user_name = nx.XValue("Alice")
        
        # Simulated view
        displayed_value: list[str] = []
        
        def refresh():
            displayed_value.clear()
            displayed_value.append(user_name.value)
        
        user_name.value_hook.add_listener(refresh)
        refresh()  # Initial display
        
        assert displayed_value == ["Alice"]
        
        # Update model
        user_name.value = "Bob"
        assert displayed_value == ["Bob"]
    
    def test_configuration_synchronization(self):
        """Test configuration synchronization pattern."""
        app_config = nx.XDict({"theme": "dark", "language": "en"})
        cache_config: nx.XDict[str, str] = nx.XDict({})
        
        # Synchronize
        app_config.dict_hook.join(cache_config.dict_hook, "use_caller_value")
        
        assert app_config.dict == cache_config.dict
        
        # Update app config
        app_config["theme"] = "light"
        
        # Cache automatically updated
        assert cache_config["theme"] == "light"
    
    def test_sensor_aggregation(self):
        """Test sensor aggregation pattern."""
        sensors = [nx.XValue(20.0 + i) for i in range(5)]
        master = nx.XValue(0.0)
        
        # Join all to master
        for sensor in sensors:
            sensor.value_hook.join(master.value_hook, "use_caller_value")
        
        # All synchronized
        for sensor in sensors:
            assert sensor.value == sensors[0].value
        
        # Update master
        master.value = 25.0
        for sensor in sensors:
            assert sensor.value == 25.0
        
        # Update any sensor
        sensors[2].value = 28.0
        for sensor in sensors:
            assert sensor.value == 28.0
        assert master.value == 28.0

