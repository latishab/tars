"""
Camera module for TARS Control System V3
Supports both Pi Camera (via picamera2) and USB webcams (via OpenCV)
"""

import numpy as np
import time

class CameraModule:
    def __init__(self, width=1280, height=720):
        """
        Initialize camera module
        Tries Pi Camera first, falls back to USB webcam

        Args:
            width: Frame width (default 1280)
            height: Frame height (default 720)
        """
        self.width = width
        self.height = height
        self.camera = None
        self.camera_type = None

        # Try Pi Camera first
        try:
            from picamera2 import Picamera2
            print("Attempting to initialize Pi Camera...")
            self.camera = Picamera2()
            config = self.camera.create_still_configuration(
                main={"size": (width, height), "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()
            time.sleep(2)  # Allow camera to warm up
            self.camera_type = "picamera2"
            print("✓ Pi Camera initialized successfully")
            return
        except Exception as e:
            print(f"Pi Camera not available: {e}")

        # Fall back to USB webcam
        try:
            import cv2
            print("Attempting to initialize USB webcam...")
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Could not open USB webcam")

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera_type = "opencv"
            print("✓ USB webcam initialized successfully")
            return
        except Exception as e:
            print(f"USB webcam not available: {e}")

        # No camera available
        self.camera = None
        self.camera_type = None
        print("⚠ No camera available")

    def capture_frame(self):
        """
        Capture a single frame from the camera

        Returns:
            numpy.ndarray: Frame in RGB format, or None if capture fails
        """
        if self.camera is None:
            return None

        try:
            if self.camera_type == "picamera2":
                # Pi Camera - capture returns RGB
                frame = self.camera.capture_array()
                return frame

            elif self.camera_type == "opencv":
                # USB webcam - read returns BGR, convert to RGB
                import cv2
                ret, frame = self.camera.read()
                if not ret:
                    return None
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame

        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None

    def close(self):
        """Clean up camera resources"""
        if self.camera is None:
            return

        try:
            if self.camera_type == "picamera2":
                self.camera.stop()
                self.camera.close()
            elif self.camera_type == "opencv":
                self.camera.release()
            print("Camera closed successfully")
        except Exception as e:
            print(f"Error closing camera: {e}")

    def is_available(self):
        """Check if camera is available"""
        return self.camera is not None

    def get_camera_type(self):
        """Get the type of camera being used"""
        return self.camera_type
