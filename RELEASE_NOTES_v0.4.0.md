# Release Notes - nexpylib v0.4.0

**Release Date**: January 29, 2025  
**Version**: 0.4.0  
**Python Support**: 3.13+  

## 🚀 Release Highlights

This release focuses on comprehensive API documentation updates, clarifying the hook system architecture, and ensuring documentation accuracy with the current implementation. The internal hook type architecture has been fully overhauled with specialized hook types for better type safety and API clarity.

## 🔧 Major Architecture Change

### Hook System Architecture Overhaul

The internal hook type system has been completely redesigned for better clarity and type safety:

- **Replaced generic `OwnedHook`**: Split into two specialized types based on functionality
- **`OwnedReadOnlyHook`**: For computed/derived values that should not be modified externally
- **`OwnedWritableHook`**: For primary values that can be directly modified
- **Improved type safety**: Clear distinction between read-only and writable hooks
- **Better API design**: Each hook type has a specific purpose and use case

This architectural change improves:
- **Type Safety**: Compiler can catch misuse of read-only hooks
- **API Clarity**: Developers know exactly what each hook type can do
- **Documentation**: Easier to understand and document each hook type's purpose
- **Maintainability**: Clear separation of concerns in the codebase

## 📚 Documentation Updates

### Complete API Refactoring Documentation

#### Hook System Clarification
The documentation has been significantly updated to reflect the new architecture:

- **`OwnedReadOnlyHook`**: Documented as a read-only hook owned by X objects, used for computed/derived values
- **`OwnedWritableHook`**: Documented as a writable hook owned by X objects, used for primary values
- **Replaced generic `OwnedHook` reference**: Updated to use the specific hook types

#### Updated Documentation Files
- **`docs/api_reference.md`**: Complete rewrite of hook documentation with accurate API details
  - Added full documentation for `OwnedReadOnlyHook` and `OwnedWritableHook`
  - Documented all methods including `set_reaction_callback()`, `get_reaction_callback()`, etc.
  - Clarified differences between hook types
  
- **`docs/usage.md`**: Updated hook usage examples
  - Replaced generic "OwnedHook" references
  - Added examples for both read-only and writable owned hooks
  - Clarified use cases for each hook type
  
- **`docs/architecture.md`**: Updated architectural diagrams
  - Corrected layer descriptions to reflect actual hook types
  - Updated component lists to show specific hook implementations
  
- **`src/nexpy/core/__init__.py`**: Updated module docstring
  - Changed "Observables Core" to "NexPy Core"
  - Added examples for hook system usage
  - Documented all exported components
  
- **`src/nexpy/foundations/serializable_protocol.py`**: Updated terminology
  - Replaced "Observable" with "NexPy object"
  - Updated class references to modern NexPy conventions
  - Changed "bindings" to "fusion domains"

### Terminology Improvements

#### NexPy Branding
- Replaced all references to "Observables" with "NexPy"
- Updated "observable objects" to "NexPy objects" or "X objects"
- Changed "bindings" to "fusion domains" to match internal architecture
- Updated class name references to modern conventions (XValue, XBase, etc.)

## 🔧 API Clarifications

### Hook Type Documentation

#### FloatingHook
Independent writable hook with validation and reaction capabilities.

```python
import nexpy as nx

hook = nx.FloatingHook(value=42)
hook.value = 100  # Writable
```

#### OwnedReadOnlyHook
Read-only hook owned by X objects, used for computed/derived values.

```python
# Used internally by X objects for read-only computed values
# Access via: obj.hook_name (read-only)
```

#### OwnedWritableHook
Writable hook owned by X objects, used for primary values.

```python
import nexpy as nx

value = nx.XValue(42)
hook = value.value_hook  # OwnedWritableHook
hook.value = 100  # Writable
```

### Key Differences

| Hook Type | Writable | Owned | Use Case |
|-----------|----------|-------|----------|
| `FloatingHook` | ✅ | ❌ | Independent reactive values |
| `OwnedReadOnlyHook` | ❌ | ✅ | Computed/derived values |
| `OwnedWritableHook` | ✅ | ✅ | Primary values in X objects |

## 🎯 What Changed

### For Users

No breaking changes. This release provides:
- **Architectural improvements**: Specialized hook types for better clarity
- **Accurate API documentation** matching the actual implementation
- **Clear hook type distinctions** for better understanding
- **Consistent terminology** throughout all documentation
- **Better examples** showing proper hook usage

### For Developers

- **Major architectural change**: Complete overhaul of internal hook type system
- **Specialized hook types**: Split `OwnedHook` into `OwnedReadOnlyHook` and `OwnedWritableHook`
- **Improved type safety**: Clear distinction between read-only and writable hooks
- Updated docstrings to match current API
- Replaced outdated terminology with current conventions
- Clarified hook type purposes and use cases
- Improved code documentation consistency

## 📦 Installation

```bash
pip install nexpylib==0.4.0
```

## 🚀 Upgrading from v0.3.0

No code changes required. This release only updates documentation and does not introduce any breaking changes.

## 🔍 Looking Ahead

Future releases will focus on:
- Enhanced performance optimizations
- Additional adapter types
- Improved GUI integration
- Extended examples and tutorials

## 📄 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

---

**Full Changelog**: https://github.com/BABrandes/nexpylib/compare/v0.3.0...v0.4.0

