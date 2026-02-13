"""Status API routes."""

import psutil
import platform
from typing import Dict, Any

from fastapi import APIRouter
from loguru import logger

router = APIRouter()

# Reference to hardware modules (set by tars_daemon)
_battery_module = None
_display_module = None
_camera_module = None
_webrtc_server = None


def set_modules(battery=None, display=None, camera=None, webrtc=None):
    """Set references to hardware modules."""
    global _battery_module, _display_module, _camera_module, _webrtc_server
    _battery_module = battery
    _display_module = display
    _camera_module = camera
    _webrtc_server = webrtc


async def get_status_data() -> Dict[str, Any]:
    """Get current status data."""
    # System stats
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    # CPU temperature (Pi specific)
    cpu_temp = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = int(f.read().strip()) / 1000.0
    except (FileNotFoundError, ValueError):
        pass

    # Battery status
    battery = {
        "level": 0,
        "charging": False,
        "voltage": 0.0,
        "current": 0.0,
    }
    if _battery_module:
        try:
            battery["level"] = int(_battery_module.normalized_percentage)
            battery["charging"] = _battery_module.charging_state == "CHARGING"
            battery["voltage"] = _battery_module.voltage
            battery["current"] = _battery_module.current
        except Exception as e:
            logger.debug(f"Battery read error: {e}")

    # Display status
    emotion = "neutral"
    eye_state = "idle"
    if _display_module:
        try:
            emotion = _display_module.state.emotion
            eye_state = _display_module.state.eye_state
        except Exception:
            pass

    # WebRTC status
    webrtc_connected = False
    if _webrtc_server:
        try:
            webrtc_connected = _webrtc_server.is_connected
        except Exception:
            pass

    return {
        "type": "status",
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used // (1024 * 1024),
            "memory_total_mb": memory.total // (1024 * 1024),
            "cpu_temp": cpu_temp,
            "platform": platform.machine(),
        },
        "battery": battery,
        "display": {
            "emotion": emotion,
            "eye_state": eye_state,
        },
        "connections": {
            "webrtc": webrtc_connected,
            "grpc": True,  # If we're running, gRPC is available
        },
    }


@router.get("/status")
async def get_status():
    """Get current robot status."""
    return await get_status_data()


@router.get("/camera")
async def get_camera():
    """Get camera snapshot as JPEG."""
    from fastapi.responses import Response

    if not _camera_module:
        return {"error": "Camera not available"}

    try:
        import cv2
        frame = _camera_module.capture_frame()
        if frame is None:
            return {"error": "Failed to capture frame"}

        # Encode as JPEG
        success, buffer = cv2.imencode(
            '.jpg',
            cv2.cvtColor(frame, cv2.COLOR_RGB2BGR),
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not success:
            return {"error": "Failed to encode image"}

        return Response(
            content=buffer.tobytes(),
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        return {"error": str(e)}
