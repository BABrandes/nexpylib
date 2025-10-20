# API Reference

Complete API documentation for NexPy (nexpylib).

---

## Table of Contents

- [Core Hook Classes](#core-hook-classes)
- [Reactive Value Objects](#reactive-value-objects)
- [Reactive Collections](#reactive-collections)
- [Selection Objects](#selection-objects)
- [Nexus System](#nexus-system)
- [Publisher-Subscriber](#publisher-subscriber)
- [Protocols](#protocols)

---

## Core Hook Classes

### FloatingHook

```python
class FloatingHook(Generic[T])
```

Independent hook not owned by any x_object.

**Constructor**:
```python
FloatingHook(
    value: T,
    reaction_callback: Optional[Callable[[], tuple[bool, str]]] = None,
    isolated_validation_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `value: T` — Current value (read/write)

**Methods**:

#### `join(other)`
Join this hook with another hook, creating a fusion domain.

**Parameters**:
- `other: Hook[T]` — Hook to join with

**Raises**:
- `ValueError` — If validation fails

**Example**:
```python
hook1 = nx.FloatingHook(10)
hook2 = nx.FloatingHook(20)
hook1.join(hook2)
print(hook1.value, hook2.value)  # 10 10
```

#### `isolate()`
Remove this hook from its fusion domain, creating an independent Nexus.

**Example**:
```python
hook.isolate()  # Hook now has independent Nexus
```

#### `is_joined_with(other)`
Check if this hook is joined with another hook (shares same Nexus).

**Parameters**:
- `other: Hook[T]` — Hook to check

**Returns**:
- `bool` — True if hooks share the same Nexus

#### `add_listener(callback)`
Add a listener that will be called when the value changes.

**Parameters**:
- `callback: Callable[[], None]` — Callback function

#### `remove_listener(callback)`
Remove a previously added listener.

**Parameters**:
- `callback: Callable[[], None]` — Callback function to remove

#### `submit_value(value)`
Submit a new value to the hook.

**Parameters**:
- `value: T` — New value to set

**Returns**:
- `tuple[bool, str]` — (success, message)

---

### OwnedHook

```python
class OwnedHook(Generic[T])
```

Hook owned by an X object, integrated with object's internal synchronization.

**Constructor**:
```python
OwnedHook(
    owner: CarriesSomeHooksProtocol[Any, Any],
    initial_value: T,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `value: T` — Current value (read/write)
- `owner: CarriesSomeHooksProtocol` — The owning X object

**Methods**:
Same as FloatingHook: `join()`, `isolate()`, `is_joined_with()`, `add_listener()`, `remove_listener()`, `submit_value()`

**Key Differences from FloatingHook**:
- Validation delegated to owner object
- Participates in owner's internal synchronization
- Automatically triggers owner invalidation on changes

---

## Reactive Value Objects

### XValue

```python
class XValue(Generic[T])
```

Reactive value wrapper providing seamless integration with NexPy's synchronization system.

**Constructor**:
```python
XValue(
    value_or_hook: T | Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T],
    validator: Optional[Callable[[T], tuple[bool, str]]] = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `value: T` — Current value (read/write)
- `hook: Hook[T]` — Underlying owned hook for fusion operations

**Methods**:

#### `change_value(new_value, *, raise_submission_error_flag=True)`
Change the value (lambda-friendly method).

**Parameters**:
- `new_value: T` — The new value to set
- `raise_submission_error_flag: bool` — Whether to raise SubmissionError on failure

**Returns**:
- `tuple[bool, str]` — (success, message)

**Example**:
```python
temperature = nx.XValue(20.0)
success, msg = temperature.change_value(25.5)
```

---

## Reactive Collections

### XList

```python
class XList(Generic[T])
```

Reactive list providing automatic synchronization of list and length.

**Constructor**:
```python
XList(
    initial_list: Sequence[T],
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `list: list[T]` — The list (read/write)
- `length: int` — Length of the list (read-only)
- `list_hook: Hook[list[T]]` — Hook for the list
- `length_hook: Hook[int]` — Hook for the length

**Methods**:

#### `append(value)`
Append a value to the list.

**Parameters**:
- `value: T` — Value to append

#### `extend(values)`
Extend the list with multiple values.

**Parameters**:
- `values: Sequence[T]` — Values to add

#### `insert(index, value)`
Insert a value at a specific index.

**Parameters**:
- `index: int` — Index to insert at
- `value: T` — Value to insert

#### `remove(value)`
Remove the first occurrence of a value.

**Parameters**:
- `value: T` — Value to remove

#### `pop(index=-1)`
Remove and return item at index (default last).

**Parameters**:
- `index: int` — Index to pop from

**Returns**:
- `T` — The popped value

#### `clear()`
Remove all items from the list.

**Example**:
```python
numbers = nx.XList([1, 2, 3])
numbers.append(4)
print(numbers.list)    # [1, 2, 3, 4]
print(numbers.length)  # 4
```

---

### XSet

```python
class XSet(Generic[T])
```

Reactive set providing automatic synchronization.

**Constructor**:
```python
XSet(
    initial_set: Set[T] | None = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `set: set[T]` — The set (read/write)
- `set_hook: Hook[set[T]]` — Hook for the set

**Methods**:

#### `add(value)`
Add a value to the set.

**Parameters**:
- `value: T` — Value to add

#### `remove(value)`
Remove a value from the set.

**Parameters**:
- `value: T` — Value to remove

**Raises**:
- `KeyError` — If value not in set

#### `discard(value)`
Remove a value from the set if it exists.

**Parameters**:
- `value: T` — Value to discard

#### `clear()`
Remove all items from the set.

**Example**:
```python
tags = nx.XSet({"python", "reactive"})
tags.add("framework")
print(tags.set)  # {"python", "reactive", "framework"}
```

---

### XDict

```python
class XDict(Generic[K, V])
```

Reactive dictionary providing automatic synchronization.

**Constructor**:
```python
XDict(
    initial_dict: Mapping[K, V] | None = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `dict: dict[K, V]` — The dictionary (read/write)
- `dict_hook: Hook[dict[K, V]]` — Hook for the dictionary

**Methods**:

#### `__getitem__(key)`
Get value for a key.

**Parameters**:
- `key: K` — Key to look up

**Returns**:
- `V` — Value at key

#### `__setitem__(key, value)`
Set value for a key.

**Parameters**:
- `key: K` — Key to set
- `value: V` — Value to set

#### `__delitem__(key)`
Delete a key-value pair.

**Parameters**:
- `key: K` — Key to delete

#### `get(key, default=None)`
Get value for a key with default.

**Parameters**:
- `key: K` — Key to look up
- `default` — Default value if key not found

**Returns**:
- `V | default` — Value at key or default

#### `clear()`
Remove all items from the dictionary.

**Example**:
```python
config = nx.XDict({"debug": False, "version": "1.0"})
config["debug"] = True
print(config.dict)  # {"debug": True, "version": "1.0"}
```

---

## Selection Objects

### XDictSelect

```python
class XDictSelect(Generic[K, V])
```

Selection from a dictionary with atomic internal synchronization of dict, key, and value.

**Constructor**:
```python
XDictSelect(
    initial_dict: Mapping[K, V],
    key: K,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `dict: dict[K, V]` — The dictionary (read/write)
- `key: K` — Currently selected key (read/write)
- `value: V` — Value at currently selected key (read/write)
- `keys: set[K]` — Set of keys in dictionary (read-only)
- `values: list[V]` — List of values in dictionary (read-only)
- `dict_hook: Hook[dict[K, V]]` — Hook for dictionary
- `key_hook: Hook[K]` — Hook for selected key
- `value_hook: Hook[V]` — Hook for selected value

**Invariants**:
- `key` must always exist in `dict`
- `value` must always equal `dict[key]`
- Changing `key` automatically updates `value`
- Changing `value` automatically updates `dict[key]`

**Methods**:

#### `change_key(new_key)`
Change the selected key.

**Parameters**:
- `new_key: K` — New key to select

**Raises**:
- `KeyError` — If key not in dictionary

#### `change_value(new_value)`
Change the value at the selected key.

**Parameters**:
- `new_value: V` — New value to set

#### `change_dict_and_key(new_dict, new_key)`
Atomically change both dictionary and selected key.

**Parameters**:
- `new_dict: Mapping[K, V]` — New dictionary
- `new_key: K` — New key to select

**Example**:
```python
options = nx.XDictSelect(
    {"low": 1, "medium": 5, "high": 10},
    key="medium"
)

print(options.value)  # 5

# Change key → value automatically updated
options.key = "high"
print(options.value)  # 10

# Change value → dict automatically updated
options.value = 15
print(options.dict["high"])  # 15
```

---

### XSetSelect

```python
class XSetSelect(Generic[T])
```

Selection from a set with automatic synchronization.

**Constructor**:
```python
XSetSelect(
    universe: Set[T],
    selection: T,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `set: set[T]` — The set of available options (read/write)
- `selection: T` — Currently selected value (read/write)
- `set_hook: Hook[set[T]]` — Hook for the set
- `selection_hook: Hook[T]` — Hook for selection

**Invariants**:
- `selection` must always exist in `set`

**Example**:
```python
options = nx.XSetSelect({1, 2, 3, 4, 5}, selection=3)
options.selection = 5  # OK
# options.selection = 10  # Would raise KeyError
```

---

### XSetMultiSelect

```python
class XSetMultiSelect(Generic[T])
```

Multi-selection from a set with automatic synchronization.

**Constructor**:
```python
XSetMultiSelect(
    universe: Set[T],
    selection: Set[T],
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `universe: set[T]` — The set of available options (read/write)
- `selection: set[T]` — Currently selected values (read/write)
- `universe_hook: Hook[set[T]]` — Hook for universe
- `selection_hook: Hook[set[T]]` — Hook for selection

**Invariants**:
- `selection` must be a subset of `universe`

**Methods**:

#### `select(value)`
Add a value to the selection.

**Parameters**:
- `value: T` — Value to select

#### `deselect(value)`
Remove a value from the selection.

**Parameters**:
- `value: T` — Value to deselect

**Example**:
```python
features = nx.XSetMultiSelect(
    universe={"a", "b", "c", "d"},
    selection={"a", "c"}
)

features.select("b")
print(features.selection)  # {"a", "b", "c"}

features.deselect("a")
print(features.selection)  # {"b", "c"}
```

---

## Nexus System

### Nexus

```python
class Nexus(Generic[T])
```

Shared synchronization core representing a fusion domain.

**Constructor**:
```python
Nexus(
    value: T,
    hooks: set[Hook[T]] = set(),
    logger: Optional[Logger] = None,
    nexus_manager: Optional[NexusManager] = None
)
```

**Properties**:
- `stored_value: T` — Current value (read-only)
- `previous_stored_value: T` — Previous value (read-only)
- `hooks: tuple[Hook[T], ...]` — Hooks in this fusion domain (read-only)

**Methods**:

#### `add_hook(hook)`
Add a hook to this Nexus.

**Parameters**:
- `hook: Hook[T]` — Hook to add

**Returns**:
- `tuple[bool, str]` — (success, message)

#### `remove_hook(hook)`
Remove a hook from this Nexus.

**Parameters**:
- `hook: Hook[T]` — Hook to remove

**Returns**:
- `tuple[bool, str]` — (success, message)

---

### NexusManager

```python
class NexusManager
```

Central coordinator for transitive synchronization and Nexus fusion (thread-safe).

**Constructor**:
```python
NexusManager(
    value_equality_callbacks: dict[tuple[type, type], Callable[[Any, Any], bool]] = {},
    registered_immutable_types: set[type] = set()
)
```

**Methods**:

#### `submit_values(nexus_and_values, mode="Normal submission", logger=None)`
Submit values to Nexuses - the central orchestration point for all value changes.

**Parameters**:
- `nexus_and_values: Mapping[Nexus[Any], Any] | Sequence[tuple[Nexus[Any], Any]]`
  — Mapping of Nexuses to their new values
- `mode: Literal["Normal submission", "Forced submission", "Check values"]`
  — Submission mode (default: "Normal submission")
- `logger: Optional[Logger]` — Optional logger for debugging

**Returns**:
- `tuple[bool, str]` — (success, message)

**Modes**:
- **"Normal submission"**: Only submits values that differ from current values
- **"Forced submission"**: Submits all values regardless of equality
- **"Check values"**: Only validates without updating

**Submission Protocol (6 Phases)**:
1. **Value Equality Check** — Skip if unchanged (Normal mode only)
2. **Value Completion** — Call `_add_values_to_be_updated()` on owners
3. **Collect Components** — Identify affected owners, hooks, publishers
4. **Validation** — Call `validate_complete_values_in_isolation()` on all owners
5. **Atomic Update** — Update all Nexuses simultaneously
6. **Notifications** — Invalidate, react, publish, notify listeners

**Example**:
```python
hook = nx.FloatingHook(10)
nexus = hook._get_nexus()
manager = DEFAULT_NEXUS_MANAGER

success, msg = manager.submit_values({nexus: 20})
```

#### `is_equal(value1, value2)`
Check if two values are equal using registered equality callbacks.

**Parameters**:
- `value1: Any` — First value
- `value2: Any` — Second value

**Returns**:
- `bool` — True if values are equal

**Note**: Use this method instead of `==` for value comparisons within the hook system.

#### `add_value_equality_callback(value_type_pair, callback)`
Register a custom equality callback for a pair of types.

**Parameters**:
- `value_type_pair: tuple[type, type]` — Tuple of types
- `callback: Callable[[Any, Any], bool]` — Equality function

**Example**:
```python
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Register custom equality for float comparisons
# Consider floats equal if they differ by less than 1e-9
def float_equality(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

DEFAULT_NEXUS_MANAGER.add_value_equality_callback(
    (float, float),
    float_equality
)

# Now float comparisons use the custom callback
hook = nx.FloatingHook(1.0)
hook.value = 1.0000000001  # Considered equal, no update triggered
```

### Custom Equality Checks

**Important**: Custom equality checks should be configured at the NexusManager level **before** creating hooks and x_objects.

#### Why Custom Equality Checks?

NexPy uses equality checks during Phase 1 (Value Equality Check) of the submission protocol to determine if a value has actually changed. By default, Python's `==` operator is used, but this may not be appropriate for all types:

- **Floating-point numbers**: Due to rounding errors, you may want to consider numbers "equal" if they're within a small tolerance (e.g., 1e-9)
- **Custom classes**: You may want domain-specific equality logic
- **Performance**: Optimized equality checks for large data structures

#### Standard Practice for Floating-Point Numbers

It's standard practice to register a custom equality callback for floating-point numbers:

```python
import nexpy as nx
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Configure BEFORE creating any hooks or x_objects
def float_equality(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), float_equality)

# Now create your hooks and x_objects
temperature = nx.XValue(20.0)
temperature.value = 20.0000000001  # No update triggered (considered equal)
```

#### Registering Custom Equality for Multiple Type Pairs

```python
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER
import numpy as np

# Float-Float comparison
def float_eq(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

# Float-Int comparison
def float_int_eq(a: float, b: int) -> bool:
    return abs(a - b) < 1e-9

# NumPy array comparison
def numpy_eq(a: np.ndarray, b: np.ndarray) -> bool:
    return np.allclose(a, b, rtol=1e-9, atol=1e-9)

# Register all callbacks before creating x_objects
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), float_eq)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, int), float_int_eq)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((int, float), lambda a, b: float_int_eq(b, a))
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((np.ndarray, np.ndarray), numpy_eq)
```

#### Best Practices

1. **Configure Early**: Register equality callbacks at application startup, before creating any hooks or x_objects
2. **Be Consistent**: Use the same tolerance/logic throughout your application
3. **Consider Cross-Type**: Register callbacks for cross-type comparisons (e.g., `float` vs `int`)
4. **Test Thoroughly**: Verify your equality logic handles edge cases (NaN, infinity, etc.)

#### Global vs Per-Manager Configuration

If you need different equality logic for different parts of your application, create separate NexusManager instances:

```python
import nexpy as nx
from nexpy.core.nexus_system.nexus_manager import NexusManager

# High-precision manager (1e-12 tolerance)
high_precision_manager = NexusManager()
high_precision_manager.add_value_equality_callback(
    (float, float),
    lambda a, b: abs(a - b) < 1e-12
)

# Low-precision manager (1e-6 tolerance)
low_precision_manager = NexusManager()
low_precision_manager.add_value_equality_callback(
    (float, float),
    lambda a, b: abs(a - b) < 1e-6
)

# Use specific managers
precise_value = nx.XValue(1.0, nexus_manager=high_precision_manager)
rough_value = nx.XValue(1.0, nexus_manager=low_precision_manager)
```

---

## Publisher-Subscriber

### Publisher

```python
class Publisher
```

Asynchronous publisher for decoupled notifications.

**Methods**:

#### `subscribe(subscriber)`
Subscribe a subscriber to this publisher.

**Parameters**:
- `subscriber: Subscriber` — Subscriber to add

#### `unsubscribe(subscriber)`
Unsubscribe a subscriber from this publisher.

**Parameters**:
- `subscriber: Subscriber` — Subscriber to remove

#### `publish(message)`
Publish a message to all subscribers (asynchronous).

**Parameters**:
- `message: Any` — Message to publish

---

### ValuePublisher

```python
class ValuePublisher(Generic[T])
```

Publisher that wraps a value and publishes on changes.

**Constructor**:
```python
ValuePublisher(
    initial_value: T
)
```

**Properties**:
- `value: T` — Current value (read/write)

---

### Subscriber

```python
class Subscriber
```

Asynchronous subscriber for receiving publications.

**Constructor**:
```python
Subscriber(
    callback: Callable[[Any], Awaitable[None]]
)
```

**Methods**:

#### `receive(message)`
Receive a published message (asynchronous).

**Parameters**:
- `message: Any` — Published message

---

## Protocols

### Hook

```python
@runtime_checkable
class Hook(Protocol[T])
```

Protocol for bidirectional hooks (send + receive).

**Required Properties**:
- `value: T` — Current value (read/write)

**Required Methods**:
- `join(other: Hook[T])` — Join with another hook
- `isolate()` — Isolate from fusion domain
- `is_joined_with(other: Hook[T]) -> bool` — Check if joined
- `add_listener(callback: Callable[[], None])` — Add listener
- `remove_listener(callback: Callable[[], None])` — Remove listener
- `submit_value(value: T) -> tuple[bool, str]` — Submit new value

---

### ReadOnlyHook

```python
@runtime_checkable
class ReadOnlyHook(Protocol[T])
```

Protocol for read-only hooks (receive only).

**Required Properties**:
- `value: T` — Current value (read-only)

**Required Methods**:
- `add_listener(callback: Callable[[], None])` — Add listener
- `remove_listener(callback: Callable[[], None])` — Remove listener

---

## Utilities

### write_report()

```python
def write_report() -> str
```

Generate a diagnostic report of the current hook system state.

**Returns**:
- `str` — Diagnostic report

**Example**:
```python
import nexpy as nx

# Create some hooks and objects
A = nx.FloatingHook(10)
B = nx.FloatingHook(20)
A.join(B)

# Generate report
report = nx.write_report()
print(report)
```

---

## Constants

### DEFAULT_NEXUS_MANAGER

```python
DEFAULT_NEXUS_MANAGER: NexusManager
```

Global singleton NexusManager used by default for all hooks and X objects.

---

## Next Steps

- **[Usage Guide](usage.md)** — Learn join/isolate mechanics
- **[Internal Synchronization](internal_sync.md)** — Understand atomic updates
- **[Examples](examples.md)** — See practical usage
- **[Concepts](concepts.md)** — Deep dive into theory

---

**[Back to README](../README.md)**

