#!/usr/bin/env python3
"""
TARS Unified Daemon
Single process managing: WebRTC audio, REST API, Display, Hardware
Inspired by Reachy Mini's architecture

Uses existing modules from src/modules/ - no code duplication!
"""

import asyncio
import signal
import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

# Set SDL video driver for framebuffer access
os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
os.environ["SDL_FBDEV"] = "/dev/fb0"

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing modules (for state tracking only)
from modules.module_servoctl import MOVING, disable_all_servos
from src.services.hardware_controller import HardwareController

# Optional imports (may not be available on all systems)
try:
    from modules.module_camera import CameraModule
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    logger.warning("Camera module not available")

try:
    from modules.module_audio import AudioModule
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("Audio module not available")

# Import display manager
try:
    from modules.module_display import DisplayManager
    from src.modules.module_wifi import get_wifi_status
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    logger.warning("Display manager not available")

# Import WebRTC server
try:
    from webrtc.server import WebRTCServer
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    logger.warning("WebRTC server not available")

# Import face tracking
try:
    from modules.module_facetracking import FaceTracker
    FACETRACKING_AVAILABLE = True
except ImportError:
    FACETRACKING_AVAILABLE = False
    logger.warning("Face tracking not available")

# Import battery monitoring
try:
    from modules.module_battery import BatteryModule
    BATTERY_AVAILABLE = True
except ImportError:
    BATTERY_AVAILABLE = False
    logger.warning("Battery monitoring not available")

# Import gRPC server
try:
    from grpc_server.server import TARSgRPCServer
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logger.warning("gRPC server not available")

class TARSDaemon:
    """
    Daemon for TARS robot.

    Manages:
    - gRPC server for hardware control (port 50051)
    - WebRTC server for audio streaming (signaling via HTTP)
    - Display (eyes, spectrum)
    - Hardware (servos, camera, battery) via existing modules

    Note: All hardware control is now via gRPC. HTTP only provides:
    - /health - Health check endpoint
    - /api/offer - WebRTC signaling
    """

    def __init__(
        self,
        api_port: int = 8000,
        display_enabled: bool = True,
        face_tracking_enabled: bool = False,
        webrtc_enabled: bool = True,
        grpc_port: int = 50051,
    ):
        self.api_port = api_port
        self.display_enabled = display_enabled
        self.face_tracking_enabled = face_tracking_enabled
        self.webrtc_enabled = webrtc_enabled
        self.grpc_enabled = True  # Always enabled
        self.grpc_port = grpc_port

        # Components (initialized in startup)
        self.webrtc: Optional[WebRTCServer] = None
        self.grpc_server: Optional[TARSgRPCServer] = None
        self.hardware_controller: Optional[HardwareController] = None
        self.display: Optional[DisplayManager] = None
        self.camera: Optional[CameraModule] = None
        self.audio: Optional[AudioModule] = None
        self.face_tracker: Optional[FaceTracker] = None
        self.battery: Optional[BatteryModule] = None

        # FastAPI app
        self.ws_manager = ConnectionManager() if DASHBOARD_AVAILABLE else None
        self.app = self._create_app()

        # State
        self._running = False

    def _create_app(self) -> FastAPI:
        """Create FastAPI application with all routes"""

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self._startup()
            yield
            await self._shutdown()

        app = FastAPI(
            title="TARS Robot API",
            version="3.1.0",
            description="""
## TARS Robot Control & Management API

This API provides complete control over the TARS robot including:

- **/api/control**: Make the robot do things (movements, emotions, eye states, reset)
- **/api/status**: Read robot state (battery, camera, system metrics)
- **/api/apps**: Manage community apps (install, start, stop, uninstall)
- **/api/wifi**: Network configuration (connect, hotspot, status)
- **/api/system**: Settings and updates
- **/api/webrtc**: WebRTC signaling for P2P audio

### WebRTC Audio

WebRTC peer-to-peer audio connection is established via POST /api/webrtc/offer.
The robot streams microphone audio and receives speaker audio bidirectionally.

### gRPC Alternative

For low-latency hardware control, use the gRPC API on port 50051.
See the [tars-sdk documentation](https://github.com/latishab/tars) for details.

### Authentication

Currently no authentication. Deploy behind VPN (Tailscale recommended).

### Base URL

- Local: http://tars.local:8000
- Tailscale: http://tars:8000
""",
            lifespan=lifespan,
            contact={
                "name": "TARS Community",
                "url": "https://github.com/latishab/tars",
            },
            license_info={
                "name": "CC BY-NC 4.0",
                "url": "https://creativecommons.org/licenses/by-nc/4.0/",
            },
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Store daemon reference
        app.state.daemon = self

        # Register routes
        self._register_routes(app)

        # Mount dashboard static files
        if DASHBOARD_AVAILABLE:
            from pathlib import Path
            dashboard_path = Path(__file__).parent / "dashboard" / "frontend" / "dist"
            if dashboard_path.exists():

                # Catch-all route for SPA - serve index.html for any dashboard path
                @app.get("/dashboard/{full_path:path}")
                async def serve_dashboard_spa(full_path: str):
                    """Serve index.html for SPA routing."""
                    from fastapi.responses import FileResponse
                    from pathlib import Path
                    
                    dashboard_index = Path(__file__).parent / "dashboard" / "frontend" / "dist" / "index.html"
                    
                    # Check if the requested path is a static file
                    requested_file = Path(__file__).parent / "dashboard" / "frontend" / "dist" / full_path
                    if requested_file.exists() and requested_file.is_file():
                        return FileResponse(str(requested_file))
                    
                    # Otherwise serve index.html for SPA routing
                    if dashboard_index.exists():
                        return FileResponse(str(dashboard_index))
                    else:
                        raise HTTPException(404, "Dashboard not found")

                app.mount("/dashboard", StaticFiles(directory=str(dashboard_path), html=True), name="dashboard")
                logger.info("✓ Dashboard UI mounted at /dashboard")

                @app.get("/")
                async def root_redirect():
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse(url="/dashboard/", status_code=302)
            else:
                logger.warning(f"Dashboard not built: {dashboard_path}")

        return app

    def _register_routes(self, app: FastAPI):
        """Register HTTP routes for TARS daemon"""

        # === Health Check ===
        @app.get("/")
        @app.get("/health")
        def health():
            """Simple health check endpoint."""
            return {
                "service": "TARS Hardware Daemon",
                "version": "3.0.0",
                "status": "running" if self._running else "starting",
                "protocol": "gRPC",
                "grpc_port": self.grpc_port if self.grpc_enabled else None,
                "hardware": {
                    "servos": True,
                    "camera": self.camera is not None,
                    "audio": self.audio is not None,
                    "display": self.display is not None,
                    "battery": self.battery is not None,
                    "moving": MOVING,
                },
                "webrtc": {
                    "available": WEBRTC_AVAILABLE,
                    "enabled": self.webrtc_enabled,
                    "connected": self.webrtc.is_connected if self.webrtc else False,
                },
                "grpc": {
                    "available": GRPC_AVAILABLE,
                    "enabled": self.grpc_enabled,
                    "port": self.grpc_port if self.grpc_enabled else None,
                },
                "message": "All hardware control now via gRPC - use tars_sdk.TarsClient"
            }

        # === Status Endpoints (inline for direct hardware access) ===
        @app.get("/api/status/camera")
        def camera_preview():
            """Return a JPEG snapshot from the camera."""
            if not self.camera or not self.camera.is_available():
                raise HTTPException(503, "Camera not available")

            frame = self.camera.capture_frame()
            if frame is None:
                raise HTTPException(500, "Failed to capture frame")

            import cv2
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return Response(content=jpeg.tobytes(), media_type="image/jpeg")

        @app.get("/api/status/battery", tags=["Status & Monitoring"])
        def get_battery_status():
            """Get detailed battery status from hardware controller."""
            if not self.battery:
                raise HTTPException(503, "Battery not available")
            
            try:
                status = self.battery.get_battery_status()
                return status
            except Exception as e:
                logger.error(f"Failed to get battery status: {e}")
                raise HTTPException(500, str(e))

        # === Dashboard Routes ===
        if DASHBOARD_AVAILABLE:
            try:
                # Initialize shared state for status routes
                status_routes.set_modules(
                    battery=self.battery if hasattr(self, 'battery') else None,
                    display=self.display if hasattr(self, 'display') else None,
                    camera=self.camera if hasattr(self, 'camera') else None,
                    webrtc=self.webrtc if hasattr(self, 'webrtc') else None
                )


                # Register routers with new structure
                app.include_router(control_routes.router, prefix="/api/control", tags=["Robot Control"])
                app.include_router(webrtc_routes.router, prefix="/api/webrtc", tags=["WebRTC"])
                app.include_router(status_routes.router, prefix="/api/status", tags=["Status & Monitoring"])
                app.include_router(apps_routes.router, prefix="/api/apps", tags=["Apps"])
                app.include_router(wifi_routes.router, prefix="/api/wifi", tags=["WiFi"])
                app.include_router(system_routes.router, prefix="/api/system", tags=["System"])
                
                logger.info("✓ Dashboard routes registered")
            except Exception as e:
                logger.error(f"Dashboard route error: {e}")

        # WebSocket endpoint for dashboard
        if DASHBOARD_AVAILABLE and self.ws_manager:
            ws_manager_ref = self.ws_manager

            @app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                await ws_manager_ref.connect(websocket)
                try:
                    while True:
                        data = await websocket.receive_text()
                        logger.debug(f"WS rx: {data}")
                except WebSocketDisconnect:
                    ws_manager_ref.disconnect(websocket)


    async def _startup(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("Starting TARS Daemon v2.0")
        logger.info("=" * 60)

        # Initialize camera (uses existing module)
        if CAMERA_AVAILABLE:
            try:
                self.camera = CameraModule(640, 480)
                logger.info("✓ Camera initialized")
            except Exception as e:
                logger.warning(f"✗ Camera not available: {e}")

        # Initialize audio (uses existing module)
        if AUDIO_AVAILABLE:
            try:
                self.audio = AudioModule()
                logger.info(f"✓ Audio initialized: {self.audio.get_device_info()}")
            except Exception as e:
                logger.warning(f"✗ Audio not available: {e}")

        # Initialize display (uses existing display_manager)
        if self.display_enabled and DISPLAY_AVAILABLE:
            try:
                self.display = DisplayManager()
                self.display.start()
                logger.info("✓ Display initialized")
            except Exception as e:
                logger.warning(f"✗ Display not available: {e}")

        # Initialize battery monitoring
        if BATTERY_AVAILABLE:
            try:
                self.battery = BatteryModule()
                if self.battery.sensor_initialized:
                    self.battery.start()
                    logger.info("✓ Battery monitoring started")

                    # Start battery display update task
                    if self.display:
                        asyncio.create_task(self._update_battery_display())
                        asyncio.create_task(self._update_wifi_display())
                else:
                    logger.warning("✗ Battery sensor not detected")
                    self.battery = None
            except Exception as e:
                logger.warning(f"✗ Battery monitoring not available: {e}")
                self.battery = None

        # Start WebRTC server
        if self.webrtc_enabled and WEBRTC_AVAILABLE:
            try:
                self.webrtc = WebRTCServer(
                    on_state_change=self._on_state_change,
                    on_emotion=self._on_emotion,
                    on_connected=self._on_webrtc_connected,
                    on_disconnected=self._on_webrtc_disconnected,
                    on_camera_log=self._on_camera_log,
                )
                await self.webrtc.start()
                logger.info("✓ WebRTC server started (waiting for AI brain connection)")
            except Exception as e:
                logger.warning(f"✗ WebRTC server failed to start: {e}")
                logger.info("  Running in standalone mode (REST API only)")

        # Initialize hardware controller (shared logic for HTTP and gRPC)
        from src.modules import module_servoctl
        from grpc_server.servicer import MOVEMENT_MAP
        
        self.hardware_controller = HardwareController(
            display=self.display,
            camera=self.camera,
            battery=self.battery,
            audio=self.audio,
            webrtc=self.webrtc,
            movement_map=MOVEMENT_MAP,
            servo_module=module_servoctl
        )
        logger.info("✓ Hardware controller initialized")

        # Start gRPC server (required for hardware control)
        if GRPC_AVAILABLE:
            try:
                self.grpc_server = TARSgRPCServer(
                    port=self.grpc_port,
                    hardware_controller=self.hardware_controller,
                    camera=self.camera,
                    display=self.display,
                    battery=self.battery,
                    audio=self.audio,
                    webrtc=self.webrtc
                )
                await self.grpc_server.start()
                logger.success(f"✓ gRPC server started on port {self.grpc_port}")
            except Exception as e:
                logger.error(f"✗ gRPC server failed to start: {e}")
                logger.error("  Cannot continue without gRPC - all hardware control requires it")
                raise
        else:
            logger.error("✗ gRPC not available - install dependencies: pip install grpcio grpcio-tools")
            raise RuntimeError("gRPC dependencies not installed")

        # Start face tracking
        if self.face_tracking_enabled and self.camera and self.display and FACETRACKING_AVAILABLE:
            try:
                self.face_tracker = FaceTracker(
                    camera=self.camera,
                    on_face_detected=self._on_face_detected,
                    on_face_lost=self._on_face_lost
                )
                self.face_tracker.start()
            except Exception as e:
                logger.warning(f"✗ Face tracking not available: {e}")

        self._running = True
        logger.info("=" * 60)
        logger.info("TARS Daemon ready")
        logger.info(f"  HTTP API:     http://0.0.0.0:{self.api_port} (WebRTC signaling + health)")
        logger.info(f"  gRPC API:     0.0.0.0:{self.grpc_port} (hardware control)")
        if self.webrtc:
            logger.info(f"  WebRTC:       Waiting for AI brain (POST /api/offer)")
        if self.face_tracker:
            logger.info(f"  Tracking:     Face tracking enabled")
        logger.info("=" * 60)
        logger.info("🎯 All hardware control now via gRPC - use tars_sdk.TarsClient")
        logger.info("=" * 60)

    async def _shutdown(self):
        """Cleanup all components"""
        logger.info("Shutting down TARS Daemon...")
        self._running = False

        if self.face_tracker:
            self.face_tracker.stop()
        if self.battery:
            self.battery.stop()
        if self.grpc_server:
            await self.grpc_server.stop()
        if self.webrtc:
            await self.webrtc.stop()
        if self.display:
            self.display.stop()
        if self.camera:
            self.camera.close()
        if self.audio:
            self.audio.close()

        disable_all_servos()
        logger.info("TARS Daemon stopped")

    # === Callbacks from WebRTC data channel ===

    def _on_state_change(self, state: str):
        """Handle eye state changes from pipecat"""
        logger.debug(f"State change: {state}")
        if self.display:
            self.display.set_eye_state(state)

    def _on_emotion(self, emotion: str):
        """Handle emotion changes from pipecat"""
        logger.debug(f"Emotion change: {emotion}")
        if self.display:
            self.display.set_emotion(emotion)

    def _on_webrtc_connected(self):
        """Handle WebRTC connection established"""
        logger.info("AI brain connected via WebRTC")
        if self.display:
            # Show connected status on display
            self.display.set_eye_state("idle")

    def _on_webrtc_disconnected(self):
        """Handle WebRTC disconnection"""
        logger.info("AI brain disconnected")
        if self.display:
            # Show waiting status on display
            self.display.set_eye_state("idle")

    def _on_camera_log(self, text: str):
        if self.display:
            self.display.add_camera_log(text)

    # === Callbacks from face tracking ===

    def _on_face_detected(self, face_pos, frame_w: int, frame_h: int):
        """Handle face detection"""
        if self.display:
            self.display.set_face_position(
                face_pos.x, face_pos.y, frame_w, frame_h, True
            )

    def _on_face_lost(self):
        """Handle face lost"""
        if self.display:
            self.display.set_face_position(0, 0, 1, 1, False)

    # === Battery display update ===

    async def _update_battery_display(self):
        """Periodically update battery display"""
        while self._running:
            try:
                if self.battery and self.display:
                    status = self.battery.get_battery_status()
                    self.display.set_battery_status(
                        percentage=status['normalized_percentage'],
                        voltage=status['voltage']
                    )
                await asyncio.sleep(2.0)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Battery display update error: {e}")
                await asyncio.sleep(5.0)

    async def _update_wifi_display(self):
        """Periodically update WiFi display"""
        while self._running:
            try:
                if self.display:
                    mode, ssid = get_wifi_status()
                    self.display.set_wifi_status(mode, ssid)
                await asyncio.sleep(5.0)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"WiFi display update error: {e}")
                await asyncio.sleep(10.0)
    def run(self):
        """Run the daemon (blocking)"""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="info"
        )

# === Dashboard Integration ===
try:
    from fastapi.staticfiles import StaticFiles
    from fastapi.websockets import WebSocketDisconnect
    from fastapi import WebSocket
    from dashboard.backend.routes import (
        status as status_routes,
        settings as settings_routes,
        updates as updates_routes,
        wifi as wifi_routes,
        apps as apps_routes,
        setup as setup_routes,
        control as control_routes,
        system as system_routes,
        webrtc as webrtc_routes,
    )
    from dashboard.backend.ws import ConnectionManager
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Dashboard not available: {e}")
    DASHBOARD_AVAILABLE = False



# === Entry Point ===

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="TARS Unified Daemon")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="REST API port (default: 8000)"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable display (for headless operation)"
    )
    parser.add_argument(
        "--no-webrtc",
        action="store_true",
        help="Disable WebRTC server (REST API only)"
    )
    parser.add_argument(
        "--face-tracking",
        action="store_true",
        help="Enable face tracking (follows faces with eyes)"
    )
    parser.add_argument(
        "--grpc-port",
        type=int,
        default=50051,
        help="gRPC server port (default: 50051)"
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Print systemd service file and installation instructions, then exit"
    )
    args = parser.parse_args()

    if args.install_service:
        import os
        python_path = sys.executable
        user = os.getenv("USER", "pi")
        service = f"""[Unit]
Description=TARS Robot Daemon
After=network.target

[Service]
Type=simple
User={user}
ExecStart={python_path} -m tars_daemon
Restart=on-failure
RestartSec=2
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
"""
        path = "/etc/systemd/system/tars.service"
        print(service)
        print("To install, run:")
        print(f"  sudo tee {path} > /dev/null << 'EOF'")
        print(service.rstrip())
        print("EOF")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable --now tars")
        sys.exit(0)

    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    # Enable aiortc standard logging so encoder errors are visible
    import logging
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("aiortc").setLevel(logging.WARNING)
    logging.getLogger("aioice").setLevel(logging.WARNING)

    daemon = TARSDaemon(
        api_port=args.port,
        display_enabled=not args.no_display,
        webrtc_enabled=not args.no_webrtc,
        face_tracking_enabled=args.face_tracking,
        grpc_port=args.grpc_port,
    )

    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal (SIGINT) — shutting down gracefully")
        sys.exit(0)

    def sigterm_handler(sig, frame):
        # os._exit bypasses Python cleanup so the port is released immediately.
        # gRPC ThreadPoolExecutor uses non-daemon threads that block sys.exit,
        # causing the process to linger on port 8000 and preventing service restart.
        logger.info("Received SIGTERM — exiting immediately to release port")
        import os as _os
        _os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    daemon.run()


if __name__ == "__main__":
    main()
