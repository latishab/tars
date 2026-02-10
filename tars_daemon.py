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
import io
import base64

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing modules
from modules.module_servoctl import (
    reset_positions, disable_all_servos, servo_positions, MOVING, move_legs
)
from modules.module_movements import (
    step_forward, step_backward, walk_forward, walk_backward,
    turn_left_slow, turn_right_slow
)

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
    from modules.module_facetracking import FaceTracker, MediaPipeFaceTracker, MEDIAPIPE_AVAILABLE
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


# Movement mapping (uses existing module_movements functions)
MOVEMENT_MAP = {
    "forward": step_forward,
    "backward": step_backward,
    "walk_forward": walk_forward,
    "walk_backward": walk_backward,
    "left": turn_left_slow,
    "right": turn_right_slow,
}


class TARSDaemon:
    """
    Unified daemon for TARS robot.

    Manages:
    - WebRTC connection to host computer (audio streaming)
    - REST API for hardware control
    - Display (eyes, spectrum)
    - Hardware (servos, camera) via existing modules
    """

    def __init__(
        self,
        api_port: int = 8001,
        display_enabled: bool = True,
        face_tracking_enabled: bool = False,
        webrtc_enabled: bool = True,
    ):
        self.api_port = api_port
        self.display_enabled = display_enabled
        self.face_tracking_enabled = face_tracking_enabled
        self.webrtc_enabled = webrtc_enabled

        # Components (initialized in startup)
        self.webrtc: Optional[WebRTCServer] = None
        self.display: Optional[DisplayManager] = None
        self.camera: Optional[CameraModule] = None
        self.audio: Optional[AudioModule] = None
        self.face_tracker: Optional[FaceTracker] = None
        self.battery: Optional[BatteryModule] = None

        # FastAPI app
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
            title="TARS Hardware Daemon",
            version="2.0.0",
            lifespan=lifespan
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

        return app

    def _register_routes(self, app: FastAPI):
        """Register all API routes"""

        # === Models ===
        class MoveRequest(BaseModel):
            movements: list[str]

        class LegsRequest(BaseModel):
            left_height: int = 50
            right_height: int = 50
            left_leg: int = 50
            right_leg: int = 50
            speed: float = 0.8

        class DisplayModeRequest(BaseModel):
            mode: str

        class EyeStateRequest(BaseModel):
            state: str

        class EmotionRequest(BaseModel):
            emotion: str

        class LookRequest(BaseModel):
            x: float
            y: float

        class AudioLevelRequest(BaseModel):
            level: float
            source: str

        class FacePositionRequest(BaseModel):
            x: int = 0
            y: int = 0
            width: int = 640
            height: int = 480
            detected: bool = False

        class AnimationRequest(BaseModel):
            animation: str

        # === WebRTC Signaling ===
        class OfferRequest(BaseModel):
            sdp: str
            type: str

        @app.post("/api/offer")
        async def handle_webrtc_offer(request: OfferRequest):
            """
            WebRTC signaling endpoint.
            MacBook sends SDP offer, RPi responds with SDP answer.
            """
            if not self.webrtc:
                raise HTTPException(503, "WebRTC server not available")

            try:
                answer = await self.webrtc.handle_offer(request.sdp, request.type)
                return answer
            except Exception as e:
                logger.error(f"Failed to handle WebRTC offer: {e}")
                raise HTTPException(500, f"WebRTC offer failed: {str(e)}")

        # === Health ===
        @app.get("/")
        @app.get("/health")
        def health():
            return {
                "service": "TARS Hardware Daemon",
                "version": "2.0.0",
                "status": "running" if self._running else "starting",
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
                "battery": self.battery.get_battery_status() if self.battery else {"available": False}
            }

        # === Movement (uses existing module_movements) ===
        @app.get("/state")
        def get_state():
            return {"positions": dict(servo_positions), "moving": MOVING}

        @app.post("/move")
        def execute_move(body: MoveRequest):
            if MOVING:
                raise HTTPException(409, "Already moving")

            results = []
            for movement in body.movements:
                if movement not in MOVEMENT_MAP:
                    raise HTTPException(
                        400,
                        f"Unknown movement: {movement}. Valid: {list(MOVEMENT_MAP.keys())}"
                    )
                MOVEMENT_MAP[movement]()
                results.append({"movement": movement, "status": "completed"})

            return {"status": "ok", "results": results}

        @app.post("/move/legs")
        def move_legs_direct(request: LegsRequest):
            if MOVING:
                raise HTTPException(409, "Already moving")
            move_legs(request.left_height, request.right_height,
                      request.left_leg, request.right_leg, request.speed)
            return {"status": "ok"}

        @app.post("/reset")
        def reset():
            reset_positions()
            return {"status": "ok", "message": "Reset to neutral"}

        @app.post("/disable")
        def disable():
            disable_all_servos()
            return {"status": "ok", "message": "Servos disabled"}

        # === Camera (uses existing module_camera) ===
        @app.get("/camera/capture")
        def capture():
            if not self.camera:
                raise HTTPException(503, "Camera not available")

            try:
                frame = self.camera.capture_frame()

                from PIL import Image
                img = Image.fromarray(frame)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)

                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                return {
                    "status": "ok",
                    "image": img_base64,
                    "format": "jpeg",
                    "width": img.width,
                    "height": img.height
                }
            except Exception as e:
                raise HTTPException(500, f"Capture failed: {str(e)}")

        @app.get("/camera/status")
        def camera_status():
            return {
                "available": self.camera is not None and self.camera.is_available() if self.camera else False,
                "running": self.camera is not None and self.camera.is_available() if self.camera else False,
                "camera_type": self.camera.get_camera_type() if self.camera else None
            }

        # === Audio ===
        @app.get("/audio/status")
        def audio_status():
            if self.audio is None:
                return {"available": False}
            return {
                "available": True,
                "recording": self.audio.is_recording,
                "playing": self.audio.is_playing,
                "device": self.audio.get_device_info()
            }

        # === Display ===
        @app.post("/display/mode")
        def set_display_mode(body: DisplayModeRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.set_mode(body.mode)
            return {"status": "ok", "mode": body.mode}

        @app.post("/eyes/state")
        def set_eye_state(body: EyeStateRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.set_eye_state(body.state)
            return {"status": "ok", "state": body.state}

        @app.post("/eyes/emotion")
        def set_emotion(body: EmotionRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.set_emotion(body.emotion)
            return {"status": "ok", "emotion": body.emotion}

        @app.post("/eyes/look")
        def set_look(body: LookRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.set_look(body.x, body.y)
            return {"status": "ok"}

        @app.post("/eyes/blink")
        def trigger_blink():
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.blink()
            return {"status": "ok"}

        @app.post("/eyes/animation")
        def play_animation(body: AnimationRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.play_animation(body.animation)
            return {"status": "ok"}

        @app.post("/display/audio")
        def set_audio_level(body: AudioLevelRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")
            self.display.set_audio_level(body.level, body.source)
            return {"status": "ok"}

        @app.post("/eyes/face")
        def set_face_position(body: FacePositionRequest):
            if not self.display:
                raise HTTPException(503, "Display not available")

            if body.detected:
                self.display.set_face_position(body.x, body.y, body.width, body.height, True)
            else:
                self.display.set_face_position(0, 0, 1, 1, False)

            return {"status": "ok"}

        @app.get("/display/status")
        def display_status():
            if not self.display:
                return {"available": False}
            return {"available": True, **self.display.get_status()}

        # === Battery ===
        @app.get("/battery/status")
        def battery_status():
            if not self.battery:
                return {"available": False}
            return {"available": True, **self.battery.get_battery_status()}

        @app.get("/battery/percentage")
        def battery_percentage():
            if not self.battery:
                raise HTTPException(503, "Battery monitoring not available")
            return {
                "percentage": self.battery.get_battery_percentage(),
                "normalized": self.battery.get_normalized_percentage()
            }

    async def _startup(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("Starting TARS Daemon v2.0")
        logger.info("=" * 60)

        # Initialize camera (uses existing module)
        if CAMERA_AVAILABLE:
            try:
                self.camera = CameraModule(1280, 720)
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
                else:
                    logger.warning("✗ Battery sensor not detected")
                    self.battery = None
            except Exception as e:
                logger.warning(f"✗ Battery monitoring not available: {e}")
                self.battery = None

        # Start WebRTC server (waits for MacBook to connect)
        if self.webrtc_enabled and WEBRTC_AVAILABLE:
            try:
                self.webrtc = WebRTCServer(
                    on_state_change=self._on_state_change,
                    on_emotion=self._on_emotion,
                    on_connected=self._on_webrtc_connected,
                    on_disconnected=self._on_webrtc_disconnected,
                )
                await self.webrtc.start()
                logger.info("✓ WebRTC server started (waiting for AI brain connection)")
            except Exception as e:
                logger.warning(f"✗ WebRTC server failed to start: {e}")
                logger.info("  Running in standalone mode (REST API only)")

        # Start face tracking
        if self.face_tracking_enabled and self.camera and self.display and FACETRACKING_AVAILABLE:
            try:
                # Use MediaPipe if available, otherwise OpenCV
                if MEDIAPIPE_AVAILABLE:
                    self.face_tracker = MediaPipeFaceTracker(
                        camera=self.camera,
                        on_face_detected=self._on_face_detected,
                        on_face_lost=self._on_face_lost
                    )
                    logger.info("✓ Face tracking initialized (MediaPipe)")
                else:
                    self.face_tracker = FaceTracker(
                        camera=self.camera,
                        on_face_detected=self._on_face_detected,
                        on_face_lost=self._on_face_lost
                    )
                    logger.info("✓ Face tracking initialized (OpenCV)")

                self.face_tracker.start()
            except Exception as e:
                logger.warning(f"✗ Face tracking not available: {e}")

        self._running = True
        logger.info("=" * 60)
        logger.info("TARS Daemon ready")
        logger.info(f"  REST API:     http://0.0.0.0:{self.api_port}")
        logger.info(f"  Docs:         http://0.0.0.0:{self.api_port}/docs")
        if self.webrtc:
            logger.info(f"  WebRTC:       Waiting for AI brain (POST /api/offer)")
        if self.face_tracker:
            logger.info(f"  Tracking:     Face tracking enabled")
        logger.info("=" * 60)

    async def _shutdown(self):
        """Cleanup all components"""
        logger.info("Shutting down TARS Daemon...")
        self._running = False

        if self.face_tracker:
            self.face_tracker.stop()
        if self.battery:
            self.battery.stop()
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
                        voltage=status['voltage'],
                        charging=status['is_charging']
                    )
                await asyncio.sleep(2.0)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Battery display update error: {e}")
                await asyncio.sleep(5.0)

    def run(self):
        """Run the daemon (blocking)"""
        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.api_port,
            log_level="info"
        )


# === Entry Point ===

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="TARS Unified Daemon")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8001,
        help="REST API port (default: 8001)"
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
    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    daemon = TARSDaemon(
        api_port=args.port,
        display_enabled=not args.no_display,
        webrtc_enabled=not args.no_webrtc,
        face_tracking_enabled=args.face_tracking,
    )

    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    daemon.run()


if __name__ == "__main__":
    main()
