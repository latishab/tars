"""Movements API routes."""

import time
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# Available movements
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

# Movement functions (set by tars_daemon)
_movement_map = {}
_servoctl = None


def set_movement_modules(movement_map: dict, servoctl=None):
    """Set references to movement modules."""
    global _movement_map, _servoctl
    _movement_map = movement_map
    _servoctl = servoctl


class MoveRequest(BaseModel):
    movement: str
    speed: float = 1.0


class MoveResponse(BaseModel):
    success: bool
    duration: float
    error: str = ""


@router.get("/movements")
async def list_movements():
    """List all available movements."""
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


@router.post("/move", response_model=MoveResponse)
async def execute_move(request: MoveRequest):
    """Execute a movement."""
    movement = request.movement

    if movement not in _movement_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown movement: {movement}. Available: {', '.join(MOVEMENTS)}"
        )

    try:
        start_time = time.time()
        movement_func = _movement_map[movement]
        movement_func()
        duration = time.time() - start_time

        logger.info(f"Movement '{movement}' completed in {duration:.2f}s")

        return MoveResponse(success=True, duration=duration)

    except Exception as e:
        error_msg = f"Movement failed: {str(e)}"
        logger.error(error_msg)
        return MoveResponse(success=False, duration=0.0, error=error_msg)


@router.post("/reset")
async def reset_position():
    """Reset robot to neutral position."""
    if not _servoctl:
        raise HTTPException(status_code=503, detail="Servo control not available")

    try:
        _servoctl.reset_positions()
        return {"success": True}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
