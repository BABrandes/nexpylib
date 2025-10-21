"""
Demo: Custom Nexus Managers
============================

This demo shows how to create and use custom nexus managers with the
clone_manager() and create_manager() functions.
"""

import nexpy as nx
from nexpy import default

print("Custom Nexus Managers Demo")
print("=" * 60)

# Example 1: Using the default manager
print("\n1. Default Manager:")
print(f"   FLOAT_ACCURACY: {default.FLOAT_ACCURACY}")

x = nx.XValue(1.0)
print(f"   Created XValue with default manager")

# Example 2: Clone the default manager with custom float accuracy
print("\n2. Clone Manager with Custom Float Accuracy:")
strict_manager = default.clone_manager(float_accuracy=1e-15)
print(f"   Cloned manager FLOAT_ACCURACY: {strict_manager.FLOAT_ACCURACY}")

# This manager has all the built-in float/int callbacks
strict_x = nx.XValue(1.0, nexus_manager=strict_manager)
strict_updates = []
strict_x.value_hook.add_listener(lambda: strict_updates.append(strict_x.value))

strict_x.value = 1.0 + 1e-16  # Within 1e-15 tolerance
print(f"   Setting value within tolerance: {len(strict_updates)} updates")

strict_x.value = 1.0 + 1e-14  # Outside 1e-15 tolerance
print(f"   Setting value outside tolerance: {len(strict_updates)} update(s)")

# Example 3: Create a clean manager
print("\n3. Create Clean Manager (no built-in callbacks):")
clean_manager = default.create_manager()
print(f"   Clean manager has {len(clean_manager._value_equality_callbacks)} callbacks")

# Add only the callbacks you need
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

def point_equal(p1: Point, p2: Point, float_accuracy: float) -> bool:
    """Custom point equality - Manhattan distance."""
    return abs(p1.x - p2.x) + abs(p1.y - p2.y) < float_accuracy

clean_manager.add_value_equality_callback((Point, Point), point_equal)

point_x = nx.XValue(Point(1.0, 2.0), nexus_manager=clean_manager)
point_updates = []
point_x.value_hook.add_listener(lambda: point_updates.append(point_x.value))

point_x.value = Point(1.0 + 1e-7, 2.0)  # Very close, within tolerance
print(f"   Setting similar point: {len(point_updates)} updates")

point_x.value = Point(1.001, 2.001)  # Different point
print(f"   Setting different point: {len(point_updates)} update(s)")

# Example 4: Multiple managers with different configurations
print("\n4. Multiple Managers with Different Configurations:")
ui_manager = default.clone_manager(float_accuracy=1e-3)  # Lenient for UI
scientific_manager = default.clone_manager(float_accuracy=1e-12)  # Strict

ui_slider = nx.XValue(0.5, nexus_manager=ui_manager)
sci_measurement = nx.XValue(0.5, nexus_manager=scientific_manager)

ui_updates = []
sci_updates = []
ui_slider.value_hook.add_listener(lambda: ui_updates.append(ui_slider.value))
sci_measurement.value_hook.add_listener(lambda: sci_updates.append(sci_measurement.value))

# Same tiny change to both
tiny_change = 1e-6
ui_slider.value = 0.5 + tiny_change
sci_measurement.value = 0.5 + tiny_change

print(f"   UI slider updates: {len(ui_updates)} (lenient tolerance)")
print(f"   Scientific updates: {len(sci_updates)} (strict tolerance)")

# Example 5: Manager-specific FLOAT_ACCURACY property
print("\n5. Manager FLOAT_ACCURACY Property:")
my_manager = default.clone_manager()
print(f"   Initial (uses default): {my_manager.FLOAT_ACCURACY}")

# Set manager-specific accuracy
my_manager.FLOAT_ACCURACY = 1e-7
print(f"   After setting on manager: {my_manager.FLOAT_ACCURACY}")
print(f"   Module-level default unchanged: {default.FLOAT_ACCURACY}")

# Example 6: Mixing managers in the same application
print("\n6. Using Multiple Managers in One Application:")

# Different domains with different precision requirements
@dataclass
class Temperature:
    celsius: float

@dataclass
class DistanceMicrons:
    value: float

# UI domain - lenient
ui_mgr = default.clone_manager(float_accuracy=1e-3)

def temp_equal(t1: Temperature, t2: Temperature, float_accuracy: float) -> bool:
    # Use custom tolerance of 0.1°C for temperature
    return abs(t1.celsius - t2.celsius) < 0.1

ui_mgr.add_value_equality_callback((Temperature, Temperature), temp_equal)

# Scientific domain - strict
sci_mgr = default.clone_manager(float_accuracy=1e-12)

def distance_equal(d1: DistanceMicrons, d2: DistanceMicrons, float_accuracy: float) -> bool:
    return abs(d1.value - d2.value) < float_accuracy  # Uses manager's precision

sci_mgr.add_value_equality_callback((DistanceMicrons, DistanceMicrons), distance_equal)

room_temp = nx.XValue(Temperature(22.0), nexus_manager=ui_mgr)
measurement = nx.XValue(DistanceMicrons(100.0), nexus_manager=sci_mgr)

print(f"   UI domain manager: {ui_mgr.FLOAT_ACCURACY}")
print(f"   Scientific domain manager: {sci_mgr.FLOAT_ACCURACY}")
print(f"   Different precision requirements handled cleanly!")

print("\n" + "=" * 60)
print("Key Takeaways:")
print("  1. clone_manager() inherits all built-in callbacks")
print("  2. create_manager() gives you a clean slate")
print("  3. Each manager can have its own FLOAT_ACCURACY")
print("  4. Use different managers for different precision domains")
print("=" * 60)

