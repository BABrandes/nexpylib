#!/usr/bin/env python3
"""
Basic usage demonstration of NexPy.

This script shows the fundamental features and usage patterns of the NexPy library.
"""

import sys
import os

# Add the src directory to the path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import nexpy

def main():
    """Main demonstration function."""
    print("NexPy Basic Usage Demo")
    print("=" * 40)
    
    # Example 1: Basic functionality
    print("\n1. Basic functionality:")
    print(f"NexPy version: {nexpy.__version__}")
    print(f"Author: {nexpy.__author__}")
    
    # Example 2: Placeholder for future features
    print("\n2. Future features will be demonstrated here:")
    print("   - Data processing")
    print("   - Analysis tools")
    print("   - Visualization utilities")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
