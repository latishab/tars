"""Robot control API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

MOVEMENTS = [
    "step_forward", "walk_forward", "step_backward", "walk_backward",
    "turn_right", "turn_right_slow", "turn_left", "turn_left_slow",
    "pose", "bow", "tilt_right", "tilt_left", "side_side",
    "wave_right", "wave_left", "neutral_legs", "excited", "laugh", "swing_legs",
]

class EmotionRequest(BaseModel):
    emotion: str

class EyeStateRequest(BaseModel):
    state: str

class MoveRequest(BaseModel):
    movement: str
    speed: float = 1.0

@router.post("/emotion")
async def set_emotion(request: EmotionRequest, req: Request):
    """Set display emotion.

    Available emotions: neutral, happy, sad, angry, excited, afraid, sideeye_left, sideeye_right, sleepy
    """
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    try:
        result = daemon.hardware_controller.set_emotion(request.emotion)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to set emotion: {e}")
        raise HTTPException(500, str(e))

@router.post("/eye-state")
async def set_eye_state(request: EyeStateRequest, req: Request):
    """Set eye animation state.

    Available states: idle, listening, thinking, speaking
    """
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    try:
        result = daemon.hardware_controller.set_eye_state(request.state)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Failed to set eye state: {e}")
        raise HTTPException(500, str(e))

@router.get("/movements")
async def list_movements():
    """List all available robot movements."""
    return {"movements": MOVEMENTS}

@router.post("/move")
async def execute_movement(request: MoveRequest, req: Request):
    """Execute a robot movement."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    try:
        result = daemon.hardware_controller.move(request.movement, request.speed)
        return result
    except Exception as e:
        logger.error(f"Movement failed: {e}")
        raise HTTPException(500, str(e))

@router.post("/reset")
async def reset_position(req: Request):
    """Reset robot to neutral position."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    try:
        result = daemon.hardware_controller.reset()
        return result
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(500, str(e))
