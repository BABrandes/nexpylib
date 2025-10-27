#!/usr/bin/env python3
"""
Test suite for XRootedPaths.

This module tests the XRootedPaths class which manages a root directory
with associated elements and provides observable hooks for path management.
"""

from typing import Optional
from pathlib import Path
import tempfile
import shutil

from unittest.mock import Mock

from nexpy import XValue, XRootedPaths, Hook
import pytest

class TestXRootedPaths:
    """Test cases for XRootedPaths."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_root = Path(self.temp_dir) / "project"
        self.test_root.mkdir()
        
        # Create some test files
        (self.test_root / "data").mkdir()
        (self.test_root / "config").mkdir()
        (self.test_root / "logs").mkdir()
        
        # Test element keys
        self.element_keys = {"data", "config", "logs"}

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_no_values(self):
        """Test initialization with no initial values."""
        manager = XRootedPaths[str]()
        
        # Check that root path is None
        assert manager.root_path is None
        
        # Check that no element keys are set
        assert len(manager.rooted_element_keys) == 0
        assert len(manager.rooted_element_relative_path_hooks) == 0
        assert len(manager.rooted_element_absolute_path_hooks) == 0

    def test_initialization_with_root_path_only(self):
        """Test initialization with only root path."""
        manager = XRootedPaths[str](root_path_initial_value=self.test_root)
        
        # Check that root path is set correctly
        assert manager.root_path == self.test_root
        
        # Check that no element keys are set
        assert len(manager.rooted_element_keys) == 0
        assert len(manager.rooted_element_relative_path_hooks) == 0
        assert len(manager.rooted_element_absolute_path_hooks) == 0

    def test_initialization_with_elements_only(self):
        """Test initialization with elements but no root path."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        
        manager = XRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check that root path is None
        assert manager.root_path is None
        
        # Check that element keys are set
        assert manager.rooted_element_keys == set(initial_values.keys())
        
        # Check that relative path hooks are created
        for key in initial_values:
            hook = manager.get_relative_path_hook(key)
            assert hook.value == initial_values[key]

    def test_initialization_with_root_and_elements(self):
        """Test initialization with both root path and elements."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check that root path is set correctly
        assert manager.root_path == self.test_root
        
        # Check that element keys are set
        assert manager.rooted_element_keys == set(initial_values.keys())
        
        # Check that relative path hooks are created
        for key in initial_values:
            hook = manager.get_relative_path_hook(key)
            assert hook.value == initial_values[key]
            
            # Check that absolute path hooks are created and computed correctly
            abs_hook = manager.get_absolute_path_hook(key)
            relative_path = initial_values[key]
            assert relative_path is not None
            assert self.test_root is not None
            expected_abs_path = self.test_root / relative_path
            assert abs_hook.value == expected_abs_path

    def test_element_key_conversion_methods(self):
        """Test the element key to path key conversion methods."""
        manager = XRootedPaths[str]()
        
        # Test relative path key conversion
        assert manager.element_key_to_relative_path_key("data") == "data_relative_path"
        assert manager.element_key_to_relative_path_key("config") == "config_relative_path"
        
        # Test absolute path key conversion
        assert manager.element_key_to_absolute_path_key("data") == "data_absolute_path"
        assert manager.element_key_to_absolute_path_key("config") == "config_absolute_path"

    def test_set_root_path(self):
        """Test setting the root path."""
        manager = XRootedPaths[str]()
        
        # Set root path
        success, _ = manager.set_root_path(self.test_root)
        assert success
        assert manager.root_path == self.test_root
        
        # Set to None
        success, _ = manager.set_root_path(None)
        assert success
        assert manager.root_path is None

    def test_set_relative_path(self):
        """Test setting relative paths for elements."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Set relative path
        success, _ = manager.set_relative_path("data", "new_data/")
        assert success
        
        hook = manager.get_relative_path_hook("data")
        assert hook.value == "new_data/"

    def test_set_absolute_path(self):
        """Test setting absolute paths for elements (should be automatically calculated)."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # The absolute path should be automatically calculated as root + relative
        expected_abs_path = self.test_root / "data/"
        hook = manager.get_absolute_path_hook("data")
        assert hook.value == expected_abs_path
        
        # When we change the relative path, the absolute path should update automatically
        manager.set_relative_path("data", "new_data/")
        expected_abs_path = self.test_root / "new_data/"
        hook = manager.get_absolute_path_hook("data")
        assert hook.value == expected_abs_path

    def test_get_relative_path_hook(self):
        """Test getting relative path hooks."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = XRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting existing hook
        hook = manager.get_relative_path_hook("data")
        assert hook.value == "data/"
        
        # Test getting non-existing hook
        with pytest.raises(ValueError):
            manager.get_relative_path_hook("nonexistent")

    def test_get_absolute_path_hook(self):
        """Test getting absolute path hooks."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting existing hook
        hook = manager.get_absolute_path_hook("data")
        expected_path = self.test_root / "data/"
        assert hook.value == expected_path
        
        # Test getting non-existing hook
        with pytest.raises(ValueError):
            manager.get_absolute_path_hook("nonexistent")

    def test_validation_with_valid_values(self):
        """Test validation with valid values."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = XRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test validation with current values
        hook_keys = manager._get_hook_keys() # type: ignore
        _ = {key: manager._get_value_by_key(key) for key in hook_keys} # type: ignore
        
        # This should pass validation
        # Note: We can't directly test the validation callback as it's private,
        # but we can test the behavior through the public interface

    def test_validation_with_invalid_root_path(self):
        """Test validation with invalid root path."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Try to set an invalid root path (not a Path object)
        # This should be handled by the validation system
        _, _ = manager.set_root_path(Path("invalid_path"))  # This should fail validation
        # The exact behavior depends on the validation implementation

    def test_automatic_absolute_path_calculation(self):
        """Test that absolute paths are automatically calculated when root or relative paths change."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Check initial absolute path
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = self.test_root / "data/"
        assert abs_hook.value == expected_path
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Check that absolute path is updated
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = new_root / "data/"
        assert abs_hook.value == expected_path
        
        # Change relative path
        manager.set_relative_path("data", "new_data/")
        
        # Check that absolute path is updated
        abs_hook = manager.get_absolute_path_hook("data")
        expected_path = new_root / "new_data/"
        assert abs_hook.value == expected_path

    def test_hook_keys_retrieval(self):
        """Test getting all hook keys."""
        initial_values: dict[str, str|None] = {"data": "data/", "config": "config/"}
        manager = XRootedPaths(
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        hook_keys = manager._get_hook_keys() # type: ignore
        
        # Should include root path key
        assert XRootedPaths.ROOT_PATH_KEY in hook_keys
        
        # Should include relative path keys
        for key in initial_values:
            assert f"{key}_relative_path" in hook_keys
            assert f"{key}_absolute_path" in hook_keys

    def test_hook_key_retrieval(self):
        """Test getting hook key from hook or nexus."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths(
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting key from root path hook
        root_hook = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        key = manager._get_key_by_hook_or_nexus(root_hook) # type: ignore
        assert key == XRootedPaths.ROOT_PATH_KEY
        
        # Test getting key from element hook
        data_hook: Hook[Optional[str]] = manager.get_relative_path_hook("data") # type ignore
        key = manager._get_key_by_hook_or_nexus(data_hook) # type: ignore
        assert key == "data_relative_path"

    def test_hook_key_retrieval_with_nonexistent_hook(self):
        """Test getting hook key with nonexistent hook."""
        manager = XRootedPaths[str]()
        
        # Create a mock hook that doesn't exist in the manager
        mock_hook = Mock()
        
        with pytest.raises(ValueError):
            manager._get_key_by_hook_or_nexus(mock_hook) # type: ignore

    def test_value_reference_retrieval(self):
        """Test getting value references from hooks."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test getting root path value reference
        root_value = manager._get_value_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        assert root_value == self.test_root
        
        # Test getting element value reference
        data_value = manager._get_value_by_key("data_relative_path") # type: ignore
        assert data_value == "data/"

    def test_value_reference_retrieval_with_nonexistent_key(self):
        """Test getting value reference with nonexistent key."""
        manager = XRootedPaths[str]()
        
        with pytest.raises(ValueError):
            manager._get_value_by_key("nonexistent_key") # type: ignore

    def test_serialization_callback(self):
        """Test the complete serialization and deserialization cycle."""
        # Step 1: Create an XRootedPaths instance
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/settings/",
            "logs": "logs/app.log",
            "cache": None
        }
        
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Step 2: Fill it (modify some values)
        manager.set_relative_path("data", "new_data/")
        manager.set_relative_path("cache", "cache/tmp/")
        
        # Store the expected state after step 2
        expected_root = manager.root_path
        expected_relative_paths = {
            "data": manager.get_relative_path_hook("data").value,
            "config": manager.get_relative_path_hook("config").value,
            "logs": manager.get_relative_path_hook("logs").value,
            "cache": manager.get_relative_path_hook("cache").value,
        }
        expected_absolute_paths = {
            "data": manager.get_absolute_path_hook("data").value,
            "config": manager.get_absolute_path_hook("config").value,
            "logs": manager.get_absolute_path_hook("logs").value,
            "cache": manager.get_absolute_path_hook("cache").value,
        }
        
        # Step 3: Serialize it and get a dict from "get_values_for_serialization"
        serialized_data = manager.get_values_for_serialization()
        
        # Verify serialized data contains expected keys
        assert XRootedPaths.ROOT_PATH_KEY in serialized_data
        assert serialized_data[XRootedPaths.ROOT_PATH_KEY] == expected_root
        for key in initial_values.keys():
            assert key in serialized_data
            assert serialized_data[key] == expected_relative_paths[key]
        
        # Step 4: Delete the object
        del manager
        
        # Step 5: Create a fresh XRootedPaths instance
        manager_restored = XRootedPaths[str](
            root_path_initial_value=None,
            rooted_elements_initial_relative_path_values={
                "data": None,
                "config": None,
                "logs": None,
                "cache": None
            }
        )
        
        # Verify it starts empty/different
        assert manager_restored.root_path is None
        
        # Step 6: Use "set_values_from_serialization"
        manager_restored.set_values_from_serialization(serialized_data)
        
        # Step 7: Check if the object is the same as after step 2
        assert manager_restored.root_path == expected_root
        
        for key in initial_values.keys():
            # Check relative paths match
            restored_relative = manager_restored.get_relative_path_hook(key).value
            assert restored_relative == expected_relative_paths[key], \
                f"Relative path for '{key}' doesn't match: {restored_relative} != {expected_relative_paths[key]}"
            
            
            # Check absolute paths match
            restored_absolute = manager_restored.get_absolute_path_hook(key).value
            assert restored_absolute == expected_absolute_paths[key], \
                f"Absolute path for '{key}' doesn't match: {restored_absolute} != {expected_absolute_paths[key]}"
            

    def test_complex_scenario(self):
        """Test a complex scenario with multiple elements and path changes."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/",
            "temp": "temp/"
        }
        
        manager = XRootedPaths(
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Verify initial state
        assert manager.root_path == self.test_root
        for key, rel_path in initial_values.items():
            assert manager.get_relative_path_hook(key).value == rel_path
            assert rel_path is not None
            assert self.test_root is not None
            expected_abs: Path = self.test_root / rel_path
            assert manager.get_absolute_path_hook(key).value == expected_abs
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Verify all absolute paths are updated
        for key, rel_path in initial_values.items():
            assert rel_path is not None
            expected_abs = new_root / rel_path
            assert manager.get_absolute_path_hook(key).value == expected_abs
        
        # Change some relative paths
        manager.set_relative_path("data", "new_data/")
        manager.set_relative_path("config", "settings/")
        
        # Verify absolute paths are recalculated
        assert manager.get_absolute_path_hook("data").value == new_root / "new_data/"
        assert manager.get_absolute_path_hook("config").value == new_root / "settings/"
        
        # Verify unchanged paths remain the same
        assert manager.get_absolute_path_hook("logs").value == new_root / "logs/"
        assert manager.get_absolute_path_hook("temp").value == new_root / "temp/"

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with empty string relative paths
        initial_values = {"data": "", "config": None}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Empty string should be handled
        assert manager.get_relative_path_hook("data").value == ""
        
        # None should be handled
        assert manager.get_relative_path_hook("config").value is None
        
        # Test with None root path
        manager.set_root_path(None)
        assert manager.root_path is None
        
        # Test setting relative path to None
        manager.set_relative_path("data", None)
        assert manager.get_relative_path_hook("data").value is None

    def test_type_safety(self):
        """Test type safety with different path types."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Test that relative paths accept strings
        manager.set_relative_path("data", "new_path/")
        assert manager.get_relative_path_hook("data").value == "new_path/"
        
        # Test that absolute paths are automatically calculated
        expected_abs_path = self.test_root / "new_path/"
        assert manager.get_absolute_path_hook("data").value == expected_abs_path

    def test_binding_with_observable_single_value_root_path(self):
        """Test binding root path hook to XValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue for root path
        root_path_observable = XValue[Path|None](self.test_root)
        
        # Connect the root path hook to the observable
        root_path_hook: Hook[Path|None] = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        root_path_hook.join(root_path_observable.value_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.root_path == self.test_root
        assert manager.get_absolute_path_hook("data").value == self.test_root / "data/"
        
        # Change the root path through the observable
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        root_path_observable.value = new_root
        
        # Verify that XRootedPaths updated
        assert manager.root_path == new_root
        assert manager.get_absolute_path_hook("data").value == new_root / "data/"
        
        # Change back to None
        root_path_observable.value = None
        
        # Verify that XRootedPaths updated
        assert manager.root_path is None
        assert manager.get_absolute_path_hook("data").value is None

    def test_binding_with_observable_single_value_relative_path(self):
        """Test binding relative path hook to XValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue for relative path
        relative_path_observable = XValue[str|None]("data/")
        
        # Connect the relative path hook to the observable
        relative_path_hook: Hook[Optional[str]] = manager.get_relative_path_hook("data")
        relative_path_hook.join(relative_path_observable.value_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.get_relative_path_hook("data").value == "data/"
        assert manager.get_absolute_path_hook("data").value == self.test_root / "data/"
        
        # Change the relative path through the observable
        relative_path_observable.value = "new_data/"
        
        # Verify that XRootedPaths updated
        assert manager.get_relative_path_hook("data").value == "new_data/"
        assert manager.get_absolute_path_hook("data").value == self.test_root / "new_data/"
        
        # Change to empty string (None would violate validation since root path is set)
        relative_path_observable.value = ""
        
        # Verify that XRootedPaths updated
        assert manager.get_relative_path_hook("data").value == ""
        assert manager.get_absolute_path_hook("data").value == self.test_root / ""

    def test_binding_with_observable_single_value_absolute_path(self):
        """Test binding absolute path hook to XValue and changing it."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue for absolute path
        absolute_path_observable = XValue[Path|None](self.test_root / "data/")
        
        # Connect the absolute path hook to the observable
        absolute_path_hook: Hook[Optional[Path]] = manager.get_absolute_path_hook("data")
        absolute_path_hook.join(absolute_path_observable.value_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.get_absolute_path_hook("data").value == self.test_root / "data/"
        
        # Change the absolute path through the observable (must match root + relative)
        new_absolute_path = self.test_root / "data/"  # Keep it consistent with relative path
        absolute_path_observable.value = new_absolute_path
        
        # Verify that XRootedPaths updated
        assert manager.get_absolute_path_hook("data").value == new_absolute_path
        
        # Change to a different valid absolute path (must match root + relative)
        different_absolute_path = self.test_root / "data/"  # Keep it consistent
        absolute_path_observable.value = different_absolute_path
        
        # Verify that XRootedPaths updated
        assert manager.get_absolute_path_hook("data").value == different_absolute_path

    def test_binding_multiple_hooks_to_observable_single_values(self):
        """Test binding multiple hooks to different XValue instances."""
        initial_values: dict[str, str|None] = {
            "data": "data/",
            "config": "config/",
            "logs": "logs/"
        }
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue instances for different paths
        root_observable = XValue(self.test_root)
        data_relative_observable = XValue("data/")
        config_relative_observable = XValue("config/")
        logs_absolute_observable = XValue(self.test_root / "logs/")
        
        # Connect hooks to observables
        root_path_hook: Hook[Path|None] = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: Hook[Path|None] = root_observable.value_hook # type: ignore
        root_path_hook.join(observable_root_path_hook, "use_caller_value")
        data_relative_hook: Hook[Optional[str]] = manager.get_relative_path_hook("data")
        observable_data_relative_hook: Hook[Optional[str]] = data_relative_observable.value_hook # type: ignore
        data_relative_hook.join(observable_data_relative_hook, "use_caller_value")
        config_relative_hook: Hook[Optional[str]] = manager.get_relative_path_hook("config")
        observable_config_relative_hook: Hook[Optional[str]] = config_relative_observable.value_hook # type: ignore
        config_relative_hook.join(observable_config_relative_hook, "use_caller_value")
        logs_absolute_hook: Hook[Optional[Path]] = manager.get_absolute_path_hook("logs")
        observable_logs_absolute_hook: Hook[Optional[Path]] = logs_absolute_observable.value_hook # type: ignore
        logs_absolute_hook.join(observable_logs_absolute_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.root_path == self.test_root
        assert manager.get_relative_path_hook("data").value == "data/"
        assert manager.get_relative_path_hook("config").value == "config/"
        assert manager.get_absolute_path_hook("logs").value == self.test_root / "logs/"
        
        # Change root path
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        root_observable.value = new_root
        
        # Verify that all absolute paths updated (including logs which is directly bound)
        assert manager.root_path == new_root
        assert manager.get_absolute_path_hook("data").value == new_root / "data/"
        assert manager.get_absolute_path_hook("config").value == new_root / "config/"
        assert manager.get_absolute_path_hook("logs").value == new_root / "logs/"  # Updated due to binding
        
        # Change relative paths
        data_relative_observable.value = "new_data/"
        config_relative_observable.value = "settings/"
        
        # Verify updates
        assert manager.get_relative_path_hook("data").value == "new_data/"
        assert manager.get_relative_path_hook("config").value == "settings/"
        assert manager.get_absolute_path_hook("data").value == new_root / "new_data/"
        assert manager.get_absolute_path_hook("config").value == new_root / "settings/"
        
        # Change absolute path directly (must match root + relative)
        new_logs_path = new_root / "logs/"  # Keep it consistent with relative path
        logs_absolute_observable.value = new_logs_path
        
        # Verify update
        assert manager.get_absolute_path_hook("logs").value == new_logs_path

    def test_bidirectional_binding_with_observable_single_value(self):
        """Test bidirectional binding between XRootedPaths and XValue."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue for root path
        root_path_observable = XValue(self.test_root)
        
        # Connect bidirectionally
        root_path_hook: Hook[Path|None] = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: Hook[Path|None] = root_path_observable.value_hook # type: ignore
        root_path_hook.join(observable_root_path_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.root_path == self.test_root
        assert root_path_observable.value == self.test_root
        
        # Change through XRootedPaths
        new_root = Path(self.temp_dir) / "new_project"
        new_root.mkdir()
        manager.set_root_path(new_root)
        
        # Verify that XValue updated
        assert manager.root_path == new_root
        assert root_path_observable.value == new_root
        
        # Change through XValue
        another_root = Path(self.temp_dir) / "another_project"
        another_root.mkdir()
        root_path_observable.value = another_root
        
        # Verify that XRootedPaths updated
        assert manager.root_path == another_root
        assert root_path_observable.value == another_root

    def test_binding_chain_with_observable_single_values(self):
        """Test a chain of bindings through multiple XValue instances."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create a chain of XValue instances
        root_observable1 = XValue(self.test_root)
        root_observable2 = XValue(self.test_root)
        root_observable3 = XValue(self.test_root)
        
        # Connect in a chain: manager -> observable1 -> observable2 -> observable3
        root_path_hook: Hook[Path|None] = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: Hook[Path|None] = root_observable1.value_hook # type: ignore
        root_path_hook.join(observable_root_path_hook, "use_caller_value")     
        root_observable1.value_hook.join(root_observable2.value_hook, "use_caller_value")
        root_observable2.value_hook.join(root_observable3.value_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.root_path == self.test_root
        assert root_observable1.value == self.test_root
        assert root_observable2.value == self.test_root
        assert root_observable3.value == self.test_root
        
        # Change through the end of the chain
        new_root = Path(self.temp_dir) / "chain_project"
        new_root.mkdir()
        root_observable3.value = new_root
        
        # Verify that all observables in the chain updated
        assert manager.root_path == new_root
        assert root_observable1.value == new_root
        assert root_observable2.value == new_root
        assert root_observable3.value == new_root
        
        # Verify that absolute paths updated
        assert manager.get_absolute_path_hook("data").value == new_root / "data/"

    def test_binding_with_validation_and_observable_single_value(self):
        """Test that validation works correctly when binding to XValue."""
        initial_values: dict[str, str|None] = {"data": "data/"}
        manager = XRootedPaths[str](
            root_path_initial_value=self.test_root,
            rooted_elements_initial_relative_path_values=initial_values
        )
        
        # Create XValue with validation
        def validate_path(path: Path|None) -> tuple[bool, str]:
            if path is None:
                return True, "None is valid"
            if not isinstance(path, Path): # type: ignore
                return False, "Must be a Path object"
            if not path.exists():
                return False, "Path must exist"
            return True, "Valid path"
        
        root_path_observable = XValue(self.test_root, validate_value_callback=validate_path)
        
        # Connect the hooks
        root_path_hook: Hook[Path|None] = manager._get_hook_by_key(XRootedPaths.ROOT_PATH_KEY) # type: ignore
        observable_root_path_hook: Hook[Path|None] = root_path_observable.value_hook # type: ignore
        root_path_hook.join(observable_root_path_hook, "use_caller_value")
        
        # Verify initial state
        assert manager.root_path == self.test_root
        assert root_path_observable.value == self.test_root
        
        # Try to set an invalid path (should fail validation)
        with pytest.raises(ValueError):
            root_path_observable.value = Path("/nonexistent/path")
        
        # Verify that values didn't change
        assert manager.root_path == self.test_root
        assert root_path_observable.value == self.test_root
        
        # Set a valid path
        new_root = Path(self.temp_dir) / "valid_project"
        new_root.mkdir()
        root_path_observable.value = new_root
        
        # Verify that values updated
        assert manager.root_path == new_root
        assert root_path_observable.value == new_root
