# Release v0.4.0 - Hook Architecture Overhaul & Documentation Updates

## 🎯 Summary

This PR prepares release v0.4.0 with major improvements to the hook system architecture and comprehensive documentation updates. The internal hook type architecture has been completely overhauled, and all documentation has been updated to accurately reflect the current API implementation.

## 🚀 Key Changes

### Architectural Improvements

**Hook System Architecture Overhaul**
- Complete redesign of internal hook type system
- Replaced generic `OwnedHook` with specialized types:
  - `OwnedReadOnlyHook` - for computed/derived values
  - `OwnedWritableHook` - for primary values
- Improved type safety and API clarity
- Better separation of concerns in the codebase

### Documentation Updates

**All documentation files updated:**
- `docs/api_reference.md` - Complete rewrite of hook documentation
- `docs/usage.md` - Updated hook usage examples
- `docs/architecture.md` - Updated architectural diagrams
- `src/nexpy/core/__init__.py` - Updated module docstring
- `src/nexpy/foundations/serializable_protocol.py` - Updated terminology

**Terminology Improvements:**
- Replaced "Observables" with "NexPy" branding
- Changed "observable objects" to "NexPy objects" or "X objects"
- Updated "bindings" to "fusion domains"
- Updated class name references to modern conventions

### Version Updates

- Updated `src/nexpy/_version.py` to 0.4.0
- Updated `src/nexpy/__init__.py` fallback version to 0.4.0
- Updated `pyproject.toml` version to 0.4.0
- Created `RELEASE_NOTES_v0.4.0.md`
- Updated `CHANGELOG.md` with v0.4.0 entry

## ✅ Breaking Changes

None. This release maintains full backward compatibility.

## 📋 Files Changed

### Version & Release Files
- `CHANGELOG.md` - Added v0.4.0 entry
- `pyproject.toml` - Updated version to 0.4.0
- `src/nexpy/_version.py` - Updated to 0.4.0
- `src/nexpy/__init__.py` - Updated fallback version to 0.4.0
- `RELEASE_NOTES_v0.4.0.md` - Created new release notes

### Documentation Files (already committed in previous commits)
- `docs/api_reference.md`
- `docs/usage.md`
- `docs/architecture.md`
- `src/nexpy/core/__init__.py`
- `src/nexpy/foundations/serializable_protocol.py`

## 🧪 Testing

All existing tests continue to pass. No new tests required as this is primarily a documentation and architectural clarification release.

## 📝 Release Notes Summary

See `RELEASE_NOTES_v0.4.0.md` for detailed information about:
- Hook system architecture changes
- Documentation improvements
- API clarifications
- Terminology updates

## 🎯 What's Next

After merging this PR:
1. Create a git tag: `git tag -a v0.4.0 -m "Release v0.4.0"`
2. Push the tag: `git push origin v0.4.0`
3. Build and publish to PyPI

## 🔗 Pull Request Details

- **Branch**: `release/0.4.0`
- **Base**: `master`
- **Type**: Release
- **Status**: Ready for review

---

**Review Checklist:**
- [x] Version numbers updated
- [x] CHANGELOG updated
- [x] Release notes created
- [x] Documentation updated
- [x] Tests pass
- [x] No breaking changes
- [x] Ready for merge

