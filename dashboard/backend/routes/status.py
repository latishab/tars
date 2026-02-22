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
_daemon_url = None


def set_modules(battery=None, display=None, camera=None, webrtc=None):
    """Set references to hardware modules."""
    global _battery_module, _display_module, _camera_module, _webrtc_server
    _battery_module = battery
    _display_module = display
    _camera_module = camera
    _webrtc_server = webrtc


def set_daemon_url(url: str):
    """Set daemon URL for battery queries."""
    global _daemon_url
    _daemon_url = url


async def get_status_data() -> Dict[str, Any]:
    """Get current status data."""
    # Load config for network info
    config = {}
    try:
        import json
        from pathlib import Path
        config_file = Path("/etc/tars/config.json")
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
    except Exception:
        pass

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
        "voltage": 0.0,
        "current": 0.0,
    }
    if _battery_module:
        # Use local battery module if available
        try:
            battery["level"] = int(_battery_module.normalized_percentage)
            battery["voltage"] = _battery_module.voltage
            battery["current"] = _battery_module.current
        except Exception as e:
            logger.debug(f"Battery read error: {e}")
    elif _daemon_url:
        # Query daemon for battery status (uses shared coulomb counting)
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{_daemon_url}/api/battery", timeout=2.0)
                if response.status_code == 200:
                    daemon_battery = response.json()
                    battery["level"] = daemon_battery.get("normalized_percentage", 0)
                    battery["voltage"] = daemon_battery.get("voltage", 0.0)
                    battery["current"] = daemon_battery.get("current", 0.0)
        except Exception as e:
            logger.debug(f"Daemon battery query error: {e}")

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
        "network": {
            "connection_mode": config.get("connection_mode", "local"),
            "tailscale_ip": config.get("tailscale_ip"),
        },
    }


@router.get("/status")
async def get_status():
    """Get current robot status."""
    return await get_status_data()


@router.get("/camera")
async def get_camera():
    """Get camera snapshot as JPEG via gRPC."""
    from fastapi.responses import Response

    try:
        # Use gRPC to get camera from tars_daemon
        import grpc
        import sys
        from pathlib import Path

        # Add src to path for grpc imports
        src_path = Path(__file__).parent.parent.parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from tars_sdk.proto import tars_pb2, tars_pb2_grpc

        # Connect to tars_daemon gRPC
        channel = grpc.insecure_channel('localhost:50051')
        stub = tars_pb2_grpc.TarsServiceStub(channel)

        # Request camera capture
        request = tars_pb2.CaptureRequest(
            width=640,
            height=480,
            quality=80
        )
        response = stub.CaptureCamera(request)
        channel.close()

        if not response.image:
            return {"error": "No image data returned"}

        return Response(
            content=response.image,
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        return {"error": str(e)}


# Movement list (informational endpoint)
MOVEMENTS = [
    "step_forward",
    "walk_forward",
    "step_backward",
    "walk_backward",
    "turn_right",
    "turn_right_slow",
    "turn_left",
    "turn_left_slow",
    "pose",
    "bow",
    "tilt_right",
    "tilt_left",
    "side_side",
    "wave_right",
    "wave_left",
    "neutral_legs",
    "excited",
    "laugh",
    "swing_legs",
]


@router.get("/movements")
async def list_movements():
    """List all available robot movements."""
    return {
        "movements": MOVEMENTS,
        "categories": {
            "walking": ["step_forward", "walk_forward", "step_backward", "walk_backward"],
            "turning": ["turn_right", "turn_right_slow", "turn_left", "turn_left_slow"],
            "expressions": ["wave_right", "wave_left", "bow", "pose", "excited", "laugh"],
            "balance": ["tilt_right", "tilt_left", "side_side", "swing_legs"],
            "utility": ["neutral_legs"],
        }
    }
