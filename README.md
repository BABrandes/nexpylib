# NexPy — Transitive Synchronization and Shared-State Fusion for Python

**NexPy** (distributed on PyPI as `nexpylib`) is a reactive synchronization framework for Python that provides a universal mechanism for maintaining coherent shared state across independent objects through **Nexus fusion** and **internal Hook synchronization**.

[![PyPI version](https://img.shields.io/pypi/v/nexpylib.svg)](https://pypi.org/project/nexpylib/)
[![Python versions](https://img.shields.io/pypi/pyversions/nexpylib.svg)](https://pypi.org/project/nexpylib/)
[![License](https://img.shields.io/github/license/babrandes/nexpylib.svg)](https://github.com/babrandes/nexpylib/blob/main/LICENSE)

---

## 🎯 Core Concept: Inter-Object Synchronization via Nexus Fusion

Unlike traditional reactive frameworks that propagate changes through dependency graphs, NexPy creates **fusion domains** where multiple hooks share a single **Nexus**—a centralized synchronization core that holds and propagates state.

### What is a Nexus?

A **Nexus** is a shared synchronization core that represents a fusion domain. Each Hook in NexPy references a Nexus, but **does not own it**—instead, multiple hooks may share the same Nexus, forming a dynamic network of coherence.

### What is Nexus Fusion?

When two hooks are **joined**, their respective Nexuses undergo a **fusion process**:

1. **Original Nexuses are destroyed** — Both hooks' previous Nexuses cease to exist
2. **New unified Nexus is created** — A single Nexus is created to hold the shared value
3. **Both hooks join the same fusion domain** — They now share synchronized state

This joining is:
- **Symmetric** — `A.join(B)` is equivalent to `B.join(A)`
- **Transitive** — Joining creates equivalence chains across all connected hooks
- **Non-directional** — There's no "master" or "slave"; all hooks are equal participants

### Transitive Synchronization Example

```python
import nexpy as nx

A = nx.Hook(1)
B = nx.Hook(2)
C = nx.Hook(3)
D = nx.Hook(4)

# Create first fusion domain
A.join(B)  # → creates Nexus_AB containing A and B

# Create second fusion domain
C.join(D)  # → creates Nexus_CD containing C and D

# Fuse both domains by connecting any pair
B.join(C)  # → fuses both domains → Nexus_ABCD

# All four hooks now share the same Nexus and value
# Even though A and D were never joined directly!
print(A.value, B.value, C.value, D.value)  # All have the same value

# Changing any hook updates all hooks in the fusion domain
A.value = 42
print(A.value, B.value, C.value, D.value)  # 42 42 42 42
```

### Hook Isolation

A hook can later be **isolated**, which:
- Removes it from its current fusion domain
- Creates a new, independent Nexus initialized with the hook's current value
- Leaves remaining hooks still joined and synchronized

```python
import nexpy as nx

A = nx.Hook(1)
B = nx.Hook(1)
C = nx.Hook(1)

A.join(B)
B.join(C)
# All share Nexus_ABC

B.isolate()
# B now has a fresh Nexus_B
# A and C remain joined via Nexus_AC

A.value = 10
print(A.value, B.value, C.value)  # 10 1 10
```

---

## ⚛️ Internal Synchronization: Intra-Object Coherence

In addition to global fusion, NexPy maintains **atomic internal synchronization** among related hooks within a single object through a **transaction-like validation and update protocol**.

### Example: XDictSelect — Multi-Hook Atomic Synchronization

`XDictSelect` exposes **5 synchronized hooks**: `dict`, `keys`, `values`, `key`, and `value`.

```python
import nexpy as nx

# Create a selection dict that maintains consistency between
# the dict, selected key, and corresponding value
select = nx.XDictSelect({"a": 1, "b": 2, "c": 3}, key="a")

# All hooks are synchronized
print(select.dict_hook.value)   # {"a": 1, "b": 2, "c": 3}
print(select.key_hook.value)    # "a"
print(select.value_hook.value)  # 1

# Changing the key automatically updates the value
select.key = "b"
print(select.value)  # 2

# Changing the value updates the dictionary
select.value = 20
print(select.dict)  # {"a": 1, "b": 20, "c": 3}

# All changes maintain invariants atomically
```

### The Internal Synchronization Protocol

When one hook changes (e.g., `key`), NexPy:

1. **Determines affected Nexuses** — Which related Nexuses must update (e.g., `value`, `dict`)
2. **Readiness check (validation pre-step)** — Queries each affected Nexus via validation callbacks
3. **Atomic update** — If all Nexuses report readiness, applies all updates in one transaction
4. **Rejection** — Otherwise rejects the change to maintain global validity

This ensures the system is:
- **Atomic** — All updates occur together or not at all
- **Consistent** — Constraints are always satisfied
- **Isolated** — Concurrent modifications are safely locked
- **Durable (logical)** — Once accepted, coherence persists until the next explicit change

NexPy guarantees **continuous validity** both within objects (internal sync) and across objects (Nexus fusion).

---

## 🚀 Quick Start

### Installation

```bash
pip install nexpylib
```

### Basic Usage

#### 1. Simple Reactive Value

```python
import nexpy as nx

# Create a reactive value
value = nx.XValue(42)

# Read the value
print(value.value)  # 42

# Update the value
value.value = 100
print(value.value)  # 100

# Add a listener that reacts to changes
def on_change():
    print(f"Value changed to: {value.value}")

value.value_hook.add_listener(on_change)
value.value = 200  # Prints: "Value changed to: 200"
```

#### 2. Hook Fusion Across Independent Objects

```python
import nexpy as nx

# Create two independent reactive values
temperature_sensor = nx.XValue(20.0)
display_value = nx.XValue(0.0)

# Fuse them so they share the same state
temperature_sensor.value_hook.join(display_value.value_hook)

# Now they're synchronized
print(temperature_sensor.value, display_value.value)  # 20.0 20.0

# Changing one updates the other
temperature_sensor.value = 25.5
print(display_value.value)  # 25.5
```

#### 3. Reactive Collections

```python
import nexpy as nx

# Reactive list
numbers = nx.XList([1, 2, 3])
numbers.list_hook.add_listener(lambda: print(f"List changed: {numbers.list}"))

numbers.append(4)  # Prints: "List changed: [1, 2, 3, 4]"

# Reactive set
tags = nx.XSet({"python", "reactive"})
tags.add("framework")
print(tags.set)  # {"python", "reactive", "framework"}

# Reactive dict
config = nx.XDict({"debug": False, "version": "1.0"})
config["debug"] = True
print(config.dict)  # {"debug": True, "version": "1.0"}
```

#### 4. Selection Objects with Internal Synchronization

```python
import nexpy as nx

# Create a selection from a dictionary
options = nx.XDictSelect(
    {"low": 1, "medium": 5, "high": 10},
    key="medium"
)

print(options.key)    # "medium"
print(options.value)  # 5

# Change selection
options.key = "high"
print(options.value)  # 10 (automatically updated)

# Modify value (updates dict atomically)
options.value = 15
print(options.dict)  # {"low": 1, "medium": 5, "high": 15}
```

#### 5. Adapter Objects for Type Bridging

```python
import nexpy as nx

# Bridge between int and Optional[int] (blocks None on the T side)
optional_adapter = nx.XOptionalAdapter[int](
    hook_t_or_value=42,
    hook_optional=None
)

print(optional_adapter.hook_t.value)      # 42
print(optional_adapter.hook_optional.value)  # 42

# Update via either hook - they stay synchronized
optional_adapter.hook_t.value = 100
print(optional_adapter.hook_optional.value)  # 100

# Bridge between set and sequence with custom sorting
set_seq_adapter = nx.XSetSequenceAdapter[int](
    hook_set_or_value={3, 1, 2},
    hook_sequence=None,
    sort_callable=lambda s: list(reversed(sorted(s)))  # Reverse order
)

print(set_seq_adapter.hook_set.value)      # {3, 1, 2}
print(set_seq_adapter.hook_sequence.value) # [3, 2, 1] (reverse sorted)
```

#### 6. Configuring Floating-Point Tolerance

```python
import nexpy as nx
from nexpy import default

# Configure BEFORE creating any observables
# Adjust tolerance based on your use case:
# - UI applications: 1e-6 to 1e-3 (more lenient)
# - General purpose: 1e-9 (default)
# - Scientific: 1e-12 to 1e-15 (high precision)

default.FLOAT_ACCURACY = 1e-6  # Lenient for UI work

# Now floating-point comparisons use the configured tolerance
temperature = nx.XValue(20.0)
temperature.value = 20.0000001  # No update (within tolerance)
temperature.value = 20.001  # Update triggered (exceeds tolerance)
```

---

## 📚 Key Features

### 🔗 Transitive Hook Fusion
- Join any hooks to create fusion domains
- Transitive synchronization: `A→B` + `B→C` = `A→B→C`
- Symmetric and non-directional connections
- Isolate hooks to break fusion domains

### ⚛️ Atomic Internal Synchronization
- ACID-like guarantees for multi-hook objects
- Transaction-style validation and updates
- Automatic constraint maintenance
- Continuous validity enforcement

### 🔄 Reactive Collections
- `XList` — Reactive lists with element access
- `XSet` — Reactive sets with membership tracking
- `XDict` — Reactive dictionaries with key-value pairs
- Full Python collection protocol support

### 🎯 Selection Objects
- `XDictSelect` — Select key-value pairs from dicts
- `XSetSingleSelect` — Select single elements from sets
- `XSetMultiSelect` — Multiple selection support
- Optional selection variants (allow `None` selection)

### 🔄 Adapter Objects
- `XOptionalAdapter` — Bridge between `T` and `Optional[T]` (blocks `None`)
- `XIntFloatAdapter` — Bridge between `int` and `float` (validates integer-valued floats)
- `XSetSequenceAdapter` — Bridge between `AbstractSet` and `Sequence` (validates unique elements)
- Custom sorting control for set-to-sequence conversion
- Type-safe bridging between incompatible hook types

### 🔒 Thread-Safe by Design
- All operations protected by reentrant locks
- Safe concurrent access from multiple threads
- Reentrancy protection against recursive modifications
- Independent nested submissions allowed

### 🎭 Multiple Notification Philosophies
1. **Listeners (Synchronous)** — Direct callbacks during updates
2. **Publish-Subscribe (Asynchronous)** — Decoupled async notifications
3. **Hooks (Bidirectional Validation)** — Enforce constraints across objects

### 🎯 Custom Equality Checks
- Built-in floating-point tolerance (configurable via `default.FLOAT_ACCURACY`)
- Standard practice: 1e-9 tolerance to avoid spurious updates
- Cross-type comparison support (e.g., `float` vs `int`)
- Register custom equality callbacks for specialized types at the NexusManager level

---

## 📖 Documentation

- **[Usage Guide](docs/usage.md)** — Join/isolate mechanics, Hook basics, Nexus fusion
- **[Internal Synchronization](docs/internal_sync.md)** — Atomic updates and validation protocol
- **[Architecture](docs/architecture.md)** — Design philosophy, data flow, locking
- **[API Reference](docs/api_reference.md)** — Complete API documentation
- **[Examples](docs/examples.md)** — Practical examples and runnable code
- **[Concepts](docs/concepts.md)** — Deep dive into fusion domains and synchronization

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Objects                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ XValue   │  │ XDict    │  │ XList    │  │ XSet     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │          Hook Layer               │
        │  (Owned Hooks + Floating Hooks)   │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │         Nexus Layer               │
        │  (Fusion Domains + Shared State)  │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │       NexusManager                │
        │  (Coordination + Validation)      │
        └───────────────────────────────────┘
```

**Key Components:**

- **Hooks** — Connection points that reference Nexuses
- **Nexus** — Shared synchronization core for fusion domains
- **NexusManager** — Central coordinator for validation and updates
- **X Objects** — High-level reactive data structures

---

## 🎓 Use Cases

### 1. GUI Data Binding

```python
import nexpy as nx

# Model
user_name = nx.XValue("Alice")

# View (simulated)
class TextWidget:
    def __init__(self, hook):
        self.hook = hook
        hook.add_listener(self.refresh)
    
    def refresh(self):
        print(f"Display: {self.hook.value}")

widget = TextWidget(user_name.value_hook)

# Changing model updates view automatically
user_name.value = "Bob"  # Display: Bob
```

### 2. Configuration Synchronization

```python
import nexpy as nx

# Multiple configuration stores that stay in sync
app_config = nx.XDict({"theme": "dark", "lang": "en"})
cache_config = nx.XDict({})

# Fuse configuration hooks
cache_config.dict_hook.join(app_config.dict_hook)

# Both stay synchronized
app_config["theme"] = "light"
print(cache_config["theme"])  # "light"
```

### 3. State Machines with Atomic Transitions

```python
import nexpy as nx

states = {"idle", "running", "paused", "stopped"}
current = nx.XDictSelect(
    {state: state for state in states},
    key="idle"
)

def validate_transition(values):
    # Add custom validation logic
    if values["key"] == "running" and some_condition:
        return False, "Cannot transition to running"
    return True, "Valid"

# Transitions are atomic and validated
try:
    current.key = "running"
except ValueError as e:
    print(f"Transition rejected: {e}")
```

---

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/babrandes/nexpylib.git
cd nexpylib

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

---

## 📄 License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **PyPI**: [https://pypi.org/project/nexpylib/](https://pypi.org/project/nexpylib/)
- **GitHub**: [https://github.com/babrandes/nexpylib](https://github.com/babrandes/nexpylib)
- **Documentation**: [https://github.com/babrandes/nexpylib#readme](https://github.com/babrandes/nexpylib#readme)
- **Issue Tracker**: [https://github.com/babrandes/nexpylib/issues](https://github.com/babrandes/nexpylib/issues)

---

## 🎯 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes between versions.

---

## ⭐ Star History

If you find NexPy useful, please consider starring the repository on GitHub!

---

**Built with ❤️ by Benedikt Axel Brandes**
