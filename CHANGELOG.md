# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.2] - 2025-01-29

### Fixed
- **Callback Signature Issues**: Fixed incorrect `self_ref` parameter in callback functions
  - Removed unnecessary `self_ref` parameter from nested callback functions
  - Callbacks now correctly use `self` from closure scope
  - Fixes 95 failing tests across the test suite
  - Affects `XCompositeBase`, `XSingletonBase`, `XAdapterBase`, `XFunction`, `XOneWayFunction`, and `XRootedPaths`

### Changed
- **Performance Optimization**: Improved callback invocation performance
  - Eliminated unnecessary argument passing for callback functions
  - Leverages Python closure mechanism for more efficient variable access
  - Slight performance improvement in high-frequency operations (value updates, validations)

### Technical Details
- Updated all internal validation and value completion callbacks to use proper closure pattern
- Ensures correct signature matching with `XBase` callback invocation expectations
- All 714 tests now passing (up from 619)

## [0.4.1] - 2025-01-29

### Fixed
- **Nexus Type Compatibility**: Relaxed strict type checking in nexus merging
  - Allows joining compatible types (e.g., `set` and `frozenset`)
  - Values are already synchronized before merging, ensuring compatibility
  - Fixes overly restrictive type checking that prevented valid use cases

### Changed
- **Internal Type Validation**: Removed unnecessary strict type equality checks
  - Improved flexibility in nexus fusion for compatible types
  - Better support for conceptually equivalent value types

## [0.4.0] - 2025-01-29

### Changed
- **Hook System Architecture**: Complete overhaul of internal hook type system
  - Replaced generic `OwnedHook` with specialized hook types: `OwnedReadOnlyHook` and `OwnedWritableHook`
  - Clear separation between read-only and writable hooks based on use case
  - Improved type safety and API clarity with specific hook implementations
  - Read-only hooks for computed/derived values, writable hooks for primary values
- **Documentation Refactoring**: Comprehensive API documentation updates
  - Clarified hook system architecture with accurate hook type documentation
  - Replaced generic `OwnedHook` references with specific `OwnedReadOnlyHook` and `OwnedWritableHook` types
  - Updated all documentation to reflect actual API implementation
- **Terminology Updates**: Unified terminology across all documentation
  - Replaced "Observables" with "NexPy" branding
  - Changed "observable objects" to "NexPy objects" or "X objects"
  - Updated "bindings" to "fusion domains"
  - Updated class name references to modern conventions

### Documentation
- **API Reference**: Complete rewrite of hook documentation with accurate API details
- **Usage Guide**: Updated hook usage examples and use cases
- **Architecture**: Updated architectural diagrams and component lists
- **Module Documentation**: Updated core module docstrings and examples
- **Protocol Documentation**: Updated serialization protocol terminology

### Fixed
- **Documentation Accuracy**: Fixed all inconsistencies between documentation and actual API
- **Terminology**: Unified terminology throughout all documentation files
- **Examples**: Updated all code examples to use correct API and modern conventions

## [0.3.0] - 2025-10-25

### Added
- **New Adapter System**: Comprehensive adapter framework for type conversion and data transformation
  - `XIntFloatAdapter`: Seamless conversion between integer and float types
  - `XOptionalAdapter`: Handle optional values with automatic None handling
  - `XSetSequenceAdapter`: Convert between sets and sequences while maintaining uniqueness
- **Enhanced Performance**: Multiple performance optimization commits
  - Improved internal submission methods with adaptive selection
  - Optimized hook management and memory usage
  - Enhanced caching mechanisms for better scalability
- **Advanced Testing Framework**: Comprehensive test suite expansion
  - `test_adaptive_submission.py`: Tests for performance-adaptive submission methods
  - `test_complex_interconnected_system.py`: Complex system integration tests
  - `test_comprehensive_performance_analysis.py`: Detailed performance benchmarking
  - `test_submit_methods_performance.py`: Submission method performance tests
- **Documentation**: Extensive API documentation and examples
  - Complete API reference documentation
  - Comprehensive usage examples and patterns
  - Performance analysis reports and benchmarks
- **Nexus ID System**: Unique identification for nexus objects
- **Foundation Classes**: Enhanced base classes for better extensibility
  - `XAdapterBase`: Base class for all adapter implementations
  - Improved `XBase` and `XCompositeBase` classes
- **Publisher-Subscriber Improvements**: Enhanced pub/sub system with better error handling

### Changed
- **Architecture Refactoring**: Major internal restructuring for better maintainability
  - Moved utilities to `core/utils.py`
  - Reorganized foundation classes into dedicated module
  - Improved module organization and imports
- **Performance Optimizations**: Significant performance improvements across the board
  - Optimized hook operations and memory management
  - Improved binding performance and reduced overhead
  - Enhanced internal synchronization mechanisms
- **Code Quality**: Improved code structure and maintainability
  - Fixed warnings and improved type safety
  - Better error handling and validation
  - Enhanced code documentation and comments

### Fixed
- **Memory Management**: Improved memory leak prevention and cleanup
- **Thread Safety**: Enhanced thread safety for concurrent operations
- **Validation**: Better input validation and error handling
- **Documentation**: Fixed documentation inconsistencies and improved clarity

### Removed
- **Deprecated Features**: Removed obsolete `XObjectBlockNone` class
- **Legacy Code**: Cleaned up unused utilities and deprecated methods

### Performance
- **Massive Performance Improvements**: Multiple commits focused on optimization
- **Adaptive Submission**: Intelligent submission method selection based on system state
- **Memory Optimization**: Reduced memory footprint and improved garbage collection
- **Scalability**: Better performance with large numbers of objects and bindings

### Testing
- **Comprehensive Test Coverage**: 692 tests passing with 78% code coverage
- **Performance Testing**: Dedicated performance and scalability tests
- **Memory Testing**: Comprehensive memory leak and cleanup tests
- **Integration Testing**: Complex system integration and edge case testing

### Documentation
- **API Reference**: Complete API documentation with examples
- **Usage Guide**: Comprehensive usage patterns and best practices
- **Performance Analysis**: Detailed performance reports and benchmarks
- **Architecture Documentation**: Internal architecture and design decisions

## [0.2.0] - Previous Release

### Added
- Initial adapter system foundation
- Basic performance optimizations
- Core testing framework

### Changed
- Improved internal architecture
- Enhanced error handling

### Fixed
- Various bug fixes and improvements

## [0.1.0] - Initial Release

### Added
- Core reactive programming framework
- Basic hook system
- Initial XObject implementations
- Fundamental binding and synchronization