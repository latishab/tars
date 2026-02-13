#!/usr/bin/env python3
"""Start dashboard with hardware module references from tars_daemon"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from dashboard.backend import server as dashboard_server
from dashboard.backend.routes import status as dashboard_status

# Battery is managed by daemon - dashboard will query via internal API
battery = None
print("Battery: querying daemon on port 8001 (shared coulomb counting state)")

try:
    from modules.module_display import DisplayManager
    display = DisplayManager()
    print(f"Display: {display.state.emotion}")
except Exception as e:
    print(f"Display init failed: {e}")
    display = None

camera = None  # Camera is managed by tars_daemon
print("Camera: using tars_daemon via gRPC (dashboard uses snapshot only)")

# Set module references for status monitoring
dashboard_status.set_modules(
    battery=battery,  # None - will query daemon instead
    display=display,
    camera=camera,
    webrtc=None
)

# Set daemon URL for battery queries
dashboard_status.set_daemon_url("http://localhost:8001")

# Emotion control is now proxied to daemon via HTTP - no local display module needed

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
print("Battery and emotion controls proxy to daemon on port 8001")
uvicorn.run(
    dashboard_server.app,
    host="0.0.0.0",
    port=8080,
    log_level="info"
)
