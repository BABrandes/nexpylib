"""
Base test class for observables tests that handles global state reset.
"""

from nexpy.core import DEFAULT_NEXUS_MANAGER
from nexpy.core.nexus_system.nexus_manager import NexusManager


class ObservableTestCase:
    """Base test case that resets global state between tests."""
    
    def setup_method(self):
        """Reset global state before each test (pytest style)."""
        DEFAULT_NEXUS_MANAGER.reset()
        # Create a fresh NexusManager for tests that need custom equality
        self.test_manager = NexusManager()
