# Usage Guide

This guide covers the fundamental concepts and operations in NexPy: Hooks, Nexus fusion, join/isolate mechanics, and basic reactive patterns.

---

## Table of Contents

- [Hooks: The Connection Points](#hooks-the-connection-points)
- [Nexus: The Fusion Domain](#nexus-the-fusion-domain)
- [Join Operations: Creating Fusion Domains](#join-operations-creating-fusion-domains)
- [Isolate Operations: Breaking Fusion](#isolate-operations-breaking-fusion)
- [Value Updates and Synchronization](#value-updates-and-synchronization)
- [Listeners and Reactions](#listeners-and-reactions)
- [Thread Safety](#thread-safety)

---

## Hooks: The Connection Points

A **Hook** is the fundamental connection point in NexPy. Think of it as a "connector" or "port" that can be joined with other hooks to establish synchronization.

### Types of Hooks

#### 1. FloatingHook — Independent Hooks

FloatingHooks are standalone hooks not owned by any x_object. They're perfect for simple reactive values or intermediate connections.

```python
import nexpy as nx

# Create independent floating hooks
temp = nx.FloatingHook(20.0)
display = nx.FloatingHook(0.0)

print(temp.value)     # 20.0
print(display.value)  # 0.0

# Update a floating hook
temp.value = 25.0
print(temp.value)  # 25.0
```

#### 2. OwnedHook — Object-Owned Hooks

OwnedHooks belong to reactive objects (like `XValue`, `XDict`, `XList`). They participate in the object's internal synchronization protocol.

```python
import nexpy as nx

# XValue internally creates an OwnedHook
value = nx.XValue(42)
hook = value.hook  # This is an OwnedHook

print(type(hook))  # OwnedHook
print(hook.owner)  # The XValue instance
```

### Hook Properties

All hooks provide these core properties:

```python
import nexpy as nx

hook = nx.FloatingHook(100)

# Read the current value
print(hook.value)  # 100

# Get the underlying Nexus
nexus = hook._get_nexus()
print(nexus.stored_value)  # 100

# Check nexus manager
manager = hook._get_nexus_manager()
```

---

## Nexus: The Fusion Domain

A **Nexus** is the shared synchronization core that represents a fusion domain. All hooks connected to the same Nexus share the same value and remain synchronized.

### Nexus Lifecycle

```
┌─────────────────┐
│ Hook Created    │ ──→  New Nexus created with initial value
└─────────────────┘

┌─────────────────┐
│ Hooks Joined    │ ──→  Original Nexuses destroyed,
└─────────────────┘      New unified Nexus created

┌─────────────────┐
│ Hook Isolated   │ ──→  Hook gets new independent Nexus,
└─────────────────┘      Original Nexus kept by remaining hooks
```

### Nexus Characteristics

1. **One Value** — Each Nexus stores exactly one value
2. **Multiple Hooks** — Many hooks can reference the same Nexus
3. **Weak References** — Hooks are stored as weak refs for automatic cleanup
4. **Synchronous Updates** — All hooks see value changes simultaneously

```python
import nexpy as nx

# Each hook starts with its own Nexus
A = nx.FloatingHook(1)
B = nx.FloatingHook(2)

nexus_A = A._get_nexus()
nexus_B = B._get_nexus()

print(nexus_A is nexus_B)  # False (different Nexuses)

# After joining, they share the same Nexus
A.join(B)

nexus_A_after = A._get_nexus()
nexus_B_after = B._get_nexus()

print(nexus_A_after is nexus_B_after)  # True (same Nexus)
```

---

## Join Operations: Creating Fusion Domains

The `join()` method is the core operation for creating fusion domains. It fuses the Nexuses of two hooks, creating transitive synchronization.

### Basic Join

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(20)

# Before join: independent values
print(A.value, B.value)  # 10 20

# Join A and B
A.join(B)

# After join: synchronized values
print(A.value, B.value)  # 10 10 (B adopts A's value)

# Updates propagate
A.value = 100
print(B.value)  # 100
```

### Join is Symmetric

```python
import nexpy as nx

A = nx.FloatingHook(1)
B = nx.FloatingHook(2)

# These are equivalent
A.join(B)  # Same as...
B.join(A)  # ...this
```

### Join is Transitive

The power of NexPy comes from **transitive synchronization**. When you join `A→B` and `B→C`, you automatically get `A→B→C` synchronization.

```python
import nexpy as nx

A = nx.FloatingHook(1)
B = nx.FloatingHook(2)
C = nx.FloatingHook(3)
D = nx.FloatingHook(4)

# Create first fusion domain
A.join(B)  # Nexus_AB: {A, B}

# Create second fusion domain
C.join(D)  # Nexus_CD: {C, D}

# Fuse both domains
B.join(C)  # Nexus_ABCD: {A, B, C, D}

# All four hooks now share the same Nexus
# Even though A and D were never joined directly!
print(A.value)  # All have the same value
print(B.value)
print(C.value)
print(D.value)

# Verify they share the same Nexus
nexus_A = A._get_nexus()
nexus_B = B._get_nexus()
nexus_C = C._get_nexus()
nexus_D = D._get_nexus()

print(nexus_A is nexus_B is nexus_C is nexus_D)  # True
```

### Join Fusion Process

When you call `A.join(B)`:

1. **Value Synchronization** — B's Nexus adopts A's value
2. **Validation** — NexusManager validates the new value is acceptable
3. **Nexus Fusion** — Both Nexuses are destroyed, new unified Nexus created
4. **Reference Update** — All hooks update their Nexus reference

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(20)

# Capture original Nexuses
original_nexus_A = A._get_nexus()
original_nexus_B = B._get_nexus()

# Join creates a new Nexus
A.join(B)

# New unified Nexus
new_nexus = A._get_nexus()

# Original Nexuses are destroyed
print(new_nexus is not original_nexus_A)  # True
print(new_nexus is not original_nexus_B)  # True

# Both hooks reference the new Nexus
print(A._get_nexus() is B._get_nexus())  # True
```

### Join with Validation

If joining would create an invalid state, the join operation fails:

```python
import nexpy as nx

# Create a floating hook with validation
def validate_positive(value):
    if value > 0:
        return True, "Valid"
    return False, "Value must be positive"

A = nx.FloatingHook(10, isolated_validation_callback=validate_positive)
B = nx.FloatingHook(-5)

# This join will fail because B's value is negative
try:
    A.join(B)
except ValueError as e:
    print(f"Join failed: {e}")  # Value must be positive
```

### Joining XObject Hooks

You can join hooks from high-level reactive objects:

```python
import nexpy as nx

# Create reactive values
temperature = nx.XValue(20.0)
display = nx.XValue(0.0)

# Join their hooks
temperature.hook.join(display.hook)

# Now synchronized
temperature.value = 25.5
print(display.value)  # 25.5

# Works both ways
display.value = 30.0
print(temperature.value)  # 30.0
```

### Complex Fusion Networks

You can build arbitrarily complex fusion networks:

```python
import nexpy as nx

# Create a network of sensors
sensors = [nx.XValue(20.0) for _ in range(10)]

# Join them all to the first sensor
main_sensor = sensors[0]
for sensor in sensors[1:]:
    main_sensor.hook.join(sensor.hook)

# All sensors are now synchronized
main_sensor.value = 25.0
print([s.value for s in sensors])  # All 25.0

# Any sensor can update the fusion domain
sensors[5].value = 30.0
print([s.value for s in sensors])  # All 30.0
```

---

## Isolate Operations: Breaking Fusion

The `isolate()` method removes a hook from its fusion domain, giving it an independent Nexus.

### Basic Isolate

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(10)
C = nx.FloatingHook(10)

# Create fusion domain
A.join(B)
B.join(C)  # All share Nexus_ABC

print(A.value, B.value, C.value)  # 10 10 10

# Isolate B
B.isolate()

# B now has its own Nexus
A.value = 20
print(A.value, B.value, C.value)  # 20 10 20

# B is independent
B.value = 99
print(A.value, B.value, C.value)  # 20 99 20
```

### Isolate Preserves Current Value

When a hook is isolated, its new Nexus is initialized with the current value:

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(10)

A.join(B)
A.value = 50

print(A.value, B.value)  # 50 50

# Isolate B with current value
B.isolate()

print(A.value, B.value)  # 50 50 (B keeps value 50)

# Now independent
A.value = 100
print(A.value, B.value)  # 100 50
```

### Isolate Use Cases

#### 1. Temporary Synchronization

```python
import nexpy as nx

# Synchronize for initial setup
config = nx.XValue({"mode": "default"})
backup = nx.XValue({})

config.hook.join(backup.hook)  # Sync initial state

# Later, break synchronization for independent evolution
backup.hook.isolate()
```

#### 2. Conditional Fusion

```python
import nexpy as nx

master = nx.XValue(100)
slave = nx.XValue(0)

# Conditionally join/isolate based on application state
def set_sync_mode(enabled: bool):
    if enabled:
        slave.hook.join(master.hook)
    else:
        slave.hook.isolate()

set_sync_mode(True)   # Enable sync
master.value = 200
print(slave.value)  # 200

set_sync_mode(False)  # Disable sync
master.value = 300
print(slave.value)  # 200 (unchanged)
```

#### 3. Breaking Circular Dependencies

```python
import nexpy as nx

A = nx.XValue(1)
B = nx.XValue(1)
C = nx.XValue(1)

# Create fusion network
A.hook.join(B.hook)
B.hook.join(C.hook)

# Break one connection to prevent unwanted propagation
B.hook.isolate()

# A and C still joined, but B is independent
A.value = 10
print(A.value, B.value, C.value)  # 10 1 10
```

---

## Value Updates and Synchronization

### Direct Value Assignment

```python
import nexpy as nx

hook = nx.FloatingHook(10)

# Direct assignment
hook.value = 20
print(hook.value)  # 20
```

### Value Submission

For more control, use `submit_value()`:

```python
import nexpy as nx

hook = nx.FloatingHook(10)

# Submit value with explicit error handling
success, msg = hook.submit_value(20)
if success:
    print(f"Value updated: {hook.value}")
else:
    print(f"Update failed: {msg}")
```

### Fusion Domain Updates

When you update a hook in a fusion domain, all connected hooks are updated:

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(10)
C = nx.FloatingHook(10)

A.join(B)
B.join(C)

# Update any hook
B.value = 99

# All hooks updated
print(A.value, B.value, C.value)  # 99 99 99
```

### Update Rejection

If an update would violate validation rules, it's rejected:

```python
import nexpy as nx

def validate_range(value):
    if 0 <= value <= 100:
        return True, "Valid"
    return False, "Value out of range"

hook = nx.FloatingHook(50, isolated_validation_callback=validate_range)

# This succeeds
hook.value = 75
print(hook.value)  # 75

# This fails
try:
    hook.value = 150
except ValueError as e:
    print(f"Update rejected: {e}")
```

---

## Listeners and Reactions

### Adding Listeners

Listeners are callbacks that execute when a hook's value changes:

```python
import nexpy as nx

hook = nx.FloatingHook(10)

def on_change():
    print(f"Hook changed to: {hook.value}")

# Add listener
hook.add_listener(on_change)

# Triggers listener
hook.value = 20  # Prints: "Hook changed to: 20"
hook.value = 30  # Prints: "Hook changed to: 30"
```

### Multiple Listeners

You can attach multiple listeners:

```python
import nexpy as nx

hook = nx.FloatingHook(10)

def logger():
    print(f"[LOG] Value: {hook.value}")

def validator():
    if hook.value < 0:
        print("[WARN] Negative value detected!")

hook.add_listener(logger)
hook.add_listener(validator)

hook.value = -5
# Prints:
# [LOG] Value: -5
# [WARN] Negative value detected!
```

### Removing Listeners

```python
import nexpy as nx

hook = nx.FloatingHook(10)

def on_change():
    print("Changed!")

hook.add_listener(on_change)
hook.value = 20  # Prints: "Changed!"

# Remove listener
hook.remove_listener(on_change)
hook.value = 30  # (no output)
```

### Listeners in Fusion Domains

Each hook maintains its own listeners, even in fusion domains:

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(10)

A.add_listener(lambda: print("A changed"))
B.add_listener(lambda: print("B changed"))

A.join(B)

# Both hooks updated, both listeners triggered
A.value = 20
# Prints:
# A changed
# B changed
```

### Reaction Callbacks

FloatingHooks support reaction callbacks for custom side effects:

```python
import nexpy as nx

def react():
    print("Reaction triggered!")
    return True, "Success"

hook = nx.FloatingHook(10, reaction_callback=react)

hook.value = 20  # Triggers reaction
```

---

## Thread Safety

All NexPy operations are thread-safe. The NexusManager uses a reentrant lock to protect the complete synchronization flow.

### Concurrent Updates

```python
import nexpy as nx
from threading import Thread

hook = nx.FloatingHook(0)
results = []

def worker(value):
    hook.value = value
    results.append(hook.value)

# Create multiple threads
threads = [Thread(target=worker, args=(i,)) for i in range(100)]

# Start all threads
for t in threads:
    t.start()

# Wait for completion
for t in threads:
    t.join()

# All updates applied safely
print(f"Final value: {hook.value}")
print(f"All results: {len(results)} updates")
```

### Thread-Safe Join/Isolate

```python
import nexpy as nx
from threading import Thread

A = nx.FloatingHook(10)
B = nx.FloatingHook(20)

def join_worker():
    A.join(B)

def isolate_worker():
    A.isolate()

# Safe to call concurrently
t1 = Thread(target=join_worker)
t2 = Thread(target=isolate_worker)

t1.start()
t2.start()
t1.join()
t2.join()
```

---

## Custom Equality Checks

NexPy uses equality checks to determine if a value has actually changed during updates. You can register custom equality callbacks at the NexusManager level for fine-grained control.

### Why Custom Equality Checks?

By default, NexPy uses Python's `==` operator for equality checks. However, this may not be appropriate for all types:

- **Floating-point numbers**: Rounding errors mean you should use tolerance-based comparison
- **Custom classes**: Domain-specific equality logic
- **Large data structures**: Performance-optimized comparisons

### Floating-Point Numbers

**Standard Practice**: Register a custom equality callback for floating-point numbers with a tolerance of 1e-9:

```python
import nexpy as nx
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Configure BEFORE creating any hooks or x_objects
def float_equality(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), float_equality)

# Now floating-point comparisons use the tolerance
temperature = nx.XValue(20.0)
temperature.value = 20.0000000001  # No update triggered (considered equal)
temperature.value = 20.001  # Update triggered (exceeds tolerance)
```

### Why This Matters

Without custom equality:
```python
hook = nx.FloatingHook(1.0)
hook.value = 1.0 + 1e-15  # Triggers update (technically different)
# Listener called unnecessarily
# Validation re-run unnecessarily
# All synchronized hooks updated unnecessarily
```

With custom equality:
```python
# Configure tolerance first
DEFAULT_NEXUS_MANAGER.add_value_equality_callback(
    (float, float),
    lambda a, b: abs(a - b) < 1e-9
)

hook = nx.FloatingHook(1.0)
hook.value = 1.0 + 1e-15  # No update (within tolerance)
# No listeners triggered
# No unnecessary validation
# No unnecessary synchronization
```

### Multiple Type Pairs

Register callbacks for multiple type pairs:

```python
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Float-Float
def float_eq(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

# Float-Int (cross-type comparison)
def float_int_eq(a: float, b: int) -> bool:
    return abs(a - b) < 1e-9

# Register both directions
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), float_eq)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, int), float_int_eq)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((int, float), lambda a, b: float_int_eq(b, a))
```

### Best Practices

1. **Configure Early**: Register callbacks at application startup, before creating hooks
2. **Use Standard Tolerances**: 1e-9 is standard for most floating-point applications
3. **Handle Cross-Type**: Register callbacks for both `(float, float)` and `(float, int)`
4. **Be Consistent**: Use the same tolerance throughout your application

### Reentrancy Protection

NexPy prevents recursive modifications of the same Nexus:

```python
import nexpy as nx

hook = nx.FloatingHook(10)

def bad_listener():
    # This attempts to modify the same hook during its own update
    hook.value = 99

hook.add_listener(bad_listener)

# This will raise RuntimeError
try:
    hook.value = 20
except RuntimeError as e:
    print(f"Reentrancy protection triggered: {e}")
```

However, modifying **independent** Nexuses in listeners is allowed:

```python
import nexpy as nx

hook1 = nx.FloatingHook(10)
hook2 = nx.FloatingHook(20)

def listener():
    # This is safe - hook2 is independent
    hook2.value = 99

hook1.add_listener(listener)

hook1.value = 30  # No error, hook2 updated to 99
```

---

## Next Steps

- **[Internal Synchronization](internal_sync.md)** — Learn about atomic multi-hook updates
- **[Architecture](architecture.md)** — Understand NexPy's design philosophy
- **[API Reference](api_reference.md)** — Complete API documentation
- **[Examples](examples.md)** — More practical examples

---

**[Back to README](../README.md)**

