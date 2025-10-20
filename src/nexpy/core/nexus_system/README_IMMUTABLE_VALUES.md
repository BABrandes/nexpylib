# Immutable Values Module

This module provides utilities for making values immutable before storage in the nexus system, ensuring data integrity and preventing accidental modification of shared state.

## Quick Start

```python
from observables._nexus_system.immutable_values import make_immutable

# Convert mutable collections to immutable equivalents
data = {"users": ["Alice", "Bob"], "count": 2}
immutable_data = make_immutable(data)
# Result: immutables.Map with tuple values
```

## Features

- ✅ **Automatic conversion** of mutable types (dict, list, set) to immutable equivalents
- ✅ **Recursive processing** of nested structures
- ✅ **Frozen dataclass support** - recognizes and preserves frozen dataclasses
- ✅ **Type checking** with `is_immutable_type()` and `validate_immutable()`
- ✅ **Clear error messages** via `ImmutabilityError` for unsupported types
- ✅ **Uses immutables library** for high-performance immutable collections

## Conversions

| Input Type | Output Type | Example |
|------------|-------------|---------|
| `dict` | `immutables.Map` | `{"a": 1}` → `Map({'a': 1})` |
| `list` | `tuple` | `[1, 2, 3]` → `(1, 2, 3)` |
| `set` | `frozenset` | `{1, 2, 3}` → `frozenset({1, 2, 3})` |
| primitives | unchanged | `42` → `42` |
| frozen dataclass | unchanged | `Point(1, 2)` → `Point(1, 2)` |

## API

### `make_immutable(value: T) -> T`

Convert a value to immutable form. Recursively processes nested structures.

**Raises:** `ImmutabilityError` for unsupported types

### `is_immutable_type(value: Any) -> bool`

Check if a value is already of an immutable type.

### `validate_immutable(value: Any) -> tuple[bool, str]`

Validate immutability without conversion. Returns `(is_valid, message)`.

### `ImmutabilityError`

Exception raised when a value cannot be made immutable. Inherits from `TypeError`.

## Examples

See:
- `tests/test_immutable_values.py` - Comprehensive test suite (39 tests)
- `tests/demo_immutable_values.py` - Interactive demonstration
- `docs/immutable_values.md` - Full documentation

## Dependencies

- **immutables** (`>=0.20`) - High-performance immutable collections

Added to `pyproject.toml` and `requirements.txt`.

## Design Philosophy

1. **Explicit is better than implicit** - Users call `make_immutable()` when needed
2. **Fail fast** - Unsupported types raise `ImmutabilityError` immediately
3. **No surprises** - Immutable types pass through unchanged (identity preserved)
4. **Performance-conscious** - Zero overhead for already-immutable values
5. **Type-safe** - Full type hints for static analysis

## Integration with Nexus System

The immutable values module is designed to work seamlessly with the nexus system:

```python
from observables._hooks.floating_hook import FloatingHook
from observables._nexus_system.immutable_values import make_immutable

# Ensure data immutability before storage
config = {"host": "localhost", "port": 8080}
immutable_config = make_immutable(config)

hook = FloatingHook(immutable_config)
# hook.value is now an immutables.Map, protected from modification
```

## Testing

Run tests:
```bash
pytest tests/test_immutable_values.py -v
```

Run demonstration:
```bash
python tests/demo_immutable_values.py
```

## Credits

- Uses the [immutables](https://github.com/MagicStack/immutables) library by MagicStack
- Inspired by functional programming principles and immutable data structures

