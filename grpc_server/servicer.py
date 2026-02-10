"""
gRPC Servicer implementation for TARS robot.
Maps gRPC methods to hardware modules.
"""

import time
import io
import asyncio
from typing import Optional

import grpc
from loguru import logger

# Import proto files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tars_sdk.proto import tars_pb2, tars_pb2_grpc

# Import existing modules
from src.modules import module_movements
from src.modules import module_servoctl
from src.modules import module_movement_registry


# Movement mapping
MOVEMENT_MAP = {
    "step_forward": module_movements.step_forward,
    "walk_forward": module_movements.walk_forward,
    "step_backward": module_movements.step_backward,
    "walk_backward": module_movements.walk_backward,
    "turn_right": module_movements.turn_right,
    "turn_right_slow": module_movements.turn_right_slow,
    "turn_left": module_movements.turn_left,
    "turn_left_slow": module_movements.turn_left_slow,
    "pose": module_movements.pose,
    "bow": module_movements.bow,
    "tilt_right": module_movements.tilt_right,
    "tilt_left": module_movements.tilt_left,
    "side_side": module_movements.side_side,
    "wave_right": module_movements.wave_right,
    "wave_left": module_movements.wave_left,
    "neutral_legs": module_movements.neutral_legs,
    "excited": module_movements.excited,
    "laugh": module_movements.laugh,
    "swing_legs": module_movements.swing_legs,
}


class TarsServiceServicer(tars_pb2_grpc.TarsServiceServicer):
    """Implementation of TARS gRPC service."""

    def __init__(
        self,
        camera=None,
        display=None,
        battery=None,
        audio=None,
        webrtc=None
    ):
        """
        Initialize servicer with module references.

        Args:
            camera: CameraModule instance
            display: DisplayManager instance
            battery: BatteryModule instance
            audio: AudioModule instance
            webrtc: WebRTCServer instance
        """
        self.camera = camera
        self.display = display
        self.battery = battery
        self.audio = audio
        self.webrtc = webrtc

        logger.info("TarsServiceServicer initialized")

    def Health(self, request, context):
        """Get health status."""
        logger.debug("gRPC Health")

        try:
            # Hardware status
            hardware = tars_pb2.HardwareStatus(
                servos=True,
                camera=self.camera is not None,
                audio=self.audio is not None,
                display=self.display is not None,
                battery=self.battery is not None,
                moving=module_servoctl.MOVING
            )

            # Battery status
            battery_status = tars_pb2.BatteryStatus(
                level=0,
                charging=False,
                voltage=0.0,
                current=0.0
            )

            if self.battery is not None:
                battery_status.level = int(self.battery.normalized_percentage)
                battery_status.charging = self.battery.charging_state == "CHARGING"
                battery_status.voltage = self.battery.voltage
                battery_status.current = self.battery.current

            return tars_pb2.HealthResponse(
                status="running",
                version="3.0.0",
                grpc_available=True,
                webrtc_available=self.webrtc is not None,
                webrtc_connected=self.webrtc.is_connected if self.webrtc else False,
                hardware=hardware,
                battery=battery_status
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.HealthResponse(status="error", version="3.0.0")

    def Move(self, request, context):
        """Execute a movement."""
        movement = request.movement
        speed = request.speed if request.speed > 0 else 1.0

        logger.info(f"gRPC Move: {movement} (speed={speed})")

        # Check if movement exists
        if movement not in MOVEMENT_MAP:
            error_msg = f"Unknown movement: {movement}"
            logger.error(error_msg)
            return tars_pb2.MoveResponse(
                success=False,
                duration=0.0,
                error=error_msg
            )

        # Execute movement
        try:
            start_time = time.time()

            # Get movement function
            movement_func = MOVEMENT_MAP[movement]

            # Execute
            movement_func()

            duration = time.time() - start_time

            logger.info(f"Movement '{movement}' completed in {duration:.2f}s")

            return tars_pb2.MoveResponse(
                success=True,
                duration=duration,
                error=""
            )

        except Exception as e:
            error_msg = f"Movement failed: {str(e)}"
            logger.error(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(error_msg)
            return tars_pb2.MoveResponse(
                success=False,
                duration=0.0,
                error=error_msg
            )

    def SetEmotion(self, request, context):
        """Set facial emotion."""
        emotion = request.emotion

        logger.info(f"gRPC SetEmotion: {emotion}")

        if self.display is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Display not available")
            return tars_pb2.Empty()

        try:
            self.display.set_emotion(emotion)
            return tars_pb2.Empty()

        except Exception as e:
            logger.error(f"SetEmotion failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.Empty()

    def SetEyeState(self, request, context):
        """Set eye state."""
        state = request.state

        logger.info(f"gRPC SetEyeState: {state}")

        if self.display is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Display not available")
            return tars_pb2.Empty()

        try:
            self.display.set_eye_state(state)
            return tars_pb2.Empty()

        except Exception as e:
            logger.error(f"SetEyeState failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.Empty()

    def CaptureCamera(self, request, context):
        """Capture a camera frame."""
        width = request.width if request.width > 0 else 640
        height = request.height if request.height > 0 else 480
        quality = request.quality if request.quality > 0 else 80

        logger.info(f"gRPC CaptureCamera: {width}x{height} q={quality}")

        if self.camera is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Camera not available")
            return tars_pb2.CaptureResponse()

        try:
            # Capture frame
            frame = self.camera.capture_frame()

            if frame is None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to capture frame")
                return tars_pb2.CaptureResponse()

            # Resize if needed
            import cv2
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))

            # Encode as JPEG
            success, buffer = cv2.imencode(
                '.jpg',
                cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, quality]
            )

            if not success:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details("Failed to encode image")
                return tars_pb2.CaptureResponse()

            jpeg_bytes = buffer.tobytes()

            logger.info(f"Captured frame: {width}x{height}, {len(jpeg_bytes)} bytes")

            return tars_pb2.CaptureResponse(
                image=jpeg_bytes,
                width=width,
                height=height,
                format="jpeg"
            )

        except Exception as e:
            logger.error(f"CaptureCamera failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.CaptureResponse()

    def GetStatus(self, request, context):
        """Get robot status."""
        logger.debug("gRPC GetStatus")

        try:
            # Battery status
            battery_status = tars_pb2.BatteryStatus(
                level=0,
                charging=False,
                voltage=0.0,
                current=0.0
            )

            if self.battery is not None:
                battery_status.level = int(self.battery.normalized_percentage)
                battery_status.charging = self.battery.charging_state == "CHARGING"
                battery_status.voltage = self.battery.voltage
                battery_status.current = self.battery.current

            # Display status
            current_emotion = "default"
            current_eye_state = "idle"

            if self.display is not None:
                current_emotion = self.display.state.emotion
                current_eye_state = self.display.state.eye_state

            # Movement status
            is_moving = module_servoctl.MOVING
            current_movement = ""

            return tars_pb2.StatusResponse(
                connected=True,
                battery=battery_status,
                current_emotion=current_emotion,
                current_eye_state=current_eye_state,
                is_moving=is_moving,
                current_movement=current_movement
            )

        except Exception as e:
            logger.error(f"GetStatus failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.StatusResponse(connected=False)

    def Reset(self, request, context):
        """Reset robot to neutral position."""
        logger.info("gRPC Reset")

        try:
            module_servoctl.reset_positions()
            return tars_pb2.Empty()

        except Exception as e:
            logger.error(f"Reset failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.Empty()

    def StreamBattery(self, request, context):
        """Stream battery status updates."""
        logger.info("gRPC StreamBattery started")

        try:
            while context.is_active():
                # Get battery status
                if self.battery is not None:
                    status = tars_pb2.BatteryStatus(
                        level=int(self.battery.normalized_percentage),
                        charging=self.battery.charging_state == "CHARGING",
                        voltage=self.battery.voltage,
                        current=self.battery.current
                    )
                else:
                    status = tars_pb2.BatteryStatus(
                        level=0,
                        charging=False,
                        voltage=0.0,
                        current=0.0
                    )

                yield status

                # Wait 2 seconds before next update
                time.sleep(2.0)

        except Exception as e:
            logger.error(f"StreamBattery failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

    def StreamMovementStatus(self, request, context):
        """Stream movement status updates."""
        logger.info("gRPC StreamMovementStatus started")

        try:
            while context.is_active():
                # Get movement status
                is_moving = module_servoctl.MOVING

                status = tars_pb2.MovementStatus(
                    moving=is_moving,
                    movement="",  # Could track current movement if needed
                    progress=0.0   # Could track progress if needed
                )

                yield status

                # Wait 100ms before next update
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"StreamMovementStatus failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

    def StreamAudioLevels(self, request_iterator, context):
        """Bidirectional streaming for audio levels (future use)."""
        logger.info("gRPC StreamAudioLevels started")

        try:
            for request in request_iterator:
                level = request.level
                # Process audio level (e.g., update display animation)
                if self.display is not None:
                    self.display.set_audio_level(level, "grpc")

                # Send acknowledgment
                yield tars_pb2.AudioLevelResponse(received=True)

        except Exception as e:
            logger.error(f"StreamAudioLevels failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
