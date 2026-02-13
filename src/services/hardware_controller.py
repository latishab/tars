"""
Hardware controller with shared business logic.
Both HTTP and gRPC APIs call these internal functions.
"""

from typing import Optional, Dict, Any
from loguru import logger

# Valid values
VALID_EMOTIONS = ['neutral', 'happy', 'sad', 'angry', 'excited', 'skeptical', 'shy', 'love', 'fear', 'bored', 'disgust', 'worried', 'curious', 'sleepy', 'focused', 'playful']
VALID_EYE_STATES = ["idle", "listening", "thinking", "speaking"]


class HardwareController:
    """Shared hardware control logic for both HTTP and gRPC APIs."""
    
    def __init__(
        self,
        display=None,
        camera=None,
        battery=None,
        audio=None,
        webrtc=None,
        movement_map=None,
        servo_module=None
    ):
        self.display = display
        self.camera = camera
        self.battery = battery
        self.audio = audio
        self.webrtc = webrtc
        self.movement_map = movement_map or {}
        self.servo_module = servo_module
    
    # === Display Control ===
    
    def set_emotion(self, emotion: str) -> Dict[str, Any]:
        """Set display emotion."""
        if not self.display:
            raise ValueError("Display not available")
        
        if emotion not in VALID_EMOTIONS:
            raise ValueError(f"Invalid emotion. Valid: {', '.join(VALID_EMOTIONS)}")
        
        self.display.set_emotion(emotion)
        logger.info(f"Set emotion: {emotion}")
        return {"success": True, "emotion": emotion}
    
    def set_eye_state(self, state: str) -> Dict[str, Any]:
        """Set eye state."""
        if not self.display:
            raise ValueError("Display not available")
        
        if state not in VALID_EYE_STATES:
            raise ValueError(f"Invalid state. Valid: {', '.join(VALID_EYE_STATES)}")
        
        self.display.set_eye_state(state)
        logger.info(f"Set eye state: {state}")
        return {"success": True, "state": state}
    
    # === Status ===
    
    def get_battery_status(self) -> Dict[str, Any]:
        """Get battery status."""
        if not self.battery:
            return {
                "level": 0,
                "charging": False,
                "voltage": 0.0,
                "current": 0.0
            }
        
        return {
            "level": int(self.battery.normalized_percentage),
            "charging": self.battery.charging_state == "CHARGING",
            "voltage": self.battery.voltage,
            "current": self.battery.current
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get full robot status."""
        battery_status = self.get_battery_status()
        
        current_emotion = "default"
        current_eye_state = "idle"
        if self.display:
            current_emotion = self.display.state.emotion
            current_eye_state = self.display.state.eye_state
        
        is_moving = False
        if self.servo_module:
            is_moving = self.servo_module.MOVING
        
        return {
            "connected": True,
            "battery": battery_status,
            "current_emotion": current_emotion,
            "current_eye_state": current_eye_state,
            "is_moving": is_moving,
            "current_movement": ""
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get health check status."""
        is_moving = False
        if self.servo_module:
            is_moving = self.servo_module.MOVING
        
        return {
            "hardware": {
                "servos": True,
                "camera": self.camera is not None,
                "audio": self.audio is not None,
                "display": self.display is not None,
                "battery": self.battery is not None,
                "moving": is_moving
            },
            "battery": self.get_battery_status(),
            "webrtc": {
                "available": self.webrtc is not None,
                "connected": self.webrtc.is_connected if self.webrtc else False
            }
        }
    
    # === Movement ===
    
    def execute_movement(self, movement: str, speed: float = 1.0) -> Dict[str, Any]:
        """Execute a movement."""
        if movement not in self.movement_map:
            raise ValueError(f"Unknown movement: {movement}")
        
        import time
        start_time = time.time()
        
        movement_func = self.movement_map[movement]
        movement_func()
        
        duration = time.time() - start_time
        logger.info(f"Movement '{movement}' completed in {duration:.2f}s")
        
        return {
            "success": True,
            "duration": duration,
            "movement": movement
        }
    
    def reset_position(self):
        """Reset robot to neutral position."""
        if not self.servo_module:
            raise ValueError("Servo module not available")
        
        self.servo_module.reset_positions()
        logger.info("Reset to neutral position")
    
    # === Camera ===
    
    def capture_camera(
        self,
        width: int = 640,
        height: int = 480,
        quality: int = 80
    ) -> Dict[str, Any]:
        """Capture camera frame and return JPEG bytes."""
        if not self.camera:
            raise ValueError("Camera not available")
        
        frame = self.camera.capture_frame()
        if frame is None:
            raise ValueError("Failed to capture frame")
        
        import cv2
        
        # Resize if needed
        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height))
        
        # Encode as JPEG
        success, buffer = cv2.imencode(
            '.jpg',
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        
        if not success:
            raise ValueError("Failed to encode image")
        
        jpeg_bytes = buffer.tobytes()
        
        logger.info(f"Captured frame: {width}x{height}, {len(jpeg_bytes)} bytes")
        
        return {
            "image": jpeg_bytes,
            "width": width,
            "height": height,
            "format": "jpeg"
        }
