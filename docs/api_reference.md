# API Reference

Complete API documentation for NexPy (nexpylib).

---

## Table of Contents

- [Core Hook Classes](#core-hook-classes)
- [Reactive Value Objects](#reactive-value-objects)
- [Reactive Collections](#reactive-collections)
- [Selection Objects](#selection-objects)
- [Adapter Objects](#adapter-objects)
- [Creating Custom X Objects](#creating-custom-x-objects)
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

### OwnedReadOnlyHook

```python
class OwnedReadOnlyHook(Generic[T, O])
```

Read-only hook owned by an X object, integrated with object's internal synchronization.

**Constructor**:
```python
OwnedReadOnlyHook(
    owner: O,
    value: T,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `value: T` — Current value (read-only)
- `owner: O` — The owning X object

**Methods**:
- `join(other: Hook[T])` — Join with another hook
- `isolate()` — Isolate from fusion domain
- `is_joined_with(other: Hook[T]) -> bool` — Check if joined
- `add_listener(callback: Callable[[], None])` — Add listener
- `remove_listener(callback: Callable[[], None])` — Remove listener
- `set_reaction_callback(callback: Callable[[], tuple[bool, str]])` — Set reaction callback
- `get_reaction_callback() -> Optional[Callable[[], tuple[bool, str]]]` — Get reaction callback
- `remove_reaction_callback()` — Remove reaction callback

**Key Differences from FloatingHook**:
- Read-only (no value setter)
- Validation delegated to owner object
- Participates in owner's internal synchronization
- Automatically triggers owner invalidation on changes

---

### OwnedWritableHook

```python
class OwnedWritableHook(Generic[T, O])
```

Writable hook owned by an X object, integrated with object's internal synchronization.

**Constructor**:
```python
OwnedWritableHook(
    owner: O,
    value: T,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Properties**:
- `value: T` — Current value (read/write)
- `owner: O` — The owning X object

**Methods**:
- `join(other: Hook[T])` — Join with another hook
- `isolate()` — Isolate from fusion domain
- `is_joined_with(other: Hook[T]) -> bool` — Check if joined
- `add_listener(callback: Callable[[], None])` — Add listener
- `remove_listener(callback: Callable[[], None])` — Remove listener
- `submit_value(value: T) -> tuple[bool, str]` — Submit new value
- `change_value(value: T, *, raise_submission_error_flag: bool = True) -> tuple[bool, str]` — Change value
- `set_reaction_callback(callback: Callable[[], tuple[bool, str]])` — Set reaction callback
- `get_reaction_callback() -> Optional[Callable[[], tuple[bool, str]]]` — Get reaction callback
- `remove_reaction_callback()` — Remove reaction callback

**Key Differences from OwnedReadOnlyHook**:
- Provides write access via `value` property setter
- Includes `change_value()` method for explicit updates
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

### XSetSingleSelect

```python
class XSetSingleSelect(Generic[T])
```

Single selection from a set with automatic synchronization.

**Constructor**:
```python
XSetSingleSelect(
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
options = nx.XSetSingleSelect({1, 2, 3, 4, 5}, selection=3)
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

## Adapter Objects

Adapter objects bridge between incompatible types, enabling connections between hooks with different type signatures while maintaining type safety and validation.

### XOptionalAdapter

```python
class XOptionalAdapter(Generic[T])
```

Adapter object that bridges between `T` and `Optional[T]`, blocking `None` values.

**Constructor**:
```python
XOptionalAdapter(
    hook_t_or_value: Hook[T] | ReadOnlyHook[T] | T | None,
    hook_optional: Hook[Optional[T]] | ReadOnlyHook[Optional[T]] | None = None,
    *,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Parameters**:
- `hook_t_or_value` — Either a non-None value or a Hook[T] to connect to the internal T hook
- `hook_optional` — Either a Hook[Optional[T]] to connect to the internal Optional[T] hook, or None
- At least one parameter must be provided

**Properties**:
- `hook_t: Hook[T]` — The T hook (left side, non-None values)
- `hook_optional: Hook[Optional[T]]` — The Optional[T] hook (right side, allows None)

**Invariants**:
- `hook_t` never contains `None` values
- `hook_optional` can contain `None` or non-None values
- Both hooks are always synchronized

**Example**:
```python
# Initialize with a non-None value
adapter = nx.XOptionalAdapter[int](
    hook_t_or_value=42,
    hook_optional=None
)
print(adapter.hook_t.value)      # 42
print(adapter.hook_optional.value)  # 42

# Update via T hook
adapter.hook_t.value = 100
print(adapter.hook_optional.value)  # 100

# Update via Optional hook
adapter.hook_optional.value = 200
print(adapter.hook_t.value)      # 200

# This would raise an error - cannot set None on T hook
# adapter.hook_t.value = None  # SubmissionError
```

---

### XIntFloatAdapter

```python
class XIntFloatAdapter
```

Adapter object that bridges between `int` and `float`, validating that float values are integer-valued.

**Constructor**:
```python
XIntFloatAdapter(
    hook_int_or_value: Hook[int] | ReadOnlyHook[int] | int | None,
    hook_float: Hook[float] | ReadOnlyHook[float] | None = None,
    *,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Parameters**:
- `hook_int_or_value` — Either an integer value or a Hook[int] to connect to the internal int hook
- `hook_float` — Either a Hook[float] to connect to the internal float hook, or None
- At least one parameter must be provided

**Properties**:
- `hook_int: Hook[int]` — The int hook (left side, integer values)
- `hook_float: Hook[float]` — The float hook (right side, integer-valued floats)

**Invariants**:
- `hook_int` always contains integer values
- `hook_float` only contains integer-valued floats (where `float.is_integer() == True`)
- Both hooks are always synchronized

**Example**:
```python
# Initialize with an integer
adapter = nx.XIntFloatAdapter(
    hook_int_or_value=42,
    hook_float=None
)
print(adapter.hook_int.value)    # 42
print(adapter.hook_float.value)  # 42.0

# Update via int hook
adapter.hook_int.value = 100
print(adapter.hook_float.value)  # 100.0

# Update via float hook (integer-valued)
adapter.hook_float.value = 200.0
print(adapter.hook_int.value)    # 200

# This would raise an error - non-integer float
# adapter.hook_float.value = 42.5  # SubmissionError
```

---

### XSetSequenceAdapter

```python
class XSetSequenceAdapter(Generic[T])
```

Adapter object that bridges between `AbstractSet` and `Sequence`, validating that sequences have unique elements.

**Constructor**:
```python
XSetSequenceAdapter(
    hook_set_or_value: Hook[AbstractSet[T]] | ReadOnlyHook[AbstractSet[T]] | AbstractSet[T] | None,
    hook_sequence: Hook[Sequence[T]] | ReadOnlyHook[Sequence[T]] | Sequence[T] | None = None,
    *,
    sort_callable: Callable[[AbstractSet[T]], Sequence[T]] = sorted,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Parameters**:
- `hook_set_or_value` — Either a set/frozenset value or a Hook[AbstractSet[T]] to connect to the internal set hook
- `hook_sequence` — Either a Hook[Sequence[T]] to connect to the internal sequence hook, or None
- `sort_callable` — Function to convert an AbstractSet to a Sequence (default: `sorted`)
- At least one parameter must be provided

**Properties**:
- `hook_set: Hook[AbstractSet[T]]` — The set hook (left side, unique elements)
- `hook_sequence: Hook[Sequence[T]]` — The sequence hook (right side, unique elements in sequence)

**Invariants**:
- `hook_set` contains unique elements (any set/frozenset)
- `hook_sequence` only contains sequences with unique elements (no duplicates)
- Both hooks are always synchronized
- Order from set to sequence is controlled by the `sort_callable`

**Example**:
```python
# Initialize with a set (default sorted order)
adapter = nx.XSetSequenceAdapter[int](
    hook_set_or_value={3, 1, 2},
    hook_sequence=None
)
print(adapter.hook_set.value)      # {3, 1, 2}
print(adapter.hook_sequence.value) # [1, 2, 3] (sorted)

# Custom sorting function
adapter = nx.XSetSequenceAdapter[int](
    hook_set_or_value={3, 1, 2},
    hook_sequence=None,
    sort_callable=lambda s: list(reversed(sorted(s)))
)
print(adapter.hook_sequence.value) # [3, 2, 1] (reverse sorted)

# Update via sequence hook
adapter.hook_sequence.value = [4, 5, 6]
print(adapter.hook_set.value)      # {4, 5, 6}

# This would raise an error - sequence with duplicates
# adapter.hook_sequence.value = [1, 2, 2]  # SubmissionError
```

**Sort Callable Examples**:
```python
# Default sorted (returns list)
adapter = nx.XSetSequenceAdapter({3, 1, 2}, sort_callable=sorted)
print(adapter.hook_sequence.value)  # [1, 2, 3]

# Custom tuple sorting
adapter = nx.XSetSequenceAdapter(
    {3, 1, 2}, 
    sort_callable=lambda s: tuple(sorted(s))
)
print(adapter.hook_sequence.value)  # (1, 2, 3)

# Reverse order
adapter = nx.XSetSequenceAdapter(
    {3, 1, 2}, 
    sort_callable=lambda s: list(reversed(sorted(s)))
)
print(adapter.hook_sequence.value)  # [3, 2, 1]

# No sorting (preserve arbitrary order)
adapter = nx.XSetSequenceAdapter(
    {3, 1, 2}, 
    sort_callable=list
)
print(adapter.hook_sequence.value)  # [3, 1, 2] (arbitrary order)
```

---

## Creating Custom X Objects

NexPy provides two base classes for creating custom reactive objects with full integration into the synchronization system:

### XSimpleBase

```python
class XSimpleBase(Generic[T])
```

Base class for creating custom X objects that wrap a **single value**.

**Use Cases:**
- Custom reactive wrappers around domain objects
- Validated single-value containers
- Specialized value types with custom behavior

**Constructor**:
```python
XSimpleBase(
    value_or_hook: T | Hook[T] | ReadOnlyHook[T] | CarriesSingleHookProtocol[T],
    validate_value_callback: Optional[Callable[[T], tuple[bool, str]]] = None,
    invalidate_after_update_callback: Optional[Callable[[], None]] = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Parameters**:
- `value_or_hook` — Initial value or hook to join
- `validate_value_callback` — Optional validation function for the value
- `invalidate_after_update_callback` — Optional callback executed after successful state changes
- `logger` — Optional logger for debugging
- `nexus_manager` — NexusManager instance (default: global manager)

**Properties Provided**:
- `value: T` — The wrapped value (read/write)
- `value_hook: Hook[T]` — The underlying hook for fusion operations

**Example: Custom Validated Value**:
```python
import nexpy as nx
from nexpy import XSimpleBase

class PositiveNumber(XSimpleBase[float]):
    """A number that must always be positive."""
    
    def __init__(self, value: float):
        def validate_positive(val: float) -> tuple[bool, str]:
            if val > 0:
                return True, "Valid positive number"
            return False, "Value must be positive"
        
        super().__init__(
            value_or_hook=value,
            validate_value_callback=validate_positive
        )

# Usage
num = PositiveNumber(10.0)
print(num.value)  # 10.0

num.value = 20.0  # OK
# num.value = -5.0  # Raises ValueError: Value must be positive
```

**Example: Custom Domain Object Wrapper**:
```python
import nexpy as nx
from nexpy import XSimpleBase
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
    age: int

class ReactiveUser(XSimpleBase[User]):
    """Reactive wrapper for User objects."""
    
    def __init__(self, user: User):
        def validate_user(u: User) -> tuple[bool, str]:
            if u.age < 0:
                return False, "Age cannot be negative"
            if "@" not in u.email:
                return False, "Invalid email"
            return True, "Valid user"
        
        super().__init__(
            value_or_hook=user,
            validate_value_callback=validate_user
        )
    
    @property
    def name(self) -> str:
        return self.value.name
    
    @property
    def email(self) -> str:
        return self.value.email

# Usage
user = ReactiveUser(User("Alice", "alice@example.com", 30))

# Add listener for changes
user.value_hook.add_listener(lambda: print(f"User changed: {user.name}"))

# Update user
user.value = User("Bob", "bob@example.com", 25)
```

---

### XCompositeBase

```python
class XCompositeBase(Generic[PHK, SHK, PHV, SHV, O])
```

Base class for creating custom X objects with **multiple related hooks** and internal synchronization.

**Use Cases:**
- Objects with multiple interdependent properties
- Selection objects (dict/set selections)
- Complex stateful objects requiring atomic updates
- Objects with computed/derived values

**Type Parameters**:
- `PHK` — Type of primary hook keys (e.g., `Literal["dict", "key"]`)
- `SHK` — Type of secondary hook keys (e.g., `Literal["keys", "values"]`)
- `PHV` — Type of primary hook values (e.g., `dict | str`)
- `SHV` — Type of secondary hook values (e.g., `set | list`)
- `O` — The class type itself (for self-referential typing)

**Constructor**:
```python
XCompositeBase(
    initial_hook_values: Mapping[PHK, PHV | OwnedHookProtocol[PHV]],
    compute_missing_primary_values_callback: Optional[Callable[[O, UpdateFunctionValues[PHK, PHV]], Mapping[PHK, PHV]]],
    compute_secondary_values_callback: Optional[Mapping[SHK, Callable[[Mapping[PHK, PHV]], SHV]]],
    validate_complete_primary_values_callback: Optional[Callable[[Mapping[PHK, PHV]], tuple[bool, str]]],
    invalidate_after_update_callback: Optional[Callable[[], None]] = None,
    validate_complete_values_custom_callback: Optional[Callable[[Mapping[PHK|SHK, PHV|SHV]], tuple[bool, str]]] = None,
    output_value_wrapper: Optional[Mapping[PHK|SHK, Callable[[PHV|SHV], PHV|SHV]]] = None,
    logger: Optional[Logger] = None,
    nexus_manager: NexusManager = DEFAULT_NEXUS_MANAGER
)
```

**Key Parameters**:

1. **`initial_hook_values`** (required)
   - Initial values for primary hooks
   - These represent the core mutable state

2. **`compute_missing_primary_values_callback`** (required, can be None)
   - Computes additional primary values needed to complete partial updates
   - Example: When key changes, compute the corresponding value

3. **`compute_secondary_values_callback`** (required, can be None)
   - Mapping of secondary hook keys to calculation functions
   - Secondary hooks are read-only and derived from primary values

4. **`validate_complete_primary_values_callback`** (required, can be None)
   - Validates that primary values form a valid state
   - Called FIRST during validation (validates ONLY primary values)

5. **`validate_complete_values_custom_callback`** (optional) **[NEW]**
   - Additional custom validation across ALL values (primary + secondary)
   - Called SECOND after primary validation and secondary computation
   - Allows cross-validation between primary and derived values

6. **`invalidate_after_update_callback`** (optional)
   - Called after successful state changes
   - Use for external side effects

**Example: Simple Multi-Property Object**:
```python
import nexpy as nx
from nexpy import XCompositeBase
from typing import Literal

class Rectangle(XCompositeBase[
    Literal["width", "height"],  # Primary keys
    Literal["area"],              # Secondary keys
    float,                        # Primary value type
    float,                        # Secondary value type
    "Rectangle"                   # Self type
]):
    def __init__(self, width: float, height: float):
        # Define how to compute area from width and height
        def compute_area(primary_values):
            return primary_values["width"] * primary_values["height"]
        
        # Validate that dimensions are positive
        def validate_dimensions(primary_values):
            if primary_values["width"] <= 0 or primary_values["height"] <= 0:
                return False, "Dimensions must be positive"
            return True, "Valid dimensions"
        
        super().__init__(
            initial_hook_values={
                "width": width,
                "height": height
            },
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={
                "area": compute_area
            },
            validate_complete_primary_values_callback=validate_dimensions
        )
    
    @property
    def width(self) -> float:
        return self._get_primary_hook("width").value
    
    @width.setter
    def width(self, value: float):
        self._submit_primary_values({"width": value})
    
    @property
    def height(self) -> float:
        return self._get_primary_hook("height").value
    
    @height.setter
    def height(self, value: float):
        self._submit_primary_values({"height": value})
    
    @property
    def area(self) -> float:
        return self._get_secondary_hook("area").value

# Usage
rect = Rectangle(10.0, 5.0)
print(rect.area)  # 50.0

rect.width = 20.0
print(rect.area)  # 100.0 (automatically updated)
```

**Example: With Custom Validator**:
```python
import nexpy as nx
from nexpy import XCompositeBase
from typing import Literal

class BoundedValue(XCompositeBase[
    Literal["value", "min", "max"],  # Primary
    Literal["range"],                 # Secondary
    float,                            # Primary type
    float,                            # Secondary type
    "BoundedValue"
]):
    def __init__(self, value: float, min_val: float, max_val: float):
        def compute_range(primary):
            return primary["max"] - primary["min"]
        
        def validate_bounds(primary):
            if primary["min"] >= primary["max"]:
                return False, "Min must be less than max"
            if not (primary["min"] <= primary["value"] <= primary["max"]):
                return False, "Value must be within bounds"
            return True, "Valid"
        
        # NEW: Custom validator across all values
        def custom_validate_all(all_values):
            # Can validate relationships between primary and secondary
            if all_values["range"] <= 0:
                return False, "Range must be positive"
            # Ensure value is centered within 10% of range
            center = (all_values["min"] + all_values["max"]) / 2
            if abs(all_values["value"] - center) > all_values["range"] * 0.1:
                return False, "Value must be near center"
            return True, "Valid"
        
        super().__init__(
            initial_hook_values={
                "value": value,
                "min": min_val,
                "max": max_val
            },
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={
                "range": compute_range
            },
            validate_complete_primary_values_callback=validate_bounds,
            validate_complete_values_custom_callback=custom_validate_all  # NEW
        )

# Usage
bounded = BoundedValue(5.0, 0.0, 10.0)
print(bounded._get_primary_hook("value").value)  # 5.0
print(bounded._get_secondary_hook("range").value)  # 10.0
```

---

### Custom Validator Feature

**What's New:** All X objects now support an optional `custom_validator` callback that provides additional validation beyond the standard internal validation.

**Validation Order:**

1. **Primary Validation** (`validate_complete_primary_values_callback`)
   - Validates primary values only
   - Checks basic invariants (e.g., key exists in dict)

2. **Secondary Computation**
   - Secondary values are computed from validated primary values

3. **Custom Validation** (`validate_complete_values_custom_callback`) **[NEW]**
   - Validates ALL values (primary + secondary)
   - Allows cross-validation between primary and derived values
   - Optional additional validation logic

**Use Cases for Custom Validators:**

1. **Cross-validation between primary and derived values**
   ```python
   def custom_validate(all_values):
       # Ensure computed value meets criteria
       if all_values["computed_metric"] < all_values["threshold"]:
           return False, "Computed metric below threshold"
       return True, "Valid"
   ```

2. **Complex business rules**
   ```python
   def custom_validate(all_values):
       # Complex rule involving multiple values
       if all_values["status"] == "active":
           if all_values["count"] == 0:
               return False, "Active items must have count > 0"
       return True, "Valid"
   ```

3. **Consistency checks across all properties**
   ```python
   def custom_validate(all_values):
       # Ensure consistency across object
       total = sum(all_values[f"part_{i}"] for i in range(5))
       if abs(total - all_values["total"]) > 0.001:
           return False, "Parts don't sum to total"
       return True, "Valid"
   ```

**Example 1: Selection with Custom Validator**:
```python
import nexpy as nx
from nexpy import XCompositeBase
from typing import Literal

class ValidatedSelection(XCompositeBase[
    Literal["options", "selection"],
    Literal["count"],
    set[str] | str,
    int,
    "ValidatedSelection"
]):
    def __init__(self, options: set[str], selection: str):
        def compute_count(primary):
            return len(primary["options"])
        
        def validate_primary(primary):
            if primary["selection"] not in primary["options"]:
                return False, "Selection not in options"
            return True, "Valid"
        
        # NEW: Custom validator ensures minimum options
        def custom_validate(all_values):
            if all_values["count"] < 2:
                return False, "Must have at least 2 options"
            return True, "Valid"
        
        super().__init__(
            initial_hook_values={
                "options": options,
                "selection": selection
            },
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={
                "count": compute_count
            },
            validate_complete_primary_values_callback=validate_primary,
            validate_complete_values_custom_callback=custom_validate
        )

# Usage
sel = ValidatedSelection({"a", "b", "c"}, "a")  # OK

# This would fail the custom validator:
# sel2 = ValidatedSelection({"a"}, "a")  # Error: Must have at least 2 options
```

**Example 2: XSubscriber - Using Custom Validator Only**:
```python
import nexpy as nx
from nexpy import XCompositeBase, Publisher
from typing import Mapping

# XSubscriber shows a pattern where you may want ONLY custom validation
# (no primary validation needed)

class XSubscriber(XCompositeBase[str, None, float, None, "XSubscriber"]):
    def __init__(
        self,
        publisher: Publisher,
        on_publication_callback: Callable[[None|Publisher], Mapping[str, float]],
        custom_validator: Optional[Callable[[Mapping[str, float]], tuple[bool, str]]] = None
    ):
        initial_values = on_publication_callback(None)
        
        # Use custom_validator to validate the complete mapping
        super().__init__(
            initial_hook_values=initial_values,
            compute_missing_primary_values_callback=None,
            compute_secondary_values_callback={},
            validate_complete_primary_values_callback=None,  # No primary validation
            validate_complete_values_custom_callback=custom_validator,  # Only custom validation
            invalidate_after_update_callback=None
        )
        
        publisher.add_subscriber(self)

# Usage
def get_sensor_data(pub):
    if pub is None:
        return {"temp": 20.0, "humidity": 50.0}
    return {"temp": read_temp(), "humidity": read_humidity()}

def validate_sensor_data(values):
    if values["temp"] < -50 or values["temp"] > 100:
        return False, "Temperature out of range"
    if values["humidity"] < 0 or values["humidity"] > 100:
        return False, "Humidity out of range"
    return True, "Valid"

sensor = XSubscriber(
    publisher=my_publisher,
    on_publication_callback=get_sensor_data,
    custom_validator=validate_sensor_data
)
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

### Nexus

```python
class Nexus(Generic[T])
```

Shared synchronization core for transitive hook fusion. A Nexus represents a fusion domain — a group of hooks that share the same value and are synchronized together.

**Properties**:
- `stored_value: T` — The current value stored in this nexus
- `previous_stored_value: T` — The previous value (before last update)
- `nexus_id: str` — Unique identifier for this nexus
- `creation_time: float` — Unix timestamp when this nexus was created
- `hooks: tuple[HookWithConnectionProtocol[T], ...]` — All hooks in this nexus

**Methods**:
- `add_hook(hook)` — Add a hook to this nexus
- `remove_hook(hook)` — Remove a hook from this nexus

**String Representation**:
- `str(nexus)` — `HookNexus(id={nexus_id}, v={value})`
- `repr(nexus)` — `HookNexus(id={nexus_id}, v={value}, {hook_count} hooks)`

**Example**:
```python
hook = nx.FloatingHook(42)
nexus = hook._get_nexus()

print(f"Nexus ID: {nexus.nexus_id}")  # Output: nexus_1
print(f"Created: {time.ctime(nexus.creation_time)}")
print(f"Value: {nexus.stored_value}")
print(f"Hooks: {len(nexus.hooks)}")
```

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

#### `get_active_nexuses()`
Get all currently active nexuses registered with this manager.

**Returns**:
- `list[Nexus[Any]]` — List of active nexuses. Dead references are automatically cleaned up.

**Example**:
```python
manager = nx.default.NEXUS_MANAGER
active_nexuses = manager.get_active_nexuses()

for nexus in active_nexuses:
    print(f"Nexus ID: {nexus.nexus_id}")
    print(f"Value: {nexus.stored_value}")
    print(f"Creation time: {nexus.creation_time}")
    print(f"Hooks: {len(nexus.hooks)}")
```

#### `get_nexus_count()`
Get the number of currently active nexuses.

**Returns**:
- `int` — Number of active nexuses registered with this manager.

**Example**:
```python
manager = nx.default.NEXUS_MANAGER
print(f"Active nexuses: {manager.get_nexus_count()}")
```

### Nexus Tracking

The NexusManager automatically tracks all active nexuses using weak references, enabling runtime monitoring of fusion domain evolution. Each nexus has a unique ID and creation timestamp for debugging and analysis purposes.

**Nexus Properties**:
- `nexus_id: str` — Unique identifier (format: `nexus_{id}` where id is an incrementing counter)
- `creation_time: float` — Unix timestamp when the nexus was created

**Use Cases**:
- **Debugging**: Track how fusion domains evolve during hook connections
- **Performance Analysis**: Monitor nexus creation and destruction patterns
- **System Introspection**: Understand the current state of the synchronization system

**Example**:
```python
import nexpy as nx
import time

# Create hooks and observe nexus evolution
hook1 = nx.FloatingHook(42)
hook2 = nx.FloatingHook(100)

manager = nx.default.NEXUS_MANAGER
print(f"Initial nexuses: {manager.get_nexus_count()}")

# Join hooks - creates fusion
hook1.join(hook2)
print(f"After fusion: {manager.get_nexus_count()}")

# Inspect active nexuses
for nexus in manager.get_active_nexuses():
    print(f"Nexus {nexus.nexus_id}: {nexus.stored_value} ({len(nexus.hooks)} hooks)")
    # Output: Nexus nexus_1: 100 (2 hooks)
```

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

