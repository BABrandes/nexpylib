# Architecture

This document explains NexPy's design philosophy, architectural layers, data flow, locking strategy, and key design decisions.

---

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [Architectural Layers](#architectural-layers)
- [Data Flow](#data-flow)
- [Locking Strategy](#locking-strategy)
- [Nexus Fusion Mechanics](#nexus-fusion-mechanics)
- [Validation Cycle](#validation-cycle)
- [Notification Philosophies](#notification-philosophies)
- [Memory Management](#memory-management)
- [Performance Characteristics](#performance-characteristics)

---

## Design Philosophy

### Core Principles

NexPy is built on several foundational principles:

#### 1. **Explicit State Sharing Through Fusion**

Unlike traditional reactive frameworks that propagate changes through dependency graphs, NexPy creates **fusion domains** where hooks *share* a single source of truth (the Nexus).

```
Traditional Reactive (Dependency Propagation):
A → B → C → D
(Changes flow through edges)

NexPy (Fusion Domains):
     Nexus_ABCD
    /    |    \   \
   A     B     C    D
(All hooks reference the same Nexus)
```

**Advantages:**
- No cascading updates or update storms
- O(1) synchronization regardless of network size
- Transitive relationships emerge naturally
- No need for dependency tracking

#### 2. **ACID-Like Guarantees for State Changes**

Every state change in NexPy follows ACID principles:

- **Atomic** — All related updates succeed or fail together
- **Consistent** — Invariants are always maintained
- **Isolated** — Concurrent modifications don't interfere
- **Durable** — State persists until explicitly changed

#### 3. **Separation of Concerns**

NexPy separates three distinct concerns:

1. **Value Storage** (Nexus) — Holds shared state
2. **Connection Management** (Hook) — Provides access points
3. **Orchestration** (NexusManager) — Coordinates validation and updates

This separation enables:
- Clear responsibilities
- Easy testing and debugging
- Flexible extension points

#### 4. **Thread Safety by Default**

All operations are thread-safe without requiring external locks. Users can safely call NexPy APIs from multiple threads.

#### 5. **No Hidden Side Effects**

NexPy never:
- Copies values implicitly
- Modifies user data
- Performs hidden conversions
- Triggers automatic garbage collection of user objects

All operations work with references, preserving object identity.

---

## Architectural Layers

NexPy is organized into four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│                     (User Code)                             │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   X Objects Layer                           │
│   XValue, XDict, XList, XSet, XDictSelect, etc.           │
│   - High-level reactive data structures                    │
│   - Internal synchronization protocol                      │
│   - User-friendly APIs                                     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Hook Layer                               │
│   FloatingHook, OwnedHook                                  │
│   - Connection points for fusion                           │
│   - Value access interface                                 │
│   - Listener management                                    │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Nexus Layer                              │
│   Nexus, NexusManager                                      │
│   - Fusion domain management                               │
│   - Value storage and synchronization                      │
│   - Validation orchestration                               │
│   - Thread-safe locking                                    │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: X Objects (High-Level API)

**Purpose**: Provide user-friendly reactive data structures.

**Components**:
- `XValue` — Single reactive value
- `XDict`, `XList`, `XSet` — Reactive collections
- `XDictSelect`, `XSetSelect` — Selection objects
- `XFunction` — Reactive computed values

**Responsibilities**:
- Expose intuitive Python APIs (properties, methods)
- Implement internal synchronization protocol
- Manage multiple owned hooks
- Provide validation callbacks

### Layer 2: Hook Layer

**Purpose**: Provide connection points for fusion and value access.

**Components**:
- `FloatingHook` — Independent hooks
- `OwnedHook` — Hooks owned by X objects
- Hook protocols and mixins

**Responsibilities**:
- Reference a Nexus
- Provide value access
- Implement join/isolate operations
- Manage listeners
- Support validation and reaction callbacks

### Layer 3: Nexus Layer

**Purpose**: Manage fusion domains and orchestrate synchronization.

**Components**:
- `Nexus` — Fusion domain (holds value, manages hooks)
- `NexusManager` — Central coordinator

**Responsibilities**:
- Store shared values
- Track hooks in fusion domain
- Coordinate value submissions
- Execute validation protocol
- Manage thread-safe locking
- Trigger notifications

---

## Data Flow

### Value Update Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. User Update                                               │
│    hook.value = new_value                                    │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Hook Submission                                           │
│    hook.submit_value(new_value)                              │
│    → Creates {nexus: new_value} mapping                      │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. NexusManager.submit_values()                              │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 1: Value Equality Check                        │ │
│    │   Skip if values unchanged (using is_equal)          │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 2: Value Completion                            │ │
│    │   Call _add_values_to_be_updated() on owners         │ │
│    │   Iteratively complete related values                │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 3: Collect Components                          │ │
│    │   Identify affected owners, hooks, publishers        │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 4: Validation                                  │ │
│    │   Call validate_complete_values_in_isolation()       │ │
│    │   Reject entire update if any validation fails       │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 5: Atomic Update                               │ │
│    │   Update all Nexuses simultaneously                  │ │
│    └──────────────────────────────────────────────────────┘ │
│    ┌──────────────────────────────────────────────────────┐ │
│    │ Phase 6: Notifications                               │ │
│    │   - Invalidate owners                                │ │
│    │   - React hooks                                      │ │
│    │   - Publish to subscribers                           │ │
│    │   - Notify listeners                                 │ │
│    └──────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. User Sees Updated State                                   │
│    print(hook.value)  # New value                            │
└──────────────────────────────────────────────────────────────┘
```

### Join Operation Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. User Initiates Join                                       │
│    hook_A.join(hook_B)                                       │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. Lock Acquisition (Ordered by Hook ID)                     │
│    Acquire locks for both hooks in consistent order          │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. Value Synchronization                                     │
│    Submit hook_A's value to hook_B's Nexus                   │
│    (Uses full validation protocol)                           │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Nexus Fusion                                              │
│    - Create merged Nexus containing all hooks                │
│    - Destroy original Nexuses                                │
│    - Update all hooks to reference merged Nexus              │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 5. Lock Release                                              │
│    Release locks in reverse order                            │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 6. Hooks Now Share Fusion Domain                             │
│    hook_A and hook_B reference the same Nexus                │
└──────────────────────────────────────────────────────────────┘
```

---

## Locking Strategy

### Thread-Safe Lock Hierarchy

NexPy uses a hierarchical locking strategy to ensure thread safety without deadlocks:

```
┌────────────────────────────────────────────────────────┐
│              NexusManager (Global Lock)                │
│  - Reentrant lock (RLock)                             │
│  - Protects entire submission protocol                 │
│  - Serializes concurrent submit_values() calls         │
└────────────────────────────────────────────────────────┘
                         │
                         ├── protects ──→ Nexus updates
                         ├── protects ──→ Validation calls
                         └── protects ──→ Notification dispatch

┌────────────────────────────────────────────────────────┐
│              Hook Locks (Per-Hook Locks)               │
│  - Used during join/isolate operations                 │
│  - Ordered by hook ID to prevent deadlocks             │
│  - Released after Nexus fusion completes               │
└────────────────────────────────────────────────────────┘
```

### Lock Ordering for Join Operations

To prevent deadlocks when joining hooks, NexPy uses **deterministic lock ordering**:

```python
# Simplified join implementation
def join(self, other):
    # Order locks by hook ID to prevent deadlock
    hook1, hook2 = sorted([self, other], key=id)
    
    with hook1._lock:
        with hook2._lock:
            # Perform fusion safely
            Nexus.join_hook_pairs((self, other))
```

This ensures that no matter which order threads call `A.join(B)` or `B.join(A)`, locks are always acquired in the same order.

### Reentrancy Protection

NexPy prevents recursive modification of the same Nexus using **thread-local state tracking**:

```python
# Simplified reentrancy protection
def submit_values(self, nexus_and_values):
    new_nexuses = set(nexus_and_values.keys())
    active_nexuses = self._thread_local.active_nexuses
    
    # Check for overlapping modifications
    if active_nexuses & new_nexuses:
        raise RuntimeError("Recursive modification detected!")
    
    # Track active nexuses for this thread
    self._thread_local.active_nexuses.update(new_nexuses)
    
    try:
        # Perform update
        return self._internal_submit_values(nexus_and_values)
    finally:
        # Always clean up
        self._thread_local.active_nexuses -= new_nexuses
```

**Key Properties**:
- Thread-local tracking (each thread has independent state)
- Prevents overlapping modifications in the same thread
- Allows independent submissions in nested calls
- Always cleans up (even on exceptions)

---

## Nexus Fusion Mechanics

### Fusion Process

When two hooks are joined, their Nexuses undergo **fusion**:

```
Before Join:
┌──────────────┐        ┌──────────────┐
│  Nexus_A     │        │  Nexus_B     │
│  value: 10   │        │  value: 20   │
│  hooks: {A}  │        │  hooks: {B}  │
└──────────────┘        └──────────────┘
       ↑                        ↑
       │                        │
    Hook_A                   Hook_B

After A.join(B):
           ┌──────────────────────┐
           │  Nexus_AB            │
           │  value: 10           │
           │  hooks: {A, B}       │
           └──────────────────────┘
                  ↑        ↑
                  │        │
               Hook_A   Hook_B

(Nexus_A and Nexus_B are destroyed)
```

### Transitive Fusion

Fusion is transitive, creating equivalence networks:

```
Step 1: A.join(B)
   Nexus_AB: {A, B}

Step 2: C.join(D)
   Nexus_AB: {A, B}
   Nexus_CD: {C, D}

Step 3: B.join(C)
   Nexus_ABCD: {A, B, C, D}

(Nexus_AB and Nexus_CD are destroyed, replaced by Nexus_ABCD)
```

### Why Fusion Instead of References?

NexPy uses **fusion** (creating new Nexuses) rather than just updating references because:

1. **Cleaner Lifecycle** — Old Nexuses are garbage collected automatically
2. **No Dangling References** — All hooks always reference valid Nexuses
3. **Simplified Tracking** — No need to track "primary" or "secondary" Nexuses
4. **Transitive Closure** — Natural representation of equivalence classes

---

## Validation Cycle

### Two-Phase Validation

NexPy uses **two-phase validation** to ensure consistency:

#### Phase 1: Completion Phase

```
User submits partial update
         ↓
Call _add_values_to_be_updated() on owners
         ↓
Owner returns additional required values
         ↓
Repeat until fixed point (no new values)
         ↓
Complete set of values ready for validation
```

**Purpose**: Ensure all related values are included in the update.

#### Phase 2: Validation Phase

```
Complete set of values ready
         ↓
Call _validate_complete_values_in_isolation() on each owner
         ↓
Call validate_value_in_isolation() on floating hooks
         ↓
If ALL validations pass → proceed to update
If ANY validation fails → reject entire update
```

**Purpose**: Ensure all invariants are satisfied.

### Validation Guarantees

1. **Completeness** — All related values are validated together
2. **Isolation** — Each owner validates independently
3. **Atomicity** — Either all updates succeed or none do
4. **Consistency** — Invariants are always maintained

---

## Notification Philosophies

NexPy supports three distinct notification mechanisms, each with different characteristics:

### 1. Listeners (Synchronous Unidirectional)

**Characteristics**:
- Executed synchronously during `submit_values()` (Phase 6)
- Unidirectional: observers can't reject changes
- Thread-safe: protected by NexusManager lock

**Use Cases**:
- UI updates
- Logging
- Simple reactions to state changes

```python
hook.add_listener(lambda: print(f"Value: {hook.value}"))
```

### 2. Publish-Subscribe (Asynchronous Unidirectional)

**Characteristics**:
- Executed asynchronously via asyncio tasks
- Unidirectional: subscribers can't affect submission
- Non-blocking: publishing returns immediately
- Thread-safe: independent async execution

**Use Cases**:
- Decoupled components
- Async I/O operations
- External system notifications

```python
publisher = nx.Publisher()
subscriber = nx.Subscriber(callback=async_handler)
publisher.subscribe(subscriber)
```

### 3. Hooks (Synchronous Bidirectional with Validation)

**Characteristics**:
- Validation occurs before value changes (Phase 4)
- Bidirectional: hooks can reject changes via validation
- Thread-safe: protected by NexusManager lock
- Enforces valid state across fusion domain

**Use Cases**:
- Maintaining invariants across objects
- Bidirectional data binding
- Cross-object constraints

```python
hook_A.join(hook_B)  # Both hooks can now validate each other's changes
```

### Notification Order

Listeners are notified in this order:

1. **Owner invalidation** — `_invalidate()` called on affected owners
2. **Hook reactions** — `react_to_value_changed()` called on hooks
3. **Publishing** — `publish()` called on publishers (async)
4. **Owner listeners** — Listeners on owners notified
5. **Hook listeners** — Listeners on affected hooks notified

---

## Memory Management

### Weak References for Hooks

Nexuses store hooks as **weak references**:

```python
self._hooks: set[weakref.ref[Hook]] = {weakref.ref(hook) for hook in hooks}
```

**Advantages**:
- Automatic cleanup when hooks are garbage collected
- No circular reference issues
- Nexuses don't prevent hook cleanup

### Automatic Dead Reference Cleanup

Nexuses periodically clean up dead weak references:

```python
def _get_hooks(self):
    alive_hooks = set()
    dead_refs = set()
    
    for hook_ref in self._hooks:
        hook = hook_ref()
        if hook is not None:
            alive_hooks.add(hook)
        else:
            dead_refs.add(hook_ref)
    
    self._hooks -= dead_refs  # Remove dead references
    return alive_hooks
```

### No Value Copying

NexPy **never copies values**:

```python
# Values are stored and passed by reference only
nexus._stored_value = value  # Reference assignment, no copy
```

**Advantages**:
- O(1) updates regardless of value size
- Preserves object identity
- No hidden memory allocation
- Works with any Python object

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Hook creation | O(1) | Creates hook + nexus |
| Value read | O(1) | Direct reference access |
| Value update | O(n) | n = number of affected hooks |
| Join operation | O(k) | k = total hooks in both fusion domains |
| Isolate operation | O(1) | Creates new independent nexus |
| Validation | O(m) | m = number of owners to validate |

### Space Complexity

| Component | Space | Notes |
|-----------|-------|-------|
| Hook | O(1) | Reference to nexus + listeners |
| Nexus | O(h) | h = number of hooks (weak refs) |
| Fusion domain | O(h) | One nexus for all hooks |
| NexusManager | O(1) | Global state, independent of hook count |

### Scalability

NexPy scales well with:
- **Large values** — No copying overhead
- **Many hooks** — O(1) per-hook value access
- **Complex fusion networks** — O(1) synchronization within domain
- **Concurrent access** — Lock contention is minimal

NexPy may have overhead with:
- **Frequent join/isolate** — Creates/destroys Nexuses
- **Complex validation** — Must validate all affected owners
- **Deep completion chains** — Iterative value completion

---

## Design Decisions

### Why Nexus Fusion Instead of Change Propagation?

**Traditional Approach** (Dependency Graph):
```
A → B → C → D
```
- Requires topological sort
- Can create update storms
- Complex cycle detection
- O(edges) propagation cost

**NexPy Approach** (Fusion Domain):
```
Nexus_ABCD: {A, B, C, D}
```
- No propagation needed
- O(1) synchronization
- Transitive by design
- No cycles possible

### Why Two-Phase Validation?

**Completion Phase** ensures all related values are included.
**Validation Phase** ensures all invariants are satisfied.

Separating these phases allows:
- Clear separation of concerns
- Independent implementation by users
- Iterative completion without validation overhead
- All-or-nothing atomic updates

### Why Thread-Local Reentrancy Protection?

Using thread-local state (instead of global state) allows:
- Independent submissions from different threads
- Detection of recursive modifications in the same thread
- No cross-thread interference
- Fine-grained overlap detection

### Why Weak References for Hooks?

Using weak references prevents:
- Circular reference memory leaks
- Nexuses keeping hooks alive indefinitely
- Need for explicit cleanup

Advantages:
- Automatic cleanup when hooks are no longer used
- Natural garbage collection integration

---

## Next Steps

- **[API Reference](api_reference.md)** — Complete API documentation
- **[Examples](examples.md)** — Practical usage examples
- **[Concepts](concepts.md)** — Deep dive into fusion domains
- **[Usage Guide](usage.md)** — Learn join/isolate mechanics

---

**[Back to README](../README.md)**

