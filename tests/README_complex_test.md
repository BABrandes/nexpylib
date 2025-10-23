# Complex Interconnected Reactive System Test

This test demonstrates a sophisticated reactive system using the nexpylib library with multiple interconnected X objects.

## System Architecture

The test creates a complex reactive system with the following components:

1. **XSelectionSet** - Manages the selection of dictionary keys
2. **XSelectionDict** - Manages a dictionary with set values, key controlled by XSelectionSet
3. **XSetSequenceAdapter** - Bridges between set and sequence representations
4. **XSet** - Reactive set that receives values through the adapter

## Data Flow

```
XSelectionSet (keys: A,B,C,D) 
    ↓ (selected_option_hook)
XSelectionDict (dict: {A: {1,2,3}, B: {4,5,6}, C: {7,8,9}, D: {10,11,12}})
    ↓ (value_hook)
XSetSequenceAdapter (set ↔ sequence conversion)
    ↓ (hook_set)
XSet (reactive set operations)
```

## Key Features Tested

### 1. Reactive Key Selection
- XSelectionSet controls which key is active in XSelectionDict
- Changing the selected key automatically updates all connected components

### 2. Set-Value Dictionary
- Dictionary values are sets of numbers
- Each key maps to a different set of integers

### 3. Adapter Integration
- XSetSequenceAdapter converts between set and sequence representations
- Custom sorting function ensures predictable order
- Validates uniqueness in sequences

### 4. Bidirectional Updates
- Changes to XSet propagate back through the adapter to the dictionary
- Changes to dictionary values propagate forward to XSet
- All components stay synchronized

### 5. Complex Operations
- Set operations (union, intersection, difference)
- Dynamic key management (add/remove keys)
- Error handling for invalid states

## Test Scenarios

### Basic Reactive Updates
1. Change selected key from 'A' to 'B' to 'C' to 'D'
2. Verify all components update reactively
3. Test direct modification of reactive set
4. Test direct modification of dictionary values

### Advanced Operations
1. Add new key 'E' to the system
2. Test complex set operations (union, intersection, difference)
3. Test rapid key changes for system stability

### Error Handling
1. Attempt to select non-existent keys
2. Test adapter validation (duplicate elements)
3. Test invalid dictionary states

### Custom Configurations
1. Test with custom sorting functions
2. Test adapter behavior with different configurations

## Running the Test

### Prerequisites
```bash
# Install dependencies
pip install typing-extensions

# Install the package in development mode
pip install -e .
```

### Execution
```bash
# Run the test directly
python tests/test_complex_interconnected_system.py

# Or run with pytest (if available)
pytest tests/test_complex_interconnected_system.py -v
```

## Expected Output

The test will output progress messages as it executes each scenario:

```
Testing key change from 'A' to 'B'...
Testing key change from 'B' to 'C'...
Testing key change from 'C' to 'D'...
Testing direct modification of reactive set...
Testing direct modification of dict value...
Testing addition of new key 'E'...
Testing complex set operations...
Testing edge cases...
Testing adapter sequence validation...
Testing final system state...
Final system state:
  Selected key: A
  Dict value: {17, 19}
  Set value: {17, 19}
  Adapter sequence: [17, 19]
  Available keys: {'A', 'B', 'C', 'D'}
Testing rapid changes...
Complex interconnected system test completed successfully!
```

## System Benefits

This test demonstrates the power of the nexpylib reactive system:

1. **Automatic Synchronization** - All components stay in sync automatically
2. **Type Safety** - Strong typing throughout the system
3. **Flexible Architecture** - Easy to add/remove components
4. **Error Handling** - Comprehensive validation and error reporting
5. **Performance** - Efficient reactive updates without manual coordination

## Use Cases

This pattern is useful for:
- UI state management with complex data relationships
- Configuration systems with interdependent settings
- Data processing pipelines with multiple transformation steps
- Real-time systems requiring synchronized state updates
