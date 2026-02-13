#!/usr/bin/env python3
"""Start dashboard with hardware module references from tars_daemon"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from dashboard.backend import server as dashboard_server
from dashboard.backend.routes import status as dashboard_status

# Import hardware modules
try:
    from modules.module_battery import BatteryModule
    battery = BatteryModule()
    battery.start()
    print(f"Battery: {battery.normalized_percentage}% @ {battery.voltage}V")
except Exception as e:
    print(f"Battery init failed: {e}")
    battery = None

try:
    from modules.module_display import DisplayManager
    display = DisplayManager()
    print(f"Display: {display.state.emotion}")
except Exception as e:
    print(f"Display init failed: {e}")
    display = None

camera = None  # Camera is managed by tars_daemon
print("Camera: using tars_daemon via gRPC (dashboard uses snapshot only)")

# Set module references
dashboard_status.set_modules(
    battery=battery,
    display=display,
    camera=camera,
    webrtc=None
)

# Set display module for settings (emotion control)
from dashboard.backend.routes import settings as dashboard_settings
dashboard_settings.set_display_module(display)

# Set movement modules if available
try:
    from grpc_server.servicer import MOVEMENT_MAP
    from modules import module_servoctl
    from dashboard.backend.routes import movements as dashboard_movements
    dashboard_movements.set_movement_modules(MOVEMENT_MAP, module_servoctl)
    print("Movement controls enabled")
except ImportError:
    print("Movement controls not available")

print("Starting dashboard on port 8080...")
uvicorn.run(
    dashboard_server.app,
    host="0.0.0.0",
    port=8080,
    log_level="info"
)
