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

    # Battery status - query local battery endpoint
    battery = {
        "level": 0,
        "voltage": 0.0,
        "current": 0.0,
    }
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/status/battery", timeout=2.0)
            if response.status_code == 200:
                battery_data = response.json()
                battery["level"] = battery_data.get("normalized_percentage", 0)
                battery["voltage"] = battery_data.get("voltage", 0.0)
                battery["current"] = battery_data.get("current", 0.0)
    except Exception as e:
        logger.debug(f"Battery query error: {e}")

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


@router.get("/")
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
