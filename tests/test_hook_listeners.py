from unittest.mock import Mock
from typing import Any

from nexpy import Hook
from nexpy import XBase
from nexpy.core import ListenableProtocol

from nexpy.core.hooks.implementations.owned_read_only_hook import OwnedReadOnlyHook as OwnedHook
from nexpy.core.nexus_system.nexus import Nexus


class MockCarriesHooks(XBase[Any, Any]):
    """Mock class that implements CarriesHooks interface for testing."""
    
    def __init__(self, name: str = "MockOwner"):
        super().__init__()
        self.name = name
        self._hooks: dict[str, Hook[Any]] = {}
    
    def is_valid_hook_value(self, hook_key: Any, value: Any) -> tuple[bool, str]:
        return True, "Valid"
    
    def _get_key_by_hook_or_nexus(self, hook_or_nexus: Hook[Any]|Nexus[Any]) -> Any:
        """Return a mock key for the hook."""
        return "mock_key"
    
    def _get_hook_keys(self) -> set[Any]:
        """Return a set of mock keys."""
        return {"mock_key"}
    
    def _get_hook_by_key(self, key: Any) -> Any:
        """Return a mock hook."""
        # Return a mock hook that won't cause issues in the nexus manager
        if key not in self._hooks:
            self._hooks[key] = OwnedHook(self, "mock_value")
        return self._hooks[key]
    
    def _get_value_by_key(self, key: Any) -> Any:
        """Return a mock value."""
        return "mock_value"

class TestHookListeners:
    """Test the listener functionality of the Hook class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.owner = MockCarriesHooks("TestOwner") # type: ignore
        # Create a mock invalidate callback for testing
        self.invalidate_callback = Mock()
        self.hook = OwnedHook(self.owner, "initial_value", self.invalidate_callback)
    
    def test_hook_inherits_from_base_listening(self):
        """Test that Hook inherits from ListeneingProtocol."""
        assert isinstance(self.hook, ListenableProtocol)
    
    def test_initial_listeners_state(self):
        """Test initial state of listeners."""
        assert len(self.hook.listeners) == 0
        assert not self.hook.is_listening_to(lambda: None)
    
    def test_add_single_listener(self):
        """Test adding a single listener."""
        callback = Mock()
        self.hook.add_listener(callback)
        
        assert len(self.hook.listeners) == 1
        assert self.hook.is_listening_to(callback)
        assert callback in self.hook.listeners
    
    def test_add_multiple_listeners(self):
        """Test adding multiple listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listener(callback1, callback2, callback3)
        
        assert len(self.hook.listeners) == 3
        assert self.hook.is_listening_to(callback1)
        assert self.hook.is_listening_to(callback2)
        assert self.hook.is_listening_to(callback3)
    
    def test_add_duplicate_listener_prevention(self):
        """Test that duplicate listeners are prevented."""
        callback = Mock()
        
        # Add the same callback multiple times
        self.hook.add_listener(callback)
        self.hook.add_listener(callback)
        self.hook.add_listener(callback)
        
        # Should only be added once
        assert len(self.hook.listeners) == 1
        assert self.hook.is_listening_to(callback)
    
    def test_remove_single_listener(self):
        """Test removing a single listener."""
        callback = Mock()
        self.hook.add_listener(callback)
        
        # Verify listener was added
        assert len(self.hook.listeners) == 1
        
        # Remove listener
        self.hook.remove_listener(callback)
        
        # Verify listener was removed
        assert len(self.hook.listeners) == 0
        assert not self.hook.is_listening_to(callback)
    
    def test_remove_multiple_listeners(self):
        """Test removing multiple listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listener(callback1, callback2, callback3)
        assert len(self.hook.listeners) == 3
        
        # Remove two listeners
        self.hook.remove_listener(callback1, callback3)
        
        # Verify only callback2 remains
        assert len(self.hook.listeners) == 1
        assert not self.hook.is_listening_to(callback1)
        assert self.hook.is_listening_to(callback2)
        assert not self.hook.is_listening_to(callback3)
    
    def test_remove_nonexistent_listener_safe(self):
        """Test that removing non-existent listeners is safe."""
        callback = Mock()
        
        # Try to remove a listener that was never added
        self.hook.remove_listener(callback)
        
        # Should not raise an error
        assert len(self.hook.listeners) == 0
    
    def test_remove_all_listeners(self):
        """Test removing all listeners at once."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        self.hook.add_listener(callback1, callback2, callback3)
        assert len(self.hook.listeners) == 3
        
        # Remove all listeners
        removed = self.hook.remove_all_listeners()
        
        # Verify all listeners were removed
        assert len(self.hook.listeners) == 0
        assert len(removed) == 3
        assert callback1 in removed
        assert callback2 in removed
        assert callback3 in removed
    
    
    def test_listeners_copy_is_returned(self):
        """Test that listeners property returns a copy, not the original set."""
        callback = Mock()
        self.hook.add_listener(callback)
        
        listeners_copy = self.hook.listeners
        
        # Modify the copy
        listeners_copy.add(Mock())
        
        # Original hook listeners should be unchanged
        assert len(self.hook.listeners) == 1
        assert len(listeners_copy) != len(self.hook.listeners)
    
    def test_listener_notification_order(self):
        """Test that listeners are notified when called."""
        notifications: list[str] = []
        
        def make_callback(name: str):
            def callback():
                notifications.append(name)
            return callback
        
        callback1 = make_callback("first")
        callback2 = make_callback("second")
        callback3 = make_callback("third")
        
        self.hook.add_listener(callback1, callback2, callback3)
        
        # Trigger notification
        self.hook._notify_listeners() # type: ignore
        
        # Verify all listeners were called (order doesn't matter for sets)
        assert len(notifications) == 3
        assert "first" in notifications
        assert "second" in notifications
        assert "third" in notifications
    
    def test_listener_removal_during_notification(self):
        """Test that removing listeners during notification doesn't break the system."""
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()
        
        # callback2 will remove itself when called
        def self_removing_callback():
            self.hook.remove_listener(callback2)
        
        callback2.side_effect = self_removing_callback
        
        self.hook.add_listener(callback1, callback2, callback3)
        
        # Trigger notification - should not raise RuntimeError
        self.hook._notify_listeners() # type: ignore
        
        # Verify all callbacks were called
        callback1.assert_called_once()
        callback2.assert_called_once()
        callback3.assert_called_once()
        
        # Verify callback2 was removed
        assert not self.hook.is_listening_to(callback2)
        assert self.hook.is_listening_to(callback1)
        assert self.hook.is_listening_to(callback3)
    
    def test_multiple_hooks_independent_listeners(self):
        """Test that different hooks have independent listener sets."""
        owner1: XBase[str, Any, "MockCarriesHooks"] = MockCarriesHooks("Owner1") # type: ignore
        owner2: XBase[str, Any, "MockCarriesHooks"] = MockCarriesHooks("Owner2") # type: ignore
        
        hook1 = OwnedHook(owner1, "value1")
        hook2 = OwnedHook(owner2, "value2")
        
        callback1 = Mock()
        callback2 = Mock()
        
        hook1.add_listener(callback1)
        hook2.add_listener(callback2)
        
        # Verify each hook has its own listeners
        assert len(hook1.listeners) == 1
        assert len(hook2.listeners) == 1
        assert hook1.is_listening_to(callback1)
        assert hook2.is_listening_to(callback2)
        assert not hook1.is_listening_to(callback2)
        assert not hook2.is_listening_to(callback1)
        
        # Trigger notification on hook1
        hook1._notify_listeners() # type: ignore
        
        # Only callback1 should be called
        callback1.assert_called_once()
        callback2.assert_not_called()
    
