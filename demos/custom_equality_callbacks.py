"""
Demo: Custom Equality Callbacks
================================

This demo shows how to register custom equality comparison functions for
your own types using the nexpy.default module.
"""

import nexpy as nx
from nexpy import default
from dataclasses import dataclass

print("Custom Equality Callbacks Demo")
print("=" * 60)

# Example 1: Custom class with tolerance-based equality
print("\n1. Custom Vector class with tolerance-based equality:")

@dataclass
class Vector:
    x: float
    y: float

def vector_equal(v1: Vector, v2: Vector, float_accuracy: float = 1e-6) -> bool:
    """Check if two vectors are equal within tolerance.
    
    float_accuracy is passed from active manager.
    Default 1e-6 is used for this demo's custom tolerance.
    """
    return (abs(v1.x - v2.x) < float_accuracy and 
            abs(v1.y - v2.y) < float_accuracy)

# Register the custom equality
default.register_equality_callback(Vector, Vector, vector_equal)

# Create observables with Vector values
v1 = nx.XValue(Vector(1.0, 2.0))
v2 = nx.XValue(Vector(1.0000001, 2.0000001))

# Join them - they'll be considered equal due to tolerance
v1.value_hook.join(v2.value_hook)
print(f"   v1.value = Vector({v1.value.x}, {v1.value.y})")
print(f"   v2.value = Vector({v2.value.x}, {v2.value.y})")

# Try to set a value within tolerance - no update should occur
initial_value = v1.value
v1.value = Vector(1.0000002, 2.0000002)
print(f"   After setting within tolerance: {v1.value is initial_value}")

# Set a value outside tolerance - update occurs
v1.value = Vector(3.0, 4.0)
print(f"   After significant change: Vector({v1.value.x}, {v1.value.y})")

# Example 2: Custom class with semantic equality
print("\n2. Custom Person class with ID-based equality:")

@dataclass
class Person:
    id: int
    name: str
    age: int

def person_equal(p1: Person, p2: Person, float_accuracy: float) -> bool:
    """Two persons are equal if they have the same ID.
    
    Ignores float_accuracy parameter (not needed for ID comparison).
    """
    return p1.id == p2.id

# Register the custom equality
default.register_equality_callback(Person, Person, person_equal)

# Create observables
person_a = nx.XValue(Person(1, "Alice", 30))
person_b = nx.XValue(Person(1, "Alice Smith", 31))  # Same ID, different data

# These are considered equal because ID matches
person_a.value_hook.join(person_b.value_hook)
print(f"   person_a: {person_a.value}")
print(f"   person_b: {person_b.value}")
print(f"   Same object reference: {person_a.value is person_b.value}")

# Example 3: List-based custom type
print("\n3. Custom type with list comparison:")

@dataclass
class Histogram:
    bins: list
    
def histogram_equal(h1: Histogram, h2: Histogram, float_accuracy: float) -> bool:
    """Compare histograms by their bin contents.
    
    float_accuracy is passed from active manager.
    """
    if len(h1.bins) != len(h2.bins):
        return False
    return all(abs(a - b) < float_accuracy for a, b in zip(h1.bins, h2.bins))

# Register the custom equality
default.register_equality_callback(Histogram, Histogram, histogram_equal)

hist1 = nx.XValue(Histogram([1.0, 2.0, 3.0]))
hist2 = nx.XValue(Histogram([1.0, 2.0, 3.0]))

hist1.value_hook.join(hist2.value_hook)
print(f"   hist1.bins = {hist1.value.bins}")
print(f"   hist2.bins = {hist2.value.bins}")

print("\n" + "=" * 60)
print("Key Takeaways:")
print("  1. Register equality callbacks before creating observables")
print("  2. Custom equality enables semantic comparisons")
print("  3. Works seamlessly with all nexpy features (hooks, fusion, etc.)")
print("=" * 60)

