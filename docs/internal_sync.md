# Internal Synchronization

This guide explains NexPy's **internal synchronization protocol**—the mechanism that maintains atomic coherence among multiple related hooks within a single object.

---

## Table of Contents

- [Overview](#overview)
- [The ACID Guarantee](#the-acid-guarantee)
- [Multi-Hook Objects](#multi-hook-objects)
- [The Synchronization Protocol](#the-synchronization-protocol)
- [Value Completion Phase](#value-completion-phase)
- [Validation Phase](#validation-phase)
- [Atomic Update Phase](#atomic-update-phase)
- [Examples](#examples)

---

## Overview

While **Nexus fusion** synchronizes state *across* independent objects (inter-object synchronization), **internal synchronization** maintains coherence *within* a single object that exposes multiple related hooks (intra-object synchronization).

### The Challenge

Consider `XDictSelect`, which exposes **5 interconnected hooks**:

- `dict` — The dictionary itself
- `keys` — The set of keys in the dictionary
- `values` — The collection of values
- `key` — The currently selected key
- `value` — The value corresponding to the selected key

These hooks have **invariants** that must always hold:

1. `key` must exist in `dict`
2. `value` must equal `dict[key]`
3. `keys` must match the keys in `dict`
4. `values` must match the values in `dict`

If you update `key`, the system must automatically update `value` to maintain consistency. If you update `value`, the `dict` must be updated at the current `key` position.

**The problem**: How do we ensure all related hooks remain consistent, even under concurrent access or complex update cascades?

**The solution**: NexPy's internal synchronization protocol provides **ACID-like guarantees** for multi-hook updates.

---

## The ACID Guarantee

NexPy's internal synchronization protocol ensures:

### 1. Atomicity

All related hook updates occur **together or not at all**. There is no intermediate state where some hooks are updated and others are not.

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# This operation is atomic:
# - Either dict, key, AND value all update together
# - Or none of them update (if validation fails)
select.key = "b"
```

### 2. Consistency

The system **never enters an invalid state**. All invariants are maintained before, during, and after updates.

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# Invariant: value == dict[key]
assert select.value == select.dict[select.key]  # Always true

select.key = "b"

# Invariant still holds
assert select.value == select.dict[select.key]  # Still true
```

### 3. Isolation

**Concurrent modifications are safely locked**. Multiple threads cannot interleave updates in a way that creates inconsistency.

```python
import nexpy as nx
from threading import Thread

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

def update_key():
    select.key = "b"

def update_value():
    select.value = 10

# Both threads execute safely
t1 = Thread(target=update_key)
t2 = Thread(target=update_value)

t1.start()
t2.start()
t1.join()
t2.join()

# Result is always consistent (never partial updates)
```

### 4. Durability (Logical)

Once an update is accepted, **coherence persists** until the next explicit change. The system doesn't "drift" into inconsistency over time.

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# After update, consistency is guaranteed
select.value = 10

# Invariant continues to hold indefinitely
assert select.value == select.dict[select.key]  # True now
# ... (time passes) ...
assert select.value == select.dict[select.key]  # Still true
```

---

## Multi-Hook Objects

Objects that expose multiple related hooks implement the **internal synchronization protocol** through three key methods:

### 1. `_add_values_to_be_updated()`

Completes missing values when a subset of hooks is updated.

**Example**: If you update `key`, this method returns the new `value` that must also be updated to maintain consistency.

```python
# Conceptual example (simplified)
def _add_values_to_be_updated(self, update_values):
    if "key" in update_values.submitted:
        # Key changed, need to update value
        new_key = update_values.submitted["key"]
        new_value = update_values.current["dict"][new_key]
        return {"value": new_value}
    return {}
```

### 2. `_validate_complete_values_in_isolation()`

Validates that a complete set of values satisfies all invariants.

```python
# Conceptual example (simplified)
def _validate_complete_values_in_isolation(self, values):
    # Check invariant: key must be in dict
    if values["key"] not in values["dict"]:
        return False, "Key not in dictionary"
    
    # Check invariant: value must match dict[key]
    if values["value"] != values["dict"][values["key"]]:
        return False, "Value doesn't match dictionary"
    
    return True, "Valid"
```

### 3. `_invalidate()`

Called after successful updates to recompute derived state.

```python
# Conceptual example (simplified)
def _invalidate(self):
    # Recompute any cached/derived values
    self._cached_keys = set(self._dict.keys())
```

---

## The Synchronization Protocol

When you update a hook in a multi-hook object, NexPy executes a **six-phase protocol**:

```
User Update Request
        ↓
┌───────────────────────────────────────────┐
│  Phase 1: Value Equality Check            │
│  Skip submission if values are unchanged  │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Phase 2: Value Completion                │
│  Call _add_values_to_be_updated()         │
│  Iteratively complete missing values      │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Phase 3: Collect Affected Components     │
│  Identify all hooks, owners, publishers   │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Phase 4: Validation                      │
│  Call _validate_complete_values_in_isolation() │
│  Reject if any validation fails           │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Phase 5: Atomic Update                   │
│  Update all Nexuses simultaneously        │
└───────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────┐
│  Phase 6: Notifications                   │
│  Call _invalidate(), listeners, publishers│
└───────────────────────────────────────────┘
        ↓
    Success
```

---

## Value Completion Phase

The **value completion phase** (Phase 2) ensures all related values are included in the update.

### How It Works

1. User submits one or more values (e.g., just `key`)
2. NexusManager calls `_add_values_to_be_updated()` on affected objects
3. The object returns additional values that must also be updated
4. Process repeats until no new values are added (fixed-point iteration)

### Example: XDictSelect

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2, "c": 3}, key="a")

# User submits only key="b"
# Completion phase automatically adds value=2
select.key = "b"

# Both key and value are updated atomically
print(select.key)    # "b"
print(select.value)  # 2 (automatically completed)
```

### Completion Logic for XDictSelect

The completion logic handles all possible combinations of submitted values:

| Submitted      | Completion Action                                     |
|----------------|-------------------------------------------------------|
| `key` only     | Add `value = dict[key]`                              |
| `value` only   | Update `dict` at current key                         |
| `dict` only    | Update `value = dict[current_key]`                   |
| `key` + `value`| Update `dict` with new key-value pair               |
| `dict` + `key` | Add `value = dict[key]`                             |
| All three      | Validate consistency                                 |

### Iterative Completion

Completion may require multiple iterations:

```python
import nexpy as nx

# Example with cascading updates
select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# Iteration 1: User submits dict
# → Completion adds: value = new_dict[current_key]

# Iteration 2: value is now submitted
# → Completion adds: keys, values (derived from dict)

# Iteration 3: No new values needed
# → Completion completes
```

The protocol prevents infinite loops by tracking which values have been added.

---

## Validation Phase

The **validation phase** (Phase 4) ensures the completed set of values satisfies all invariants.

### Validation Strategy

1. **Complete Value Set** — Validation receives *all* hook values (both submitted and current)
2. **Isolation** — Each object validates independently
3. **All-or-Nothing** — If any validation fails, the entire update is rejected

### Example: XDictSelect Validation

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# Valid update (key exists in dict)
select.key = "b"  # Success

# Invalid update (key doesn't exist)
try:
    select.key = "z"  # KeyError
except KeyError as e:
    print(f"Validation failed: {e}")
```

### Validation Implementation

```python
# Simplified validation for XDictSelect
def _validate_complete_values_in_isolation(self, values):
    # Check all required values present
    if "dict" not in values or "key" not in values or "value" not in values:
        return False, "Missing required values"
    
    # Check dict is not None
    if values["dict"] is None:
        return False, "Dictionary is None"
    
    # Check key exists in dict
    if values["key"] not in values["dict"]:
        return False, f"Key {values['key']} not in dictionary"
    
    # Check value matches dict[key]
    if values["value"] != values["dict"][values["key"]]:
        return False, "Value doesn't match dictionary entry"
    
    return True, "Valid"
```

### Cross-Object Validation

When hooks are joined across objects, validation occurs for *all* affected objects:

```python
import nexpy as nx

select1 = nx.XDictSelect({"a": 1, "b": 2}, key="a")
select2 = nx.XDictSelect({"x": 10, "y": 20}, key="x")

# Join their dict hooks
select1.dict_hook.join(select2.dict_hook)

# Now updates must satisfy BOTH objects' invariants
# This will fail because new dict doesn't contain select2's key="x"
try:
    select1.change_dict_and_key({"c": 3}, "c")
except ValueError as e:
    print(f"Cross-object validation failed: {e}")
```

---

## Atomic Update Phase

The **atomic update phase** (Phase 5) applies all validated changes simultaneously.

### Update Characteristics

1. **Simultaneous** — All Nexuses updated in one operation
2. **Synchronized** — All hooks see changes at the same time
3. **Previous Value Tracking** — Old values saved for rollback/history

### Implementation

```python
# Simplified atomic update (from NexusManager)
for nexus, value in complete_nexus_and_values.items():
    nexus._previous_stored_value = nexus._stored_value
    nexus._stored_value = value
```

### Update Visibility

After the atomic update:

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# Before update
print(select.key)    # "a"
print(select.value)  # 1

# Atomic update of multiple hooks
select.key = "b"

# After update (all changes visible together)
print(select.key)    # "b"
print(select.value)  # 2 (updated atomically)
```

There is **no intermediate state** where `key="b"` but `value=1`.

---

## Examples

### Example 1: XDictSelect — Basic Internal Sync

```python
import nexpy as nx

# Create a selection dictionary
options = nx.XDictSelect(
    {"low": 1, "medium": 5, "high": 10},
    key="medium"
)

print(options.dict)   # {"low": 1, "medium": 5, "high": 10}
print(options.key)    # "medium"
print(options.value)  # 5

# Change key → value automatically updated
options.key = "high"
print(options.value)  # 10

# Change value → dict automatically updated
options.value = 15
print(options.dict)  # {"low": 1, "medium": 5, "high": 15}

# Change dict and key together → value computed
options.change_dict_and_key({"fast": 100, "slow": 10}, "fast")
print(options.value)  # 100
```

### Example 2: XList — List and Element Sync

```python
import nexpy as nx

# Create a reactive list
numbers = nx.XList([1, 2, 3, 4, 5])

# List and length are synchronized
print(numbers.list)    # [1, 2, 3, 4, 5]
print(numbers.length)  # 5

# Append updates both list and length
numbers.append(6)
print(numbers.list)    # [1, 2, 3, 4, 5, 6]
print(numbers.length)  # 6

# Direct list update also updates length
numbers.list = [10, 20]
print(numbers.length)  # 2
```

### Example 3: Cross-Object Internal Sync

```python
import nexpy as nx

# Two selection dicts with shared dictionary
select1 = nx.XDictSelect({"a": 1, "b": 2}, key="a")
select2 = nx.XDictSelect({"a": 1, "b": 2}, key="b")

# Join their dict hooks
select1.dict_hook.join(select2.dict_hook)

# Now they share the same dictionary
print(select1.dict)  # {"a": 1, "b": 2}
print(select2.dict)  # {"a": 1, "b": 2}

# Update value in select1 updates shared dict
select1.value = 10
print(select1.dict)  # {"a": 10, "b": 2}
print(select2.dict)  # {"a": 10, "b": 2}

# select2's value is unchanged (different key)
print(select1.value)  # 10
print(select2.value)  # 2
```

### Example 4: Validation Rejection

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# This will fail: key "z" doesn't exist
try:
    select.key = "z"
except KeyError as e:
    print(f"Update rejected: {e}")

# State remains unchanged
print(select.key)    # "a" (unchanged)
print(select.value)  # 1 (unchanged)

# This will also fail: can't set None as key
try:
    select.key = None
except (KeyError, ValueError) as e:
    print(f"Update rejected: {e}")
```

### Example 5: Listener Notifications

```python
import nexpy as nx

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

# Add listeners to multiple hooks
def on_key_change():
    print(f"Key changed to: {select.key}")

def on_value_change():
    print(f"Value changed to: {select.value}")

select.key_hook.add_listener(on_key_change)
select.value_hook.add_listener(on_value_change)

# Changing key triggers both listeners (internal sync updates value)
select.key = "b"
# Output:
# Key changed to: b
# Value changed to: 2
```

### Example 6: Thread-Safe Internal Sync

```python
import nexpy as nx
from threading import Thread

select = nx.XDictSelect({"a": 1, "b": 2}, key="a")

def update_key():
    for _ in range(100):
        select.key = "b"
        select.key = "a"

def update_value():
    for _ in range(100):
        select.value = 10
        select.value = 1

# Concurrent updates are safe
t1 = Thread(target=update_key)
t2 = Thread(target=update_value)

t1.start()
t2.start()
t1.join()
t2.join()

# Invariant always maintained
assert select.value == select.dict[select.key]
print("Thread safety verified!")
```

---

## Summary

NexPy's internal synchronization protocol ensures:

- ✅ **Atomic updates** across multiple related hooks
- ✅ **Continuous validity** of invariants
- ✅ **Thread-safe** concurrent access
- ✅ **Automatic completion** of related values
- ✅ **Validation** before committing changes
- ✅ **No intermediate invalid states**

This protocol works seamlessly with Nexus fusion to provide coherent synchronization both *within* objects (internal sync) and *across* objects (fusion domains).

---

## Next Steps

- **[Architecture](architecture.md)** — Understand the design philosophy
- **[API Reference](api_reference.md)** — Complete API documentation
- **[Examples](examples.md)** — More practical examples
- **[Concepts](concepts.md)** — Deep dive into fusion domains

---

**[Back to README](../README.md)**

