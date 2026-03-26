"""
gRPC Servicer implementation for TARS robot.
Maps gRPC methods to hardware modules.
"""

import time
import io
import asyncio
import platform
from typing import Optional

import grpc
from loguru import logger

# Import proto files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tars_sdk.proto import tars_pb2, tars_pb2_grpc
from tars_sdk._version import __version__, __minimum_compatible_client__
from grpc_server.version_service import (
    get_git_commit,
    get_build_date,
    check_for_update,
)

# Import existing modules
from src.modules import module_servoctl


class TarsServiceServicer(tars_pb2_grpc.TarsServiceServicer):
    """Implementation of TARS gRPC service."""

    def __init__(
        self,
        hardware_controller=None,
        camera=None,
        display=None,
        battery=None,
        audio=None,
        webrtc=None
    ):
        """
        Initialize servicer with hardware controller.

        Args:
            hardware_controller: HardwareController instance (preferred)
            camera: CameraModule instance (legacy)
            display: DisplayManager instance (legacy)
            battery: BatteryModule instance (legacy)
            audio: AudioModule instance (legacy)
            webrtc: WebRTCServer instance
        """
        self.hw = hardware_controller
        self.camera = camera
        self.display = display
        self.battery = battery
        self.audio = audio
        self.webrtc = webrtc
        self._build_date = get_build_date()

        logger.info("TarsServiceServicer initialized")

    def GetVersion(self, request, context):
        """Get version information."""
        logger.debug("gRPC GetVersion")

        try:
            return tars_pb2.VersionResponse(
                version=__version__,
                git_commit=get_git_commit() or "",
                build_date=self._build_date,
                python_version=platform.python_version(),
                platform=platform.platform(),
                minimum_client=__minimum_compatible_client__,
            )
        except Exception as e:
            logger.error(f"GetVersion failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.VersionResponse(version=__version__)

    def CheckUpdate(self, request, context):
        """Check for available updates."""
        logger.debug("gRPC CheckUpdate")

        try:
            info = check_for_update()
            return tars_pb2.UpdateCheckResponse(
                update_available=info["update_available"],
                current_version=info["current_version"],
                latest_version=info["latest_version"],
                severity=info["severity"],
                release_notes=info["release_notes"],
                pypi_url=info["pypi_url"],
                github_url=info["github_url"],
            )
        except Exception as e:
            logger.error(f"CheckUpdate failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.UpdateCheckResponse(
                update_available=False,
                current_version=__version__,
                latest_version=__version__,
                severity="none",
            )

    def Health(self, request, context):
        """Get health status."""
        logger.debug("gRPC Health")

        if not self.hw:
            return tars_pb2.HealthResponse(status="error", version=__version__)

        try:
            health_data = self.hw.get_health()
            
            hardware = tars_pb2.HardwareStatus(
                servos=health_data["hardware"]["servos"],
                camera=health_data["hardware"]["camera"],
                audio=health_data["hardware"]["audio"],
                display=health_data["hardware"]["display"],
                battery=health_data["hardware"]["battery"],
                moving=health_data["hardware"]["moving"]
            )

            battery_data = health_data["battery"]
            battery_status = tars_pb2.BatteryStatus(
                level=battery_data["level"],
                charging=battery_data["charging"],
                voltage=battery_data["voltage"],
                current=battery_data["current"]
            )

            return tars_pb2.HealthResponse(
                status="running",
                version=__version__,
                grpc_available=True,
                webrtc_available=health_data["webrtc"]["available"],
                webrtc_connected=health_data["webrtc"]["connected"],
                hardware=hardware,
                battery=battery_status
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.HealthResponse(status="error", version=__version__)

    def Move(self, request, context):
        """Execute a movement."""
        movement = request.movement
        speed = request.speed if request.speed > 0 else 1.0

        logger.info(f"gRPC Move: {movement} (speed={speed})")

        if not self.hw:
            error_msg = "Hardware controller not available"
            logger.error(error_msg)
            return tars_pb2.MoveResponse(
                success=False,
                duration=0.0,
                error=error_msg
            )

        try:
            result = self.hw.execute_movement(movement, speed)
            return tars_pb2.MoveResponse(
                success=result["success"],
                duration=result["duration"],
                error=""
            )

        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            return tars_pb2.MoveResponse(
                success=False,
                duration=0.0,
                error=error_msg
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

        logger.debug(f"gRPC SetEmotion: {emotion}")

        if not self.hw:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Hardware controller not available")
            return tars_pb2.Empty()

        try:
            self.hw.set_emotion(emotion)
            return tars_pb2.Empty()

        except ValueError as e:
            logger.error(f"SetEmotion failed: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return tars_pb2.Empty()
        except Exception as e:
            logger.error(f"SetEmotion failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.Empty()

    def SetEyeState(self, request, context):
        """Set eye state."""
        state = request.state

        logger.debug(f"gRPC SetEyeState: {state}")

        if not self.hw:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Hardware controller not available")
            return tars_pb2.Empty()

        try:
            self.hw.set_eye_state(state)
            return tars_pb2.Empty()

        except ValueError as e:
            logger.error(f"SetEyeState failed: {e}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
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

        if not self.hw:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Hardware controller not available")
            return tars_pb2.CaptureResponse()

        try:
            result = self.hw.capture_camera(width, height, quality)
            
            return tars_pb2.CaptureResponse(
                image=result["image"],
                width=result["width"],
                height=result["height"],
                format=result["format"]
            )

        except ValueError as e:
            logger.error(f"CaptureCamera failed: {e}")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(str(e))
            return tars_pb2.CaptureResponse()
        except Exception as e:
            logger.error(f"CaptureCamera failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.CaptureResponse()

    def GetStatus(self, request, context):
        """Get robot status."""
        logger.debug("gRPC GetStatus")

        if not self.hw:
            return tars_pb2.StatusResponse(connected=False)

        try:
            status = self.hw.get_status()
            
            battery_data = status["battery"]
            battery_status = tars_pb2.BatteryStatus(
                level=battery_data["level"],
                charging=battery_data["charging"],
                voltage=battery_data["voltage"],
                current=battery_data["current"]
            )

            return tars_pb2.StatusResponse(
                connected=status["connected"],
                battery=battery_status,
                current_emotion=status["current_emotion"],
                current_eye_state=status["current_eye_state"],
                is_moving=status["is_moving"],
                current_movement=status["current_movement"]
            )

        except Exception as e:
            logger.error(f"GetStatus failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return tars_pb2.StatusResponse(connected=False)

    def Reset(self, request, context):
        """Reset robot to neutral position."""
        logger.info("gRPC Reset")

        if not self.hw:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Hardware controller not available")
            return tars_pb2.Empty()

        try:
            self.hw.reset_position()
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
                    movement="",
                    progress=0.0
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
                # Process audio level
                if self.display is not None:
                    self.display.set_audio_level(level, "grpc")

                # Send acknowledgment
                yield tars_pb2.AudioLevelResponse(received=True)

        except Exception as e:
            logger.error(f"StreamAudioLevels failed: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
    def SetMicMute(self, request, context):
        muted = request.muted
        if self.webrtc and hasattr(self.webrtc, 'mic_track') and self.webrtc.mic_track:
            self.webrtc.mic_track.mute(muted)
        logger.info(f"gRPC SetMicMute: {muted}")
        return tars_pb2.Empty()

    def GetMicMute(self, request, context):
        muted = False
        if self.webrtc and hasattr(self.webrtc, 'mic_track') and self.webrtc.mic_track:
            muted = self.webrtc.mic_track._muted
        return tars_pb2.MicMuteResponse(muted=muted)

    def LaunchApp(self, request, context):
        """Switch display to a named app (eyes/spectrum/clock)."""
        if self.display is None:
            return tars_pb2.AppResponse(success=False, error="Display not available")
        success = self.display.launch_app(request.name)
        if not success:
            return tars_pb2.AppResponse(success=False, error=f"Unknown app: {request.name}")
        logger.info(f"gRPC LaunchApp: {request.name}")
        return tars_pb2.AppResponse(success=True)

    def ListApps(self, request, context):
        """List available display apps."""
        apps = []
        if self.display:
            for a in self.display.get_available_apps():
                apps.append(tars_pb2.AppInfo(name=a["name"], label=a["label"]))
        return tars_pb2.AppListResponse(apps=apps)

    def ActivateScreensaver(self, request, context):
        """Force-activate a screensaver by name (or random if name is empty)."""
        if self.display:
            name = request.name if request.name else None
            self.display.activate_screensaver(name)
            logger.info(f"gRPC ActivateScreensaver: {name or 'random'}")
        return tars_pb2.Empty()

    def DeactivateScreensaver(self, request, context):
        """Deactivate screensaver, returning to active app."""
        if self.display:
            self.display.deactivate_screensaver()
        return tars_pb2.Empty()

    def ListScreensavers(self, request, context):
        """List available screensavers."""
        names = self.display.get_available_screensavers() if self.display else []
        return tars_pb2.ScreensaverListResponse(names=names)
