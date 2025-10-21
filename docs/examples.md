# Examples

This document provides practical, runnable examples demonstrating NexPy's features and common usage patterns.

---

## Table of Contents

- [Basic Examples](#basic-examples)
- [Hook Fusion Examples](#hook-fusion-examples)
- [Reactive Collections](#reactive-collections)
- [Selection Objects](#selection-objects)
- [Internal Synchronization](#internal-synchronization)
- [Validation and Error Handling](#validation-and-error-handling)
- [Listeners and Callbacks](#listeners-and-callbacks)
- [Real-World Use Cases](#real-world-use-cases)

---

## Basic Examples

### Example 1: Simple Reactive Value

```python
import nexpy as nx

# Create a reactive value
temperature = nx.XValue(20.0)

# Read the value
print(f"Current temperature: {temperature.value}°C")

# Update the value
temperature.value = 25.5
print(f"New temperature: {temperature.value}°C")

# Access the underlying hook
hook = temperature.value_hook
print(f"Hook value: {hook.value}°C")
```

**Output:**
```
Current temperature: 20.0°C
New temperature: 25.5°C
Hook value: 25.5°C
```

### Example 2: Creating Independent Hooks

```python
import nexpy as nx

# Create floating hooks (not owned by any object)
sensor1 = nx.FloatingHook(18.0)
sensor2 = nx.FloatingHook(22.0)
sensor3 = nx.FloatingHook(20.0)

# Each hook is independent
print(f"Sensor 1: {sensor1.value}°C")
print(f"Sensor 2: {sensor2.value}°C")
print(f"Sensor 3: {sensor3.value}°C")

# Update one sensor
sensor1.value = 19.5
print(f"Sensor 1 after update: {sensor1.value}°C")
print(f"Sensor 2 (unchanged): {sensor2.value}°C")
```

**Output:**
```
Sensor 1: 18.0°C
Sensor 2: 22.0°C
Sensor 3: 20.0°C
Sensor 1 after update: 19.5°C
Sensor 2 (unchanged): 22.0°C
```

---

## Hook Fusion Examples

### Example 3: Basic Join Operation

```python
import nexpy as nx

# Create two independent hooks
source = nx.FloatingHook(100)
target = nx.FloatingHook(0)

print(f"Before join: source={source.value}, target={target.value}")

# Join them (target adopts source's value)
source.join(target)

print(f"After join: source={source.value}, target={target.value}")

# Now they're synchronized
source.value = 200
print(f"After update: source={source.value}, target={target.value}")
```

**Output:**
```
Before join: source=100, target=0
After join: source=100, target=100
After update: source=200, target=200
```

### Example 4: Transitive Synchronization

```python
import nexpy as nx

# Create a network of hooks
A = nx.FloatingHook(1)
B = nx.FloatingHook(2)
C = nx.FloatingHook(3)
D = nx.FloatingHook(4)

# Create separate fusion domains
A.join(B)  # Domain 1: {A, B}
C.join(D)  # Domain 2: {C, D}

print("Two separate domains:")
print(f"  Domain 1: A={A.value}, B={B.value}")
print(f"  Domain 2: C={C.value}, D={D.value}")

# Fuse both domains by connecting any pair
B.join(C)

print("\nAfter fusion:")
print(f"  A={A.value}, B={B.value}, C={C.value}, D={D.value}")

# All hooks now synchronized, even though A and D were never joined directly
A.value = 999
print(f"\nAfter A update: A={A.value}, B={B.value}, C={C.value}, D={D.value}")
```

**Output:**
```
Two separate domains:
  Domain 1: A=1, B=1
  Domain 2: C=3, D=3

After fusion:
  A=1, B=1, C=1, D=1

After A update: A=999, B=999, C=999, D=999
```

### Example 5: Isolate Operation

```python
import nexpy as nx

# Create a fusion domain
A = nx.FloatingHook(10)
B = nx.FloatingHook(10)
C = nx.FloatingHook(10)

A.join(B)
B.join(C)

print(f"Fused: A={A.value}, B={B.value}, C={C.value}")

# Isolate B
B.isolate()

# B is now independent
A.value = 50
print(f"After isolate and update: A={A.value}, B={B.value}, C={C.value}")

# B can change independently
B.value = 99
print(f"After B update: A={A.value}, B={B.value}, C={C.value}")
```

**Output:**
```
Fused: A=10, B=10, C=10
After isolate and update: A=50, B=10, C=50
After B update: A=50, B=99, C=50
```

### Example 6: Fusing Reactive Objects

```python
import nexpy as nx

# Create two reactive values
model_data = nx.XValue({"user": "Alice", "age": 30})
cache_data = nx.XValue({})

# Fuse them
model_data.value_hook.join(cache_data.value_hook)

print(f"Model: {model_data.value}")
print(f"Cache: {cache_data.value}")

# Update model updates cache
model_data.value = {"user": "Bob", "age": 25}
print(f"\nAfter model update:")
print(f"Model: {model_data.value}")
print(f"Cache: {cache_data.value}")
```

**Output:**
```
Model: {'user': 'Alice', 'age': 30}
Cache: {'user': 'Alice', 'age': 30}

After model update:
Model: {'user': 'Bob', 'age': 25}
Cache: {'user': 'Bob', 'age': 25}
```

---

## Reactive Collections

### Example 7: Reactive List

```python
import nexpy as nx

# Create a reactive list
numbers = nx.XList([1, 2, 3])

print(f"Initial list: {numbers.list}")
print(f"Length: {numbers.length}")

# Append elements
numbers.append(4)
numbers.append(5)

print(f"\nAfter appends: {numbers.list}")
print(f"Length: {numbers.length}")

# Direct list modification
numbers.list = [10, 20, 30, 40, 50]
print(f"\nAfter direct modification: {numbers.list}")
print(f"Length: {numbers.length}")
```

**Output:**
```
Initial list: [1, 2, 3]
Length: 3

After appends: [1, 2, 3, 4, 5]
Length: 5

After direct modification: [10, 20, 30, 40, 50]
Length: 5
```

### Example 8: Reactive Set

```python
import nexpy as nx

# Create a reactive set
tags = nx.XSet({"python", "reactive", "sync"})

print(f"Initial tags: {tags.set}")

# Add elements
tags.add("framework")
tags.add("library")

print(f"After adding: {tags.set}")

# Remove element
tags.remove("sync")
print(f"After removing: {tags.set}")

# Check membership
print(f"\n'python' in tags: {'python' in tags.set}")
print(f"'java' in tags: {'java' in tags.set}")
```

**Output:**
```
Initial tags: {'python', 'reactive', 'sync'}
After adding: {'python', 'reactive', 'sync', 'framework', 'library'}
After removing: {'python', 'reactive', 'framework', 'library'}

'python' in tags: True
'java' in tags: False
```

### Example 9: Reactive Dictionary

```python
import nexpy as nx

# Create a reactive dictionary
config = nx.XDict({"debug": False, "version": "1.0", "timeout": 30})

print(f"Initial config: {config.dict}")

# Update values
config["debug"] = True
config["port"] = 8080

print(f"After updates: {config.dict}")

# Get keys and values
print(f"\nKeys: {list(config.dict.keys())}")
print(f"Values: {list(config.dict.values())}")
```

**Output:**
```
Initial config: {'debug': False, 'version': '1.0', 'timeout': 30}
After updates: {'debug': True, 'version': '1.0', 'timeout': 30, 'port': 8080}

Keys: ['debug', 'version', 'timeout', 'port']
Values: [True, '1.0', 30, 8080]
```

---

## Selection Objects

### Example 10: Dictionary Selection

```python
import nexpy as nx

# Create a selection from a dictionary
themes = nx.XDictSelect(
    {"light": "#FFFFFF", "dark": "#000000", "blue": "#0000FF"},
    key="light"
)

print(f"Selected theme: {themes.key}")
print(f"Theme color: {themes.value}")

# Change selection
themes.key = "dark"
print(f"\nAfter selection change:")
print(f"Selected theme: {themes.key}")
print(f"Theme color: {themes.value}")

# Modify the selected value
themes.value = "#111111"
print(f"\nAfter value change:")
print(f"Dictionary: {themes.dict}")
```

**Output:**
```
Selected theme: light
Theme color: #FFFFFF

After selection change:
Selected theme: dark
Theme color: #000000

After value change:
Dictionary: {'light': '#FFFFFF', 'dark': '#111111', 'blue': '#0000FF'}
```

### Example 11: Set Single Selection

```python
import nexpy as nx

# Create a selection from a set
options = nx.XSetSingleSelect({1, 2, 3, 4, 5}, selection=3)

print(f"Available options: {options.set}")
print(f"Selected: {options.selection}")

# Change selection
options.selection = 5
print(f"\nNew selection: {options.selection}")

# Add new option and select it
options.add(10)
options.selection = 10
print(f"\nAfter adding and selecting:")
print(f"Available: {options.set}")
print(f"Selected: {options.selection}")
```

**Output:**
```
Available options: {1, 2, 3, 4, 5}
Selected: 3

New selection: 5

After adding and selecting:
Available: {1, 2, 3, 4, 5, 10}
Selected: 10
```

### Example 12: Multi-Selection from Set

```python
import nexpy as nx

# Create a multi-selection set
available_features = {"feature_a", "feature_b", "feature_c", "feature_d"}
selected_features = {"feature_a", "feature_c"}

features = nx.XSetMultiSelect(
    universe=available_features,
    selection=selected_features
)

print(f"Available features: {features.universe}")
print(f"Selected features: {features.selection}")

# Add to selection
features.select("feature_b")
print(f"\nAfter selecting feature_b: {features.selection}")

# Remove from selection
features.deselect("feature_a")
print(f"After deselecting feature_a: {features.selection}")
```

**Output:**
```
Available features: {'feature_a', 'feature_b', 'feature_c', 'feature_d'}
Selected features: {'feature_a', 'feature_c'}

After selecting feature_b: {'feature_a', 'feature_c', 'feature_b'}
After deselecting feature_a: {'feature_c', 'feature_b'}
```

---

## Internal Synchronization

### Example 13: Automatic Value Completion

```python
import nexpy as nx

# Create a selection dict
options = nx.XDictSelect(
    {"small": 10, "medium": 20, "large": 30},
    key="medium"
)

print(f"Initial state:")
print(f"  Key: {options.key}")
print(f"  Value: {options.value}")

# Update only the key - value is automatically completed
options.key = "large"

print(f"\nAfter key change:")
print(f"  Key: {options.key}")
print(f"  Value: {options.value} (automatically updated)")

# Update only the value - dict is automatically updated
options.value = 35

print(f"\nAfter value change:")
print(f"  Dict: {options.dict}")
print(f"  Value at 'large': {options.dict['large']} (automatically updated)")
```

**Output:**
```
Initial state:
  Key: medium
  Value: 20

After key change:
  Key: large
  Value: 30 (automatically updated)

After value change:
  Dict: {'small': 10, 'medium': 20, 'large': 35}
  Value at 'large': 35 (automatically updated)
```

### Example 14: Atomic Multi-Hook Updates

```python
import nexpy as nx

# Create a selection dict
select = nx.XDictSelect(
    {"a": 1, "b": 2, "c": 3},
    key="a"
)

# Track updates
updates = []

def track_key_update():
    updates.append(("key", select.key))

def track_value_update():
    updates.append(("value", select.value))

select.key_hook.add_listener(track_key_update)
select.value_hook.add_listener(track_value_update)

# Change key (triggers atomic update of both key and value)
select.key = "c"

print("Updates recorded:")
for hook_name, value in updates:
    print(f"  {hook_name} = {value}")

print(f"\nFinal state: key={select.key}, value={select.value}")
```

**Output:**
```
Updates recorded:
  key = c
  value = 3

Final state: key=c, value=3
```

---

## Validation and Error Handling

### Example 15: Custom Validation

```python
import nexpy as nx

# Create a hook with validation
def validate_positive(value):
    if value > 0:
        return True, "Valid positive number"
    return False, "Value must be positive"

positive_number = nx.FloatingHook(10, isolated_validation_callback=validate_positive)

print(f"Initial value: {positive_number.value}")

# Valid update
positive_number.value = 50
print(f"After valid update: {positive_number.value}")

# Invalid update
try:
    positive_number.value = -10
except ValueError as e:
    print(f"\nInvalid update rejected: {e}")
    print(f"Value unchanged: {positive_number.value}")
```

**Output:**
```
Initial value: 10
After valid update: 50

Invalid update rejected: Value must be positive
Value unchanged: 50
```

### Example 16: Selection Validation

```python
import nexpy as nx

# Create a selection with restricted keys
config = nx.XDictSelect(
    {"mode_a": 1, "mode_b": 2, "mode_c": 3},
    key="mode_a"
)

print(f"Current mode: {config.key}")

# Valid selection change
config.key = "mode_b"
print(f"Changed to: {config.key}")

# Invalid selection (key doesn't exist)
try:
    config.key = "mode_z"
except KeyError as e:
    print(f"\nInvalid selection rejected: {e}")
    print(f"Mode unchanged: {config.key}")
```

**Output:**
```
Current mode: mode_a
Changed to: mode_b

Invalid selection rejected: Key mode_z not in dictionary
Mode unchanged: mode_b
```

### Example 17: Cross-Object Validation

```python
import nexpy as nx

# Two selection objects with different dictionaries
select1 = nx.XDictSelect({"a": 1, "b": 2}, key="a")
select2 = nx.XDictSelect({"x": 10, "y": 20}, key="x")

# Join their dict hooks
select1.dict_hook.join(select2.dict_hook)

# Now they share the same dict
print(f"Select1 dict: {select1.dict}")
print(f"Select2 dict: {select2.dict}")

# This update will fail because it doesn't contain select2's key="x"
try:
    select1.change_dict_and_key({"c": 3, "d": 4}, "c")
except (ValueError, KeyError) as e:
    print(f"\nCross-object validation failed: {e}")
    print(f"Dict unchanged: {select1.dict}")
```

**Output:**
```
Select1 dict: {'a': 1, 'b': 2}
Select2 dict: {'a': 1, 'b': 2}

Cross-object validation failed: Key x not in dictionary
Dict unchanged: {'a': 1, 'b': 2}
```

---

## Listeners and Callbacks

### Example 18: Simple Listeners

```python
import nexpy as nx

# Create a reactive value
counter = nx.XValue(0)

# Add a listener
def on_counter_change():
    print(f"Counter changed to: {counter.value}")

counter.value_hook.add_listener(on_counter_change)

# Updates trigger the listener
print("Incrementing counter...")
counter.value = 1
counter.value = 2
counter.value = 3
```

**Output:**
```
Incrementing counter...
Counter changed to: 1
Counter changed to: 2
Counter changed to: 3
```

### Example 19: Multiple Listeners

```python
import nexpy as nx

temperature = nx.XValue(20.0)

# Add multiple listeners
def logger():
    print(f"[LOG] Temperature: {temperature.value}°C")

def alert_high():
    if temperature.value > 30:
        print("[ALERT] High temperature!")

def alert_low():
    if temperature.value < 10:
        print("[ALERT] Low temperature!")

temperature.value_hook.add_listener(logger)
temperature.value_hook.add_listener(alert_high)
temperature.value_hook.add_listener(alert_low)

# Trigger listeners
print("Setting temperature to 35°C:")
temperature.value = 35.0

print("\nSetting temperature to 5°C:")
temperature.value = 5.0
```

**Output:**
```
Setting temperature to 35°C:
[LOG] Temperature: 35.0°C
[ALERT] High temperature!

Setting temperature to 5°C:
[LOG] Temperature: 5.0°C
[ALERT] Low temperature!
```

### Example 20: Listeners in Fusion Domains

```python
import nexpy as nx

A = nx.FloatingHook(10)
B = nx.FloatingHook(10)

# Each hook has its own listener
A.add_listener(lambda: print("A was updated"))
B.add_listener(lambda: print("B was updated"))

# Join them
A.join(B)

print("Updating A:")
A.value = 20
# Both listeners triggered because both hooks are updated

print("\nUpdating B:")
B.value = 30
# Both listeners triggered again
```

**Output:**
```
Updating A:
A was updated
B was updated

Updating B:
A was updated
B was updated
```

---

## Real-World Use Cases

### Example 21: GUI Data Binding

```python
import nexpy as nx

# Model
class UserModel:
    def __init__(self, name, email):
        self.name = nx.XValue(name)
        self.email = nx.XValue(email)

# View (simulated)
class TextView:
    def __init__(self, label, hook):
        self.label = label
        self.hook = hook
        hook.add_listener(self.refresh)
        self.refresh()  # Initial display
    
    def refresh(self):
        print(f"[{self.label}] Display: {self.hook.value}")

# Create model and views
user = UserModel("Alice", "alice@example.com")
name_widget = TextView("Name Widget", user.name.value_hook)
email_widget = TextView("Email Widget", user.email.value_hook)

# Update model -> views refresh automatically
print("\nChanging name to 'Bob':")
user.name.value = "Bob"

print("\nChanging email:")
user.email.value = "bob@example.com"
```

**Output:**
```
[Name Widget] Display: Alice
[Email Widget] Display: alice@example.com

Changing name to 'Bob':
[Name Widget] Display: Bob

Changing email:
[Email Widget] Display: bob@example.com
```

### Example 22: Configuration Synchronization

```python
import nexpy as nx

# Application configuration
app_config = nx.XDict({
    "theme": "dark",
    "language": "en",
    "timeout": 30
})

# Cache/backup configuration
cache_config = nx.XDict({})

# Synchronize configurations
app_config.dict_hook.join(cache_config.dict_hook)

print("Initial state:")
print(f"  App config: {app_config.dict}")
print(f"  Cache config: {cache_config.dict}")

# Update app config -> cache automatically synchronized
app_config["theme"] = "light"
app_config["language"] = "fr"

print("\nAfter app config update:")
print(f"  App config: {app_config.dict}")
print(f"  Cache config: {cache_config.dict}")
```

**Output:**
```
Initial state:
  App config: {'theme': 'dark', 'language': 'en', 'timeout': 30}
  Cache config: {'theme': 'dark', 'language': 'en', 'timeout': 30}

After app config update:
  App config: {'theme': 'light', 'language': 'fr', 'timeout': 30}
  Cache config: {'theme': 'light', 'language': 'fr', 'timeout': 30}
```

### Example 23: State Machine with Validated Transitions

```python
import nexpy as nx

# State machine states
states = {"idle", "running", "paused", "stopped"}

# Create selection for current state
state_machine = nx.XDictSelect(
    {state: state for state in states},
    key="idle"
)

# Add validation for state transitions
previous_state = "idle"

def validate_transition(values):
    global previous_state
    new_state = values["key"]
    
    # Define allowed transitions
    allowed = {
        "idle": {"running"},
        "running": {"paused", "stopped"},
        "paused": {"running", "stopped"},
        "stopped": set()  # No transitions from stopped
    }
    
    if new_state not in allowed.get(previous_state, set()):
        return False, f"Cannot transition from {previous_state} to {new_state}"
    
    previous_state = new_state
    return True, "Valid transition"

# Note: This is a simplified example. In practice, you'd implement
# validation through the XDictSelect's validation system

print(f"Initial state: {state_machine.key}")

# Valid transitions
state_machine.key = "running"
print(f"State: {state_machine.key}")

state_machine.key = "paused"
print(f"State: {state_machine.key}")

state_machine.key = "stopped"
print(f"State: {state_machine.key}")
```

**Output:**
```
Initial state: idle
State: running
State: paused
State: stopped
```

### Example 24: Sensor Aggregation

```python
import nexpy as nx

# Multiple temperature sensors
sensors = [nx.XValue(20.0 + i) for i in range(5)]

# Master aggregator
master = nx.XValue(0.0)

# Join all sensors to master
for sensor in sensors:
    sensor.value_hook.join(master.value_hook)

print("All sensors synchronized:")
for i, sensor in enumerate(sensors):
    print(f"  Sensor {i+1}: {sensor.value}°C")

# Update master -> all sensors update
print("\nSetting master to 25.0°C:")
master.value = 25.0

for i, sensor in enumerate(sensors):
    print(f"  Sensor {i+1}: {sensor.value}°C")

# Update any sensor -> all others update
print("\nSensor 3 reads 28.0°C:")
sensors[2].value = 28.0

for i, sensor in enumerate(sensors):
    print(f"  Sensor {i+1}: {sensor.value}°C")
print(f"  Master: {master.value}°C")
```

**Output:**
```
All sensors synchronized:
  Sensor 1: 20.0°C
  Sensor 2: 20.0°C
  Sensor 3: 20.0°C
  Sensor 4: 20.0°C
  Sensor 5: 20.0°C

Setting master to 25.0°C:
  Sensor 1: 25.0°C
  Sensor 2: 25.0°C
  Sensor 3: 25.0°C
  Sensor 4: 25.0°C
  Sensor 5: 25.0°C

Sensor 3 reads 28.0°C:
  Sensor 1: 28.0°C
  Sensor 2: 28.0°C
  Sensor 3: 28.0°C
  Sensor 4: 28.0°C
  Sensor 5: 28.0°C
  Master: 28.0°C
```

---

---

## Advanced: Custom Equality Checks

### Example 25: Floating-Point Tolerance

```python
import nexpy as nx
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Standard practice: Configure floating-point equality with 1e-9 tolerance
# BEFORE creating any hooks or x_objects
def float_equality(a: float, b: float) -> bool:
    return abs(a - b) < 1e-9

DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), float_equality)

# Track update count
update_count = 0

def on_update():
    global update_count
    update_count += 1
    print(f"Update #{update_count}: {temperature.value}")

# Create reactive value
temperature = nx.XValue(20.0)
temperature.value_hook.add_listener(on_update)

# These don't trigger updates (within tolerance)
temperature.value = 20.0000000001  # No update
temperature.value = 20.0 + 1e-15   # No update
print(f"Update count: {update_count}")  # 0

# This triggers an update (exceeds tolerance)
temperature.value = 20.001
print(f"Update count: {update_count}")  # 1
```

**Output:**
```
Update count: 0
Update #1: 20.001
Update count: 1
```

### Example 26: Cross-Type Equality

```python
import nexpy as nx
from nexpy.core.nexus_system.default_nexus_manager import DEFAULT_NEXUS_MANAGER

# Configure float-int cross-type comparison
def float_int_equality(a: float, b: int) -> bool:
    return abs(a - b) < 1e-9

DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, float), lambda a, b: abs(a - b) < 1e-9)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((float, int), float_int_equality)
DEFAULT_NEXUS_MANAGER.add_value_equality_callback((int, float), lambda a, b: float_int_equality(b, a))

# Create value with float
value = nx.XValue(10.0)
updates = []
value.value_hook.add_listener(lambda: updates.append(value.value))

# These are considered equal
value.value = 10      # int 10 ≈ float 10.0 (no update)
value.value = 10.0    # float 10.0 = float 10.0 (no update)
print(f"Updates: {len(updates)}")  # 0

# This exceeds tolerance
value.value = 10.5
print(f"Updates: {len(updates)}")  # 1
```

**Output:**
```
Updates: 0
Updates: 1
```

### Example 27: Per-Manager Custom Equality

```python
import nexpy as nx
from nexpy.core.nexus_system.nexus_manager import NexusManager

# Create managers with different precision requirements
high_precision_manager = NexusManager()
high_precision_manager.add_value_equality_callback(
    (float, float),
    lambda a, b: abs(a - b) < 1e-12  # Very tight tolerance
)

low_precision_manager = NexusManager()
low_precision_manager.add_value_equality_callback(
    (float, float),
    lambda a, b: abs(a - b) < 1e-6   # Looser tolerance
)

# Create values with different managers
precise = nx.XValue(1.0, nexus_manager=high_precision_manager)
rough = nx.XValue(1.0, nexus_manager=low_precision_manager)

precise_updates = []
rough_updates = []

precise.value_hook.add_listener(lambda: precise_updates.append(precise.value))
rough.value_hook.add_listener(lambda: rough_updates.append(rough.value))

# Small change
delta = 1e-9
precise.value = 1.0 + delta  # Triggers update (exceeds 1e-12)
rough.value = 1.0 + delta    # No update (within 1e-6)

print(f"Precise updates: {len(precise_updates)}")  # 1
print(f"Rough updates: {len(rough_updates)}")      # 0
```

**Output:**
```
Precise updates: 1
Rough updates: 0
```

---

## Next Steps

- **[Usage Guide](usage.md)** — Learn join/isolate mechanics
- **[Internal Synchronization](internal_sync.md)** — Understand atomic updates
- **[API Reference](api_reference.md)** — Complete API documentation
- **[Concepts](concepts.md)** — Deep dive into fusion domains

---

**[Back to README](../README.md)**

