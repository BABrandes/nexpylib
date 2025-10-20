# Concepts

This document provides a deep conceptual exploration of NexPy's core ideas: fusion domains, equivalence networks, transitive synchronization, and the mathematical foundations of the system.

---

## Table of Contents

- [Fusion Domains](#fusion-domains)
- [Equivalence Networks](#equivalence-networks)
- [Transitive Synchronization](#transitive-synchronization)
- [The Join-Isolate Algebra](#the-join-isolate-algebra)
- [Internal vs External Synchronization](#internal-vs-external-synchronization)
- [Comparison with Other Patterns](#comparison-with-other-patterns)
- [Mathematical Properties](#mathematical-properties)
- [Conceptual ASCII Diagrams](#conceptual-ascii-diagrams)

---

## Fusion Domains

### What is a Fusion Domain?

A **fusion domain** is a set of hooks that share a single Nexus—a centralized synchronization core. All hooks in a fusion domain:

1. **Reference the same Nexus**
2. **Share the same value**
3. **Update simultaneously**
4. **Are transitively connected**

```
Fusion Domain = Nexus + Set of Hooks

Example:
  Nexus_ABCD
      ↑
  ┌───┼───┬───┬───┐
  │   │   │   │   │
Hook_A B   C   D   E ... (all reference Nexus_ABCD)
```

### Fusion Domain Properties

#### 1. Single Source of Truth

Unlike distributed consensus where multiple nodes maintain copies of state, a fusion domain has **exactly one source of truth**: the Nexus.

```
Traditional Distributed System:
┌─────┐  ┌─────┐  ┌─────┐
│ A:v │  │ B:v │  │ C:v │  (Copies must be synchronized)
└─────┘  └─────┘  └─────┘

NexPy Fusion Domain:
       ┌─────────┐
       │ Nexus:v │  (Single source of truth)
       └─────────┘
        ↗   ↑   ↖
     Hook_A  B   C  (All reference the same Nexus)
```

#### 2. Zero Propagation Delay

Since all hooks reference the same Nexus, updates have **zero propagation delay** within the fusion domain.

```
Update Flow:
User → Hook.value = x → Nexus._stored_value = x → All hooks see x

Time: O(1) regardless of domain size
```

#### 3. Transitive Closure

Fusion domains naturally represent **transitive closure** of the join relation. If `A` joins `B` and `B` joins `C`, then `A`, `B`, and `C` all share the same Nexus (transitive fusion).

---

## Equivalence Networks

### Hooks as Equivalence Classes

In mathematics, an **equivalence relation** is a relation that is:
1. **Reflexive**: `A ~ A`
2. **Symmetric**: If `A ~ B`, then `B ~ A`
3. **Transitive**: If `A ~ B` and `B ~ C`, then `A ~ C`

NexPy's join operation creates an equivalence relation on hooks:

- **Reflexive**: Every hook is in its own fusion domain (initially)
- **Symmetric**: `A.join(B)` is equivalent to `B.join(A)`
- **Transitive**: Joining creates transitive closure

### Equivalence Classes are Fusion Domains

Each fusion domain represents an **equivalence class** of hooks. All hooks in the same equivalence class (fusion domain) are synchronized.

```
Initial State (each hook is its own class):
[A], [B], [C], [D]

After A.join(B):
[A, B], [C], [D]

After C.join(D):
[A, B], [C, D]

After B.join(C):
[A, B, C, D]  (Equivalence classes merged)
```

### Partition of Hooks

At any moment, the set of all hooks can be **partitioned** into disjoint fusion domains:

```
All Hooks = Domain₁ ∪ Domain₂ ∪ ... ∪ Domainₙ

Where:
- Each Domain_i is a fusion domain (equivalence class)
- Domains are disjoint: Domain_i ∩ Domain_j = ∅ (for i ≠ j)
- Every hook belongs to exactly one domain
```

---

## Transitive Synchronization

### What is Transitive Synchronization?

**Transitive synchronization** means that if `A` is synchronized with `B`, and `B` is synchronized with `C`, then `A` is automatically synchronized with `C`—without explicitly connecting `A` and `C`.

```
Explicit Connections:
A ↔ B
B ↔ C

Implied Connection:
A ↔ C  (Transitive)
```

### How NexPy Achieves Transitivity

NexPy achieves transitivity through **Nexus fusion**:

```
Step 1: A.join(B)
  - Destroy Nexus_A and Nexus_B
  - Create Nexus_AB
  - A and B both reference Nexus_AB

Step 2: B.join(C)
  - Destroy Nexus_AB and Nexus_C
  - Create Nexus_ABC
  - A, B, and C all reference Nexus_ABC

Result: A, B, C are transitively synchronized
```

### Comparison: Transitive vs Non-Transitive

#### Non-Transitive Synchronization

In traditional observer patterns, connections are **direct** but **not transitive**:

```
A observes B
B observes C

But A does NOT automatically observe C
```

If `C` changes, `B` gets notified, but `A` does not (unless `B` explicitly propagates).

#### Transitive Synchronization (NexPy)

In NexPy, connections are **transitive**:

```
A.join(B)
B.join(C)

Result: A, B, C all share Nexus_ABC
```

If any hook updates, all hooks see the change immediately.

---

## The Join-Isolate Algebra

### Join Operation

**Definition**: `A.join(B)` creates a fusion domain containing both `A` and `B`.

**Properties**:
- **Symmetric**: `A.join(B)` ≡ `B.join(A)`
- **Idempotent**: `A.join(B); A.join(B)` ≡ `A.join(B)` (second join is a no-op)
- **Associative** (in effect): `(A.join(B)).join(C)` creates the same fusion domain as `A.join(B.join(C))`

**Formal Semantics**:
```
Before: A ∈ Domain_X, B ∈ Domain_Y
After:  A ∈ Domain_Z, B ∈ Domain_Z
Where:  Domain_Z = Domain_X ∪ Domain_Y
```

### Isolate Operation

**Definition**: `A.isolate()` removes `A` from its fusion domain and creates a new independent domain.

**Properties**:
- **Creates independence**: After `A.isolate()`, `A` is in its own domain
- **Preserves value**: `A` retains its current value after isolation
- **Doesn't affect others**: Other hooks in the original domain remain joined

**Formal Semantics**:
```
Before: A ∈ Domain_X = {A, B, C, ...}
After:  A ∈ Domain_A = {A}
        B, C, ... ∈ Domain_BC... = {B, C, ...}
```

### Algebraic Laws

#### Law 1: Join is Commutative
```
A.join(B) ≡ B.join(A)
```

#### Law 2: Join is Transitive
```
If A.join(B) and B.join(C), then A, B, C share the same domain
```

#### Law 3: Isolate Breaks All Connections
```
A.join(B)
A.isolate()
→ A is no longer joined to B
```

#### Law 4: Isolate is Idempotent
```
A.isolate()
A.isolate()
≡ A.isolate()  (Second isolate has no effect)
```

#### Law 5: Re-joining After Isolate
```
A.join(B)       // A and B joined
A.isolate()     // A isolated
A.join(B)       // A and B joined again
```

---

## Internal vs External Synchronization

NexPy provides two complementary forms of synchronization:

### External Synchronization (Nexus Fusion)

**Scope**: Across independent objects
**Mechanism**: Join/isolate operations
**Purpose**: Create dynamic equivalence networks

```
Object A     Object B
   ↓            ↓
Hook A  ←join→ Hook B
   ↓            ↓
Same Nexus (synchronized)
```

**Characteristics**:
- **User-controlled**: Join/isolate are explicit operations
- **Dynamic**: Connections can be created/broken at runtime
- **Non-directional**: No "master" or "slave"
- **Transitive**: Creates equivalence classes

### Internal Synchronization (Multi-Hook Coordination)

**Scope**: Within a single object
**Mechanism**: Validation + completion protocol
**Purpose**: Maintain object invariants

```
XDictSelect Object
   ┌─────────┬─────────┬─────────┐
   │         │         │         │
dict_hook key_hook value_hook keys_hook ...
   │         │         │         │
   └─────────┴─────────┴─────────┘
          All synchronized atomically
```

**Characteristics**:
- **Automatic**: System-controlled, not user-controlled
- **Static**: Relationships defined by object structure
- **Directional**: Object enforces consistency rules
- **Atomic**: All updates succeed or fail together

### Interaction Between Internal and External

External and internal synchronization can interact:

```python
import nexpy as nx

# Two selection objects (each has internal sync)
select1 = nx.XDictSelect({"a": 1, "b": 2}, key="a")
select2 = nx.XDictSelect({"x": 10, "y": 20}, key="x")

# External sync: join their dict hooks
select1.dict_hook.join(select2.dict_hook)

# Now updates must satisfy BOTH objects' internal invariants
select1.value = 5
# Internal sync: dict automatically updated
# External sync: select2.dict also updated
```

---

## Comparison with Other Patterns

### vs Observer Pattern

**Observer Pattern**:
```
Subject
  ↓ notifies
Observer 1, Observer 2, Observer 3, ...
```

- **Directional**: Subject → Observers (one-way)
- **Non-transitive**: Observers don't affect each other
- **Propagation**: Changes propagate through callbacks
- **Asymmetric**: Subject and Observers have different roles

**NexPy**:
```
       Nexus
      /  |  \
Hook A   B   C
```

- **Non-directional**: All hooks are equal
- **Transitive**: Joining creates equivalence classes
- **Shared State**: All hooks reference the same value
- **Symmetric**: No distinguished "subject"

### vs Reactive Streams (RxJS, RxJava)

**Reactive Streams**:
```
Source → Operator → Operator → Observer
```

- **Pipeline**: Data flows through transformation pipeline
- **Time-based**: Handles sequences of values over time
- **Async**: Often asynchronous processing
- **Push-based**: Values pushed through the stream

**NexPy**:
```
Fusion Domain: Shared state among hooks
```

- **State-based**: Focuses on shared state, not sequences
- **Synchronous**: Updates are synchronous (by default)
- **Equivalence**: Creates equivalence networks
- **Pull/Push**: Supports both reading and updating

### vs Publish-Subscribe

**Pub/Sub**:
```
Publisher → Topic → Subscriber 1, Subscriber 2, ...
```

- **Decoupled**: Publishers don't know subscribers
- **Topic-based**: Messages routed by topic
- **Asynchronous**: Usually async messaging
- **One-way**: Publishers send, subscribers receive

**NexPy**:
```
Fusion Domain: Bidirectional synchronization
```

- **Coupled**: Hooks in fusion domain are tightly synchronized
- **State-based**: Shared state, not messages
- **Synchronous**: Updates are immediate within domain
- **Bidirectional**: Any hook can update, all see changes

### vs Data Binding (WPF, Angular)

**Data Binding**:
```
Model ↔ ViewModel ↔ View
```

- **Layered**: Specific layers (Model, View, ViewModel)
- **Framework-specific**: Tied to UI frameworks
- **Template-based**: Often declarative bindings
- **Hierarchical**: Parent-child relationships

**NexPy**:
```
Fusion Domain: Flat network of synchronized hooks
```

- **Flat**: No inherent hierarchy
- **Framework-agnostic**: Works with any Python code
- **Programmatic**: Joins are explicit operations
- **Network-based**: Arbitrary connection topology

---

## Mathematical Properties

### Fusion as a Union-Find Structure

NexPy's fusion domains can be understood as a **Union-Find (Disjoint Set)** data structure:

- **Universe**: All hooks
- **Sets**: Fusion domains (disjoint sets of hooks)
- **Union**: Join operation (merges two sets)
- **Find**: Get the Nexus for a hook (find representative)

**Operations**:
- `find(hook)` → Returns the Nexus (set representative)
- `union(hookA, hookB)` → Joins their fusion domains (merges sets)

**Properties**:
- **Disjoint**: Every hook belongs to exactly one fusion domain
- **Partition**: Fusion domains partition the set of all hooks
- **Dynamic**: Union operations create larger fusion domains

### Graph Representation

Fusion domains can be represented as a graph:

```
Nodes: Hooks
Edges: Hooks in the same fusion domain are fully connected

Example:
Before join:
A   B   C

After A.join(B):
A—B   C

After B.join(C):
A—B
 \ |
  \C
(Complete graph: A-B, B-C, A-C all connected)
```

### Equivalence Relation Properties

The "same fusion domain" relation is an equivalence relation:

**1. Reflexive**: `A ~ A`
   - Every hook is in the same domain as itself

**2. Symmetric**: `A ~ B ⟹ B ~ A`
   - If A is in B's domain, then B is in A's domain

**3. Transitive**: `A ~ B ∧ B ~ C ⟹ A ~ C`
   - If A and B share a domain, and B and C share a domain,
     then A and C share a domain

### Time Complexity Analysis

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Create hook | O(1) | O(1) |
| Read value | O(1) | — |
| Update value | O(h + v) | O(h) |
| Join | O(h₁ + h₂) | O(h₁ + h₂) |
| Isolate | O(1) | O(1) |

Where:
- `h` = number of hooks in fusion domain
- `v` = number of validations to perform
- `h₁, h₂` = hooks in respective fusion domains

---

## Conceptual ASCII Diagrams

### Diagram 1: Nexus Fusion Process

```
Initial State:
┌─────────────┐     ┌─────────────┐
│  Nexus_A    │     │  Nexus_B    │
│  value: 10  │     │  value: 20  │
│  hooks: {A} │     │  hooks: {B} │
└─────────────┘     └─────────────┘
       ↑                   ↑
       │                   │
    Hook_A              Hook_B


After A.join(B):
       ┌──────────────────────┐
       │    Nexus_AB          │
       │    value: 10         │
       │    hooks: {A, B}     │
       └──────────────────────┘
              ↑        ↑
              │        │
           Hook_A   Hook_B

(Nexus_A and Nexus_B destroyed)
```

### Diagram 2: Transitive Fusion

```
Step 1: A.join(B)
─────────────────────
┌─────────────────┐        ┌─────────┐
│   Nexus_AB      │        │ Nexus_C │
│   {A, B}        │        │  {C}    │
└─────────────────┘        └─────────┘


Step 2: C.join(D)
─────────────────────
┌─────────────────┐        ┌─────────────┐
│   Nexus_AB      │        │ Nexus_CD    │
│   {A, B}        │        │  {C, D}     │
└─────────────────┘        └─────────────┘


Step 3: B.join(C)
─────────────────────
        ┌──────────────────────┐
        │   Nexus_ABCD         │
        │   {A, B, C, D}       │
        └──────────────────────┘
         ↗    ↗    ↖    ↖
       A     B     C     D

(All four hooks transitively synchronized)
```

### Diagram 3: Internal vs External Synchronization

```
┌────────────────────────────────────────────────────────┐
│           XDictSelect Object                           │
│                                                        │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐           │
│  │dict_hook │  │key_hook │  │value_hook │           │
│  └────┬─────┘  └────┬────┘  └─────┬─────┘           │
│       │             │              │                  │
│       └──────── Internal Sync ─────┘                 │
│                (Atomic updates)                       │
└────────────────────────────────────────────────────────┘
        │
        │ External Sync (join)
        │
        ↓
┌────────────────────────────────────────────────────────┐
│           Another XDictSelect Object                   │
│                                                        │
│  ┌──────────┐  ┌─────────┐  ┌───────────┐           │
│  │dict_hook │  │key_hook │  │value_hook │           │
│  └────┬─────┘  └────┬────┘  └─────┬─────┘           │
│       │             │              │                  │
│       └──────── Internal Sync ─────┘                 │
└────────────────────────────────────────────────────────┘
```

### Diagram 4: Validation Protocol

```
User Update Request
        ↓
┌───────────────────────────┐
│  Value Equality Check     │
│  (Skip if unchanged)      │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Value Completion         │
│  ┌─────────────────────┐ │
│  │ Call owner          │ │
│  │ _add_values_to_be_  │ │
│  │ updated()           │ │
│  │                     │ │
│  │ Iterate until       │ │
│  │ fixed point         │ │
│  └─────────────────────┘ │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Validation               │
│  ┌─────────────────────┐ │
│  │ For each owner:     │ │
│  │ validate_complete_  │ │
│  │ values_in_isolation │ │
│  │                     │ │
│  │ All must pass       │ │
│  └─────────────────────┘ │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Atomic Update            │
│  All Nexuses updated      │
│  simultaneously           │
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  Notifications            │
│  - Invalidate             │
│  - React                  │
│  - Publish                │
│  - Notify listeners       │
└───────────────────────────┘
```

---

## Summary

NexPy's conceptual foundation rests on:

1. **Fusion Domains** — Sets of hooks sharing a Nexus
2. **Equivalence Networks** — Hooks as equivalence classes
3. **Transitive Synchronization** — Automatic propagation through fusion
4. **Join-Isolate Algebra** — Operations that build/break connections
5. **Internal/External Duality** — Object invariants + cross-object sync
6. **Mathematical Properties** — Equivalence relations, union-find, graph representation

These concepts provide a solid theoretical foundation for understanding and using NexPy effectively.

---

## Next Steps

- **[Usage Guide](usage.md)** — Learn practical join/isolate operations
- **[Architecture](architecture.md)** — Understand implementation details
- **[API Reference](api_reference.md)** — Complete API documentation
- **[Examples](examples.md)** — See concepts in action

---

**[Back to README](../README.md)**

