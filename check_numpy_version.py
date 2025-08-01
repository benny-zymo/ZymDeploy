"""
Simple script to check if NumPy is installed correctly and print its version.
This can be used to verify that the installation process is working properly.
"""
import sys

try:
    import numpy as np
    print(f"NumPy is installed successfully!")
    print(f"NumPy version: {np.__version__}")
    print(f"NumPy installation path: {np.__file__}")
    # Check if the version matches what we expect
    if np.__version__ != "1.26.3":
        print(f"Warning: NumPy version {np.__version__} is installed, but version 1.26.3 was specified in requirements.txt")
        # This is just a warning, not an error
except ImportError as e:
    print(f"Error importing NumPy: {e}")
    print("NumPy is not installed correctly.")
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)  # Exit with error code
except Exception as e:
    print(f"Unexpected error: {e}")
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)  # Exit with error code

print("\nNumPy verification completed successfully.")
print("Press Enter to continue...")
input()
