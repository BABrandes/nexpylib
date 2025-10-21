# Custom Callbacks with Float Accuracy

## Overview

Custom equality callbacks can (and should!) accept an optional `float_accuracy` parameter to respect the manager's tolerance setting. This is especially important for custom numerical types.

## How It Works

When you register a callback, the `NexusManager` will automatically pass its `FLOAT_ACCURACY` to your callback when comparing values:

```python
# Your callback
def my_equal(v1, v2, float_accuracy=1e-9):
    return abs(v1 - v2) < float_accuracy

# Manager calls it like this:
result = my_equal(value1, value2, float_accuracy=manager.FLOAT_ACCURACY)
```

## Callback Signatures

### Required Signature: All callbacks must accept `float_accuracy`

```python
def callback(value1: MyType, value2: MyType, float_accuracy: float) -> bool:
    """Compare values using manager's tolerance.
    
    Note: float_accuracy is ALWAYS passed from active manager.
    For numerical types, use it. For non-numerical types, ignore it.
    """
    # Use float_accuracy for numerical comparisons
    return abs(value1.x - value2.x) < float_accuracy
```

**Benefits:**
- ✅ Respects each manager's tolerance setting
- ✅ Works with different precision requirements
- ✅ Dynamic - changes when `manager.FLOAT_ACCURACY` changes
- ✅ Same callback works for UI (lenient) and scientific (strict) use cases
- ✅ No try-catch overhead in `is_equal()` (fast!)

### For Non-Numerical Types: Accept but ignore the parameter

```python
def callback(value1: MyType, value2: MyType, float_accuracy: float) -> bool:
    """Compare values without tolerance.
    
    float_accuracy is required but can be ignored for non-numerical types.
    """
    # Ignore float_accuracy for non-numerical comparisons
    return value1.id == value2.id
```

**Use cases:**
- Non-numerical types (strings, IDs, enums)
- Structural equality (dict keys, list lengths)
- Any comparison that doesn't involve floating-point numbers

## Complete Examples

### Example 1: Vector Type

```python
from nexpy import default
from dataclasses import dataclass
import nexpy as nx

@dataclass
class Vector:
    x: float
    y: float

def vector_equal(v1: Vector, v2: Vector, float_accuracy: float) -> bool:
    """Compare vectors component-wise with tolerance.
    
    float_accuracy is passed from active manager.
    """
    return (abs(v1.x - v2.x) < float_accuracy and 
            abs(v1.y - v2.y) < float_accuracy)

# Register
default.register_equality_callback(Vector, Vector, vector_equal)

# Use with different managers
ui_mgr = default.clone_manager(float_accuracy=1e-3)   # Lenient for UI
sci_mgr = default.clone_manager(float_accuracy=1e-15)  # Strict for science

ui_vector = nx.XValue(Vector(1.0, 2.0), nexus_manager=ui_mgr)
sci_vector = nx.XValue(Vector(1.0, 2.0), nexus_manager=sci_mgr)

# Same callback, different behaviors!
ui_vector.value = Vector(1.0001, 2.0)   # No update (within 1e-3)
sci_vector.value = Vector(1.0001, 2.0)  # Updates (outside 1e-15)
```

### Example 2: Complex Numbers

```python
@dataclass
class ComplexNum:
    real: float
    imag: float

def complex_equal(c1: ComplexNum, c2: ComplexNum, float_accuracy: float) -> bool:
    """Compare complex numbers with tolerance.
    
    float_accuracy is passed from active manager.
    """
    return (abs(c1.real - c2.real) < float_accuracy and
            abs(c1.imag - c2.imag) < float_accuracy)

default.register_equality_callback(ComplexNum, ComplexNum, complex_equal)
```

### Example 3: Matrix Type

```python
@dataclass
class Matrix2x2:
    data: list[list[float]]  # 2x2 matrix

def matrix_equal(m1: Matrix2x2, m2: Matrix2x2, float_accuracy: float) -> bool:
    """Compare matrices element-wise.
    
    float_accuracy is passed from active manager.
    """
    for i in range(2):
        for j in range(2):
            if abs(m1.data[i][j] - m2.data[i][j]) >= float_accuracy:
                return False
    return True

default.register_equality_callback(Matrix2x2, Matrix2x2, matrix_equal)
```

### Example 4: Non-Numerical Type (no float_accuracy)

```python
@dataclass
class Person:
    id: int
    name: str

def person_equal(p1: Person, p2: Person) -> bool:
    """ID-based equality - no tolerance needed."""
    return p1.id == p2.id

default.register_equality_callback(Person, Person, person_equal)
# Still works! Manager gracefully falls back to 2-parameter call
```

## How the Manager Calls Your Callback

Inside `NexusManager.is_equal()`:

```python
def is_equal(self, value1, value2):
    callback = self._value_equality_callbacks[type_pair]
    # All callbacks receive float_accuracy
    return callback(value1, value2, float_accuracy=self.FLOAT_ACCURACY)
```

This ensures:
- ✅ All callbacks get the manager's FLOAT_ACCURACY setting
- ✅ No try-catch overhead (fast!)
- ✅ Simple and consistent API
- ✅ Callbacks can ignore the parameter if not needed

## Dynamic Tolerance Changes

When you change a manager's `FLOAT_ACCURACY`, callbacks immediately use the new value:

```python
mgr = default.clone_manager(float_accuracy=1e-9)
x = nx.XValue(Vector(1.0, 2.0), nexus_manager=mgr)

# Uses 1e-9
x.value = Vector(1.0 + 1e-10, 2.0)  # No update

# Change tolerance
mgr.FLOAT_ACCURACY = 1e-12

# Now uses 1e-12
x.value = Vector(1.0 + 1e-11, 2.0)  # No update
x.value = Vector(1.0 + 1e-10, 2.0)  # Updates!
```

## Best Practices

### DO ✅

1. **Always accept `float_accuracy` parameter (required!)**
   ```python
   def my_equal(v1, v2, float_accuracy):
       # float_accuracy is ALWAYS passed from active manager
       return abs(v1 - v2) < float_accuracy
   ```

2. **Use it for numerical comparisons**
   ```python
   return (abs(v1.x - v2.x) < float_accuracy and
           abs(v1.y - v2.y) < float_accuracy)
   ```

3. **Ignore it for non-numerical comparisons**
   ```python
   def id_equal(v1, v2, float_accuracy):
       # Parameter required but not used for ID comparison
       return v1.id == v2.id
   ```

4. **Optionally provide a default for standalone testing**
   ```python
   def my_equal(v1, v2, float_accuracy=1e-9):
       # Default only used if called directly (rare)
       # Manager always overrides with its FLOAT_ACCURACY
       return abs(v1 - v2) < float_accuracy
   ```

5. **Document that your callback respects tolerance**
   ```python
   def vector_equal(v1, v2, float_accuracy):
       """Compare vectors using manager's tolerance.
       
       float_accuracy is passed from active manager.
       """
       ...
   ```

### DON'T ❌

1. **Don't omit `float_accuracy` parameter (required!)**
   ```python
   # BAD - missing required parameter
   def bad_equal(v1, v2):
       return abs(v1 - v2) < 1e-9
   # Will raise TypeError when manager calls it!
   ```

2. **Don't hard-code tolerances for numerical types**
   ```python
   # BAD - ignores manager's setting
   def bad_equal(v1, v2, float_accuracy):
       return abs(v1 - v2) < 1e-6  # Hard-coded! Should use float_accuracy
   ```

3. **Don't use wrong parameter**
   ```python
   # BAD - uses wrong tolerance
   def bad_equal(v1, v2, float_accuracy):
       return abs(v1 - v2) < 1e-9  # Should use float_accuracy parameter!
   ```

## Integration with NumPy

If you're using NumPy arrays:

```python
import numpy as np

def numpy_equal(a: np.ndarray, b: np.ndarray, float_accuracy: float) -> bool:
    """Compare numpy arrays with tolerance.
    
    float_accuracy is passed from active manager.
    """
    return np.allclose(a, b, atol=float_accuracy, rtol=0)

default.register_equality_callback(np.ndarray, np.ndarray, numpy_equal)
```

## Summary

| Feature | Status |
|---------|--------|
| Built-in callbacks use `float_accuracy` | ✅ Yes |
| Custom callbacks can use it | ✅ Yes |
| Manager passes its `FLOAT_ACCURACY` | ✅ Yes |
| Backward compatible with 2-param callbacks | ✅ Yes |
| Works with different managers | ✅ Yes |
| Dynamic tolerance changes | ✅ Yes |

**Bottom Line**: For numerical types, always accept `float_accuracy` as an optional third parameter. Your callback will automatically respect each manager's tolerance setting, making it work seamlessly across different precision requirements.

