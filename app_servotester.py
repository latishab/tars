#!/usr/bin/env python3
"""
TARS Servo Tester CLI Entry Point
Wrapper for src/app-servotester.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Main entry point for tars-servo-tester command."""
    # Import the actual servo tester
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "app_servotester",
            Path(__file__).parent / "src" / "app-servotester.py"
        )
        module = importlib.util.module_from_spec(spec)

        # Execute the module (which will run the if __name__ == "__main__" block)
        spec.loader.exec_module(module)

    except ImportError as e:
        print(f"Error: Could not import servo tester: {e}")
        print("\nMake sure you're running this on a Raspberry Pi with:")
        print("  - pygame installed")
        print("  - PCA9685 hardware connected")
        print("  - Adafruit libraries installed")
        sys.exit(1)
    except Exception as e:
        print(f"Error running servo tester: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
