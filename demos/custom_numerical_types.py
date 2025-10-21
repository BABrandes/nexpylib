"""
Demo: Custom Numerical Types with Float Accuracy
=================================================

This demo shows how to implement custom numerical types that respect
the manager's FLOAT_ACCURACY setting.
"""

import nexpy as nx
from nexpy import default
from dataclasses import dataclass
from math import sqrt

print("Custom Numerical Types with Float Accuracy")
print("=" * 60)

# Example 1: Vector type with float_accuracy parameter
print("\n1. Vector Type (Respects Manager Tolerance):")

@dataclass
class Vector:
    x: float
    y: float
    
    def magnitude(self) -> float:
        return sqrt(self.x**2 + self.y**2)

def vector_equal(v1: Vector, v2: Vector, float_accuracy: float) -> bool:
    """Compare vectors using manager's tolerance.
    
    float_accuracy is passed from active manager.
    """
    return (abs(v1.x - v2.x) < float_accuracy and 
            abs(v1.y - v2.y) < float_accuracy)

# Register the callback
default.register_equality_callback(Vector, Vector, vector_equal)

# Test with default manager (1e-9 tolerance)
print("   Using default manager (1e-9):")
v1 = nx.XValue(Vector(1.0, 2.0))
updates_default = []
v1.value_hook.add_listener(lambda: updates_default.append(v1.value))

v1.value = Vector(1.0 + 1e-10, 2.0)  # Within 1e-9
print(f"   Setting within tolerance: {len(updates_default)} updates")

v1.value = Vector(1.001, 2.0)  # Outside 1e-9
print(f"   Setting outside tolerance: {len(updates_default)} update(s)")

# Test with strict manager (1e-12 tolerance)
print("\n   Using strict manager (1e-12):")
strict_mgr = default.clone_manager(float_accuracy=1e-12)
v2 = nx.XValue(Vector(3.0, 4.0), nexus_manager=strict_mgr)
updates_strict = []
v2.value_hook.add_listener(lambda: updates_strict.append(v2.value))

v2.value = Vector(3.0 + 1e-13, 4.0)  # Within 1e-12
print(f"   Setting within tolerance: {len(updates_strict)} updates")

v2.value = Vector(3.0 + 1e-11, 4.0)  # Outside 1e-12
print(f"   Setting outside tolerance: {len(updates_strict)} update(s)")

print("   ✓ Same callback, different tolerances!")

# Example 2: Complex number type
print("\n2. Complex Number Type:")

@dataclass
class ComplexNum:
    real: float
    imag: float

def complex_equal(c1: ComplexNum, c2: ComplexNum, float_accuracy: float) -> bool:
    """Compare complex numbers using manager's tolerance.
    
    float_accuracy is passed from active manager.
    """
    return (abs(c1.real - c2.real) < float_accuracy and
            abs(c1.imag - c2.imag) < float_accuracy)

default.register_equality_callback(ComplexNum, ComplexNum, complex_equal)

# Use different managers
ui_mgr = default.clone_manager(float_accuracy=1e-3)  # Lenient for UI
sci_mgr = default.clone_manager(float_accuracy=1e-15)  # Strict for science

c_ui = nx.XValue(ComplexNum(1.0, 2.0), nexus_manager=ui_mgr)
c_sci = nx.XValue(ComplexNum(1.0, 2.0), nexus_manager=sci_mgr)

ui_updates = []
sci_updates = []
c_ui.value_hook.add_listener(lambda: ui_updates.append(c_ui.value))
c_sci.value_hook.add_listener(lambda: sci_updates.append(c_sci.value))

# Same small change to both
tiny = 1e-6
c_ui.value = ComplexNum(1.0 + tiny, 2.0)
c_sci.value = ComplexNum(1.0 + tiny, 2.0)

print(f"   UI manager (1e-3) updates: {len(ui_updates)}")
print(f"   Scientific manager (1e-15) updates: {len(sci_updates)}")
print("   ✓ Different precision requirements handled!")

# Example 3: Matrix type (simplified)
print("\n3. Matrix Type (2x2 for demo):")

@dataclass
class Matrix2x2:
    a: float
    b: float
    c: float
    d: float

def matrix_equal(m1: Matrix2x2, m2: Matrix2x2, float_accuracy: float) -> bool:
    """Compare matrices element-wise using manager's tolerance.
    
    float_accuracy is passed from active manager.
    """
    return all([
        abs(m1.a - m2.a) < float_accuracy,
        abs(m1.b - m2.b) < float_accuracy,
        abs(m1.c - m2.c) < float_accuracy,
        abs(m1.d - m2.d) < float_accuracy,
    ])

default.register_equality_callback(Matrix2x2, Matrix2x2, matrix_equal)

mgr = default.clone_manager(float_accuracy=1e-10)
m = nx.XValue(Matrix2x2(1.0, 0.0, 0.0, 1.0), nexus_manager=mgr)
m_updates = []
m.value_hook.add_listener(lambda: m_updates.append(m.value))

# Tiny numerical error (within tolerance)
m.value = Matrix2x2(1.0 + 1e-11, 0.0, 0.0, 1.0)
print(f"   Updates for tiny error: {len(m_updates)}")

# Actual change
m.value = Matrix2x2(2.0, 0.0, 0.0, 2.0)
print(f"   Updates for actual change: {len(m_updates)}")

# Example 4: Custom type without float_accuracy (still works!)
print("\n4. Non-Numerical Type (No float_accuracy needed):")

@dataclass
class Person:
    id: int
    name: str
    age: int

def person_equal(p1: Person, p2: Person, float_accuracy: float) -> bool:
    """ID-based equality - ignores float_accuracy parameter."""
    return p1.id == p2.id

default.register_equality_callback(Person, Person, person_equal)

person = nx.XValue(Person(1, "Alice", 30))
person_updates = []
person.value_hook.add_listener(lambda: person_updates.append(person.value))

# Same ID, different data
person.value = Person(1, "Alice Smith", 31)
print(f"   Updates for same ID: {len(person_updates)}")

# Different ID
person.value = Person(2, "Bob", 25)
print(f"   Updates for different ID: {len(person_updates)}")
print("   ✓ Backward compatible - no float_accuracy needed!")

# Example 5: Changing tolerance at runtime
print("\n5. Dynamic Tolerance Changes:")

@dataclass
class Measurement:
    value: float
    unit: str

def measurement_equal(m1: Measurement, m2: Measurement, float_accuracy: float) -> bool:
    """Compare measurements respecting manager's tolerance.
    
    float_accuracy is passed from active manager.
    """
    if m1.unit != m2.unit:
        return False
    return abs(m1.value - m2.value) < float_accuracy

default.register_equality_callback(Measurement, Measurement, measurement_equal)

mgr = default.clone_manager(float_accuracy=1e-6)
temp = nx.XValue(Measurement(20.0, "°C"), nexus_manager=mgr)
temp_updates = []
temp.value_hook.add_listener(lambda: temp_updates.append(temp.value))

print(f"   Initial tolerance: {mgr.FLOAT_ACCURACY}")
temp.value = Measurement(20.0 + 1e-7, "°C")  # Within 1e-6
print(f"   Updates: {len(temp_updates)}")

# Change tolerance at runtime
mgr.FLOAT_ACCURACY = 1e-12
print(f"   Changed tolerance to: {mgr.FLOAT_ACCURACY}")
temp.value = Measurement(20.0 + 1e-11, "°C")  # Within 1e-12
print(f"   Updates: {len(temp_updates)}")

temp.value = Measurement(20.0 + 1e-10, "°C")  # Outside 1e-12
print(f"   Updates: {len(temp_updates)}")
print("   ✓ Runtime changes work immediately!")

print("\n" + "=" * 60)
print("Key Takeaways:")
print("  1. Custom numerical types SHOULD accept float_accuracy parameter")
print("  2. Manager automatically passes its FLOAT_ACCURACY to callbacks")
print("  3. Different managers can have different tolerances")
print("  4. Same callback respects each manager's setting")
print("  5. Non-numerical types don't need the parameter (backward compatible)")
print("  6. Tolerance changes at runtime take effect immediately")
print("=" * 60)

