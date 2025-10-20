# Release Notes: NexPyLib v0.1.0

## 🎉 First Public Release

This is the first public release of NexPyLib, ready for PyPI deployment!

---

## ✨ Key Features

### **Transitive Synchronization Through Nexus Fusion**
- Join any hooks to create fusion domains with automatic transitive synchronization
- Non-directional, symmetric synchronization (no master/slave relationships)
- Dynamic fusion and isolation of hooks at runtime

### **Atomic Internal Synchronization**
- ACID-like guarantees for multi-hook objects
- Transaction-style validation and updates
- Coherent state maintained across related hooks (e.g., dict/keys/values/key/value in XDictSelect)

### **Rich Reactive Data Structures**
- `XValue` — Single reactive values
- `XList` — Reactive lists with full Python list protocol
- `XSet` — Reactive sets with full Python set protocol  
- `XDict` — Reactive dictionaries with full Python dict protocol
- `XDictSelect` — Selection from a dictionary (key ↔ value synchronization)
- `XSetSingleSelect` — Single selection from a set
- `XSetSingleSelectOptional` — Optional single selection (can be None)
- `XSetMultiSelect` — Multiple selections from a set

### **Thread-Safe by Design**
- All operations protected by reentrant locks
- Safe concurrent access from multiple threads
- Reentrancy protection prevents recursive modifications

### **Custom Equality Checks**
- Configure custom equality callbacks at the NexusManager level
- Standard support for floating-point tolerance (1e-9)
- Per-manager configurations for different use cases

---

## 🔧 API Improvements (This Release)

### 1. **Default `initial_sync_mode` for `join()`**
**Before:**
```python
hook1.join(hook2, initial_sync_mode="use_target_value")  # Required
```

**After:**
```python
hook1.join(hook2)  # Defaults to "use_target_value"
```

**Rationale:** When joining to a potentially large nexus, adopting the target's value is the sensible default.

---

### 2. **Consistent Collection Property Names**
**New API:**
```python
XValue  → .value       + .value_hook
XList   → .list        + .list_hook
XSet    → .set         + .set_hook
XDict   → .dict        + .dict_hook
```

**Rationale:** Semantic, consistent naming across all collection types.

---

### 3. **Improved Selection Set Naming**
**Before:**
```python
XSetSelect              # Ambiguous
XSetOptionalSelect      # Inconsistent
XSetMultiSelect         # OK
```

**After:**
```python
XSetSingleSelect          # Clear: single selection required
XSetSingleSelectOptional  # Clear: single selection optional
XSetMultiSelect           # Clear: multiple selections
```

---

### 4. **Consistent Exception Handling**
**Pattern:**
- Property setters (`.value = x`) call `.change_value(x)`
- `.change_value()` always raises `SubmissionError` on failure
- All setter/change methods now consistent across the library

**Example:**
```python
# Both raise SubmissionError on failure
temperature.value = -300  # Via setter
temperature.change_value(-300)  # Direct method call
```

---

## 📦 PyPI Metadata

**Package:** `nexpylib`  
**Version:** `0.1.0`  
**Description:** Transitive synchronization and shared-state fusion for Python through Nexus fusion and atomic internal synchronization  
**Keywords:** reactive, binding, data-binding, synchronization, nexus, fusion, observable, gui, reactive-programming  
**Python:** >=3.13  
**License:** Apache-2.0

---

## 🧪 Test Coverage

- ✅ **611 tests passing**
- ✅ 3 tests skipped (intentional)
- ✅ 0 failures
- ✅ Comprehensive test coverage across:
  - Hook fusion and isolation
  - Thread safety
  - Memory management  
  - Custom equality checks
  - Internal synchronization
  - Reactive collections
  - Selection objects
  - Performance benchmarks

---

## 📚 Documentation

Complete documentation suite included:
- `README.md` — High-level overview and quickstart
- `docs/usage.md` — Join/isolate mechanics, Hook basics
- `docs/internal_sync.md` — Internal synchronization details
- `docs/architecture.md` — Design philosophy and data flow
- `docs/api_reference.md` — Full API documentation
- `docs/examples.md` — Practical runnable examples
- `docs/concepts.md` — Deep conceptual background

---

## 🎯 Primary Use Case

**Complex GUI Applications** — The library is designed for building reactive GUI applications with complex state synchronization requirements, where multiple components need to stay synchronized without tightly coupled dependencies.

---

## 🚀 Installation

```bash
pip install nexpylib
```

---

## 📖 Quick Start

```python
import nexpy as nx

# Simple reactive value
temperature = nx.XValue(20.0)
temperature.value = 25.5

# Hook fusion across objects
sensor = nx.XValue(20.0)
display = nx.XValue(0.0)
sensor.value_hook.join(display.value_hook)  # Now synchronized
sensor.value = 25.5
print(display.value)  # 25.5

# Reactive collections
numbers = nx.XList([1, 2, 3])
numbers.append(4)
print(numbers.list)  # [1, 2, 3, 4]

# Selection with internal sync
options = nx.XDictSelect({"low": 1, "high": 10}, key="low")
print(options.value)  # 1
options.key = "high"
print(options.value)  # 10 (automatically synchronized)
```

---

## 🙏 Credits

**Author:** Benedikt Axel Brandes  
**Year:** 2025  
**License:** Apache License 2.0

---

## ⚠️ Development Status

**Alpha** — This library is functional and well-tested, but the API may still evolve based on user feedback. Breaking changes are possible in minor version updates.

---

## 🐛 Bug Reports & Feedback

Please report issues at: https://github.com/babrandes/nexpylib/issues

---

**Happy Coding! 🎉**

