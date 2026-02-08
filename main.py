"""
TARS Control System V3
FastAPI-based control system for servo control and camera capture on Raspberry Pi 5
Uses Servo Control V3 and Movement System
"""
import sys
import base64
import time
from pathlib import Path

# Add src directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import cv2
import numpy as np

# Import servo control functions (V3.1)
from modules import module_servoctl as servoctl
from modules import module_movements as movements
from modules import module_movement_registry as registry

# Initialize camera module
camera = None
try:
    from modules.UI.module_ui_camera import CameraModule
    camera = CameraModule(1280, 720, use_camera_module=True)
    print("✓ Camera initialized successfully")
except Exception as e:
    print(f"⚠ Camera unavailable: {e}")

# Create FastAPI app
app = FastAPI(
    title="TARS Control System V3",
    description="Servo control and camera API for Raspberry Pi 5",
    version="3.0.0"
)

# Add CORS middleware for cross-origin requests from MacBook
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build movement function mapping from registry and module
AVAILABLE_MOVEMENTS = registry.get_all()
MOVEMENT_FUNCTIONS = {}

# Map movement names to functions from module_movements
for movement_name in AVAILABLE_MOVEMENTS.keys():
    if hasattr(movements, movement_name):
        MOVEMENT_FUNCTIONS[movement_name] = getattr(movements, movement_name)

# Pydantic models for request validation
class MoveRequest(BaseModel):
    movements: List[str]

class LegsRequest(BaseModel):
    left_height: Optional[int] = None  # 1-100
    right_height: Optional[int] = None  # 1-100
    left_leg: Optional[int] = None  # 1-100
    right_leg: Optional[int] = None  # 1-100
    speed: float = 0.8


# API Endpoints
@app.get("/")
def root():
    """Root endpoint - service info"""
    return {
        "service": "TARS Control System",
        "version": "3.0.0",
        "servo_controller": "V3",
        "status": "running",
        "camera_available": camera is not None,
        "moving": servoctl.MOVING,
        "available_movements": len(MOVEMENT_FUNCTIONS)
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "moving": servoctl.MOVING,
        "camera": camera is not None and camera.running
    }


@app.get("/state")
def get_state():
    """Get current servo positions and movement state"""
    return {
        "positions": servoctl.servo_positions,
        "moving": servoctl.MOVING,
        "camera_running": camera is not None and camera.running
    }


@app.get("/movements")
def list_movements():
    """List all available movements"""
    all_movements = {}
    for name, info in AVAILABLE_MOVEMENTS.items():
        all_movements[name] = {
            "display_name": info["name"],
            "type": info["type"],
            "available": name in MOVEMENT_FUNCTIONS
        }

    return {
        "movements": all_movements,
        "total": len(all_movements),
        "legs_only": list(registry.get_legs_only().keys()),
        "requires_arms": list(registry.get_has_arms().keys())
    }


@app.post("/move")
def execute_move(request: MoveRequest):
    """
    Execute a sequence of movements

    Available movements depend on hardware configuration (arms present or not).
    Use GET /movements to see all available movements.

    Common movements:
    - step_forward, walk_forward
    - step_backward, walk_backward
    - turn_left, turn_right
    - wave_right, wave_left (legs only)
    - bow, pose, laugh, swing_legs
    - right_hi, left_hi (requires arms)
    - monster, happy_dance (requires arms)
    """
    if servoctl.MOVING:
        raise HTTPException(status_code=409, detail="Robot is already moving")

    # Validate all movements first
    for movement in request.movements:
        if movement not in MOVEMENT_FUNCTIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown movement: {movement}. Use GET /movements to see available movements."
            )

    # Execute movements sequentially
    results = []
    for movement in request.movements:
        try:
            MOVEMENT_FUNCTIONS[movement]()
            results.append({"movement": movement, "status": "completed"})
        except Exception as e:
            results.append({"movement": movement, "status": "error", "error": str(e)})
            raise HTTPException(status_code=500, detail=f"Movement '{movement}' failed: {str(e)}")

    return {
        "status": "ok",
        "results": results
    }


@app.post("/move/legs")
def move_legs_manual(request: LegsRequest):
    """
    Manual leg control

    Parameters (all optional, 1-100 range):
    - left_height: Height of left leg (1=up, 100=down)
    - right_height: Height of right leg (1=up, 100=down)
    - left_leg: Left leg forward/back position (1=forward, 50=neutral, 100=backward)
    - right_leg: Right leg forward/back position (1=forward, 50=neutral, 100=backward)
    - speed: Movement speed (0.0-1.0, default 0.8)
    """
    if servoctl.MOVING:
        raise HTTPException(status_code=409, detail="Robot is already moving")

    try:
        # Call move_legs with V3.1 parameter order:
        # left_height, right_height, left_leg, right_leg, speed
        servoctl.move_legs(
            left_height_percent=request.left_height,
            right_height_percent=request.right_height,
            left_leg_percent=request.left_leg,
            right_leg_percent=request.right_leg,
            speed_factor=request.speed
        )

        return {
            "status": "ok",
            "left_height": request.left_height,
            "right_height": request.right_height,
            "left_leg": request.left_leg,
            "right_leg": request.right_leg,
            "speed": request.speed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leg movement failed: {str(e)}")


@app.post("/reset")
def reset_servos():
    """Reset all servos to neutral position"""
    if servoctl.MOVING:
        raise HTTPException(status_code=409, detail="Robot is already moving")

    try:
        servoctl.reset_positions()
        return {"status": "ok", "message": "Servos reset to neutral position"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/disable")
def disable_servos():
    """Disable all servos (power off)"""
    try:
        servoctl.disable_all_servos()
        return {"status": "ok", "message": "All servos disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Disable failed: {str(e)}")


@app.get("/camera/status")
def camera_status():
    """Get camera status"""
    if camera is None:
        return {
            "available": False,
            "running": False,
            "message": "Camera module not initialized"
        }

    return {
        "available": True,
        "running": camera.running,
        "first_frame_captured": camera.first_frame_captured
    }


@app.get("/camera/capture")
def capture_frame():
    """
    Capture current camera frame and return as base64-encoded JPEG

    Returns:
    - status: "ok" or error
    - image: base64-encoded JPEG image
    - format: "jpeg"
    - width: image width
    - height: image height
    """
    if camera is None:
        raise HTTPException(status_code=503, detail="Camera not available")

    if not camera.running:
        raise HTTPException(status_code=503, detail="Camera not running")

    # Get raw frame from camera
    frame = camera.capture_raw_frame()
    if frame is None:
        raise HTTPException(status_code=500, detail="No frame available")

    # Encode frame to JPEG
    try:
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise HTTPException(status_code=500, detail="JPEG encoding failed")

        # Convert to base64
        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        return {
            "status": "ok",
            "image": img_base64,
            "format": "jpeg",
            "width": frame.shape[1],
            "height": frame.shape[0]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame encoding failed: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Print startup info"""
    print("\n" + "="*50)
    print("🤖 TARS Control System V3 Starting")
    print("="*50)
    print(f"Servo Controller: V3")
    print(f"Camera: {'✓ Available' if camera else '✗ Not available'}")
    print(f"Servo Control: ✓ Loaded")
    print(f"Available Movements: {len(MOVEMENT_FUNCTIONS)}")
    print(f"API Endpoints: ✓ Ready")
    print(f"\nService running on http://0.0.0.0:8001")
    print(f"API Documentation: http://localhost:8001/docs")
    print("="*50 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
