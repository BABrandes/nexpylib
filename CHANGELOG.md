# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-10-21

### Added
- **Base Classes for Custom X Objects**: `XSimpleBase` and `XCompositeBase` base classes for creating custom reactive objects
  - `XSimpleBase`: For single-value reactive wrappers with validation
  - `XCompositeBase`: For complex objects with multiple interdependent hooks and internal synchronization
  - Full documentation and examples in API reference
- **Custom Validator Support**: New `validate_complete_values_custom_callback` parameter in `XCompositeBase`
  - Allows additional validation across all values (primary + secondary)
  - Called after primary validation and secondary computation
  - Enables cross-validation between primary and derived values
- **XBase Protocol**: New unified base protocol `XBase` for all X objects
  - Replaces previous fragmented base class structure
  - Provides consistent interface for hook management and synchronization

### Changed
- **Refactored Base Class Architecture**: 
  - Removed `carries_some_hooks_base.py` and consolidated into `x_base.py`
  - Removed `src/nexpy/core/nexus_system/__init__.py`
  - Improved type safety and consistency across base classes
- **Documentation**: Updated all documentation to use correct class names
  - Fixed `XSetSelect` → `XSetSingleSelect` throughout documentation
  - Added comprehensive guide for creating custom X objects
  - Documented validation order and custom validator feature

### Fixed
- Documentation inconsistencies with exported class names
- API reference now accurately reflects available exports

## [0.1.0] - 2024-01-01

### Added
- Initial release
- Basic nexpy package structure
- Core module with version information
