#!/usr/bin/env python3
"""
Test runner for the observables library.
"""

import sys
import os
import logging
from pathlib import Path

# Set up console logging for all tests
def setup_logging():
    """Set up console logging configuration."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# Create a global logger instance that tests can import
console_logger = setup_logging()

def main():
    """Run the test suite using pytest."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Add project root to Python path so tests can import observables
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change to project root
    os.chdir(project_root)
    
    print("Running observables test suite with pytest...")
    print(f"Project root: {project_root}")
    print()
    
    try:
        import pytest
        
        # Run pytest with the tests directory
        test_dir = Path(__file__).parent
        exit_code = pytest.main([
            str(test_dir),
            "-v",                    # Verbose output
            "--tb=short",            # Shorter traceback format
            "--color=yes",           # Colored output
            "-ra",                   # Show summary of all test outcomes
        ])
        
        if exit_code == 0:
            print("\n✅ All tests passed!")
            return 0
        else:
            print(f"\n❌ Tests failed with exit code: {exit_code}")
            return exit_code
            
    except ImportError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
