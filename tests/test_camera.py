#!/usr/bin/env python3
"""
Test script for camera module
Tests both Pi Camera and USB webcam fallback
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
cv2 = pytest.importorskip("cv2", reason="OpenCV not installed")
from modules.module_camera import CameraModule

def test_camera():
    print("="*50)
    print("Testing TARS Camera Module")
    print("="*50)

    # Initialize camera
    print("\n1. Initializing camera...")
    camera = CameraModule(1280, 720)

    if not camera.is_available():
        print("❌ No camera available")
        return False

    print(f"✓ Camera initialized: {camera.get_camera_type()}")

    # Capture a frame
    print("\n2. Capturing frame...")
    frame = camera.capture_frame()

    if frame is None:
        print("❌ Failed to capture frame")
        camera.close()
        return False

    print(f"✓ Frame captured: {frame.shape} (RGB)")

    # Convert to BGR and save
    print("\n3. Saving test image...")
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite("test_frame.jpg", frame_bgr)
    print("✓ Image saved as test_frame.jpg")

    # Capture a few more frames
    print("\n4. Testing multiple captures...")
    for i in range(5):
        frame = camera.capture_frame()
        if frame is None:
            print(f"❌ Failed to capture frame {i+1}")
            camera.close()
            return False
        print(f"✓ Frame {i+1}: {frame.shape}")

    # Close camera
    print("\n5. Closing camera...")
    camera.close()
    print("✓ Camera closed")

    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_camera()
    sys.exit(0 if success else 1)
