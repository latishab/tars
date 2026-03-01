"""Robot control API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from pathlib import Path
from loguru import logger
import asyncio
import json
import re

router = APIRouter()

SEQUENCES_FILE = Path(__file__).parent.parent.parent.parent / "custom_sequences.json"

MOVEMENTS = [
    "step_forward", "walk_forward", "step_backward", "walk_backward",
    "turn_right", "turn_right_slow", "turn_left", "turn_left_slow",
    "pose", "bow", "tilt_right", "tilt_left", "side_side",
    "wave_right", "wave_left", "neutral_legs", "excited", "laugh", "swing_legs",
    "nod", "shake", "tilt_quick_right", "tilt_quick_left", "lean_back", "lean_in",
    "wiggle", "perk_up", "slump", "bow_quick", "wave_short",
]

class EmotionRequest(BaseModel):
    emotion: str

class EyeStateRequest(BaseModel):
    state: str

class MoveRequest(BaseModel):
    movement: str
    speed: float = 1.0

class MoveLegRequest(BaseModel):
    left_height: int
    right_height: int
    left_leg: int
    right_leg: int
    speed: float

class SequenceStep(BaseModel):
    # If movement is set, execute a named movement instead of raw servo positions
    movement: str | None = None
    left_height: int = 50
    right_height: int = 50
    left_leg: int = 50
    right_leg: int = 50
    speed: float = 0.85
    hold_time: float = 0.0

class PlaySequenceRequest(BaseModel):
    steps: list[SequenceStep]

class SaveSequenceRequest(BaseModel):
    name: str
    steps: list[SequenceStep]
    type: str = "movement"
    quick: bool = False

@router.post("/emotion")
async def set_emotion(request: EmotionRequest, req: Request):
    """Set display emotion."""
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
    """Set eye animation state."""
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
        result = daemon.hardware_controller.execute_movement(request.movement, request.speed)
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
        result = daemon.hardware_controller.reset_position()
        return result
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(500, str(e))

@router.post("/move-legs")
async def move_legs(request: MoveLegRequest, req: Request):
    """Move legs to a specific position."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    servo = daemon.hardware_controller.servo_module
    if servo is None:
        raise HTTPException(503, "Servo module not available")

    try:
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: servo.move_legs(
                request.left_height, request.right_height,
                request.left_leg, request.right_leg,
                request.speed
            )
        )
        servo.disable_all_servos()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"move-legs failed: {e}")
        raise HTTPException(500, str(e))

@router.post("/play-sequence")
async def play_sequence(request: PlaySequenceRequest, req: Request):
    """Play a sequence of leg positions."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    servo = daemon.hardware_controller.servo_module
    if servo is None:
        raise HTTPException(503, "Servo module not available")

    if servo.MOVING:
        raise HTTPException(409, "Robot is already moving")

    servo.MOVING = True
    servo._notify_movement_start()
    try:
        for step in request.steps:
            if step.movement:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=step: daemon.hardware_controller.execute_movement(s.movement)
                )
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=step: servo.move_legs(
                        s.left_height, s.right_height,
                        s.left_leg, s.right_leg,
                        s.speed
                    )
                )
            if step.hold_time > 0:
                await asyncio.sleep(step.hold_time)
        # return to neutral
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: servo.move_legs(50, 50, 50, 50, 0.8)
        )
        servo.disable_all_servos()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"play-sequence failed: {e}")
        raise HTTPException(500, str(e))
    finally:
        servo.MOVING = False
        servo._notify_movement_end()

@router.post("/save-sequence")
async def save_sequence(request: SaveSequenceRequest):
    """Save a named sequence to disk."""
    data = {}
    if SEQUENCES_FILE.exists():
        try:
            data = json.loads(SEQUENCES_FILE.read_text())
        except Exception:
            data = {}

    existing = data.get(request.name, {})
    data[request.name] = {**existing, "type": request.type, "quick": request.quick, "steps": [step.dict() for step in request.steps]}
    SEQUENCES_FILE.write_text(json.dumps(data, indent=2))
    return {"status": "ok", "name": request.name}

@router.get("/saved-sequences")
async def get_saved_sequences():
    """Return all saved sequences."""
    if not SEQUENCES_FILE.exists():
        return {}
    try:
        return json.loads(SEQUENCES_FILE.read_text())
    except Exception:
        return {}

@router.delete("/saved-sequences/{name}")
async def delete_saved_sequence(name: str):
    """Delete a saved sequence by name."""
    if not SEQUENCES_FILE.exists():
        raise HTTPException(404, "No sequences file")

    data = json.loads(SEQUENCES_FILE.read_text())
    if name not in data:
        raise HTTPException(404, f"Sequence '{name}' not found")

    del data[name]
    SEQUENCES_FILE.write_text(json.dumps(data, indent=2))
    return {"status": "ok"}

@router.post("/play-saved/{name}")
async def play_saved_sequence(name: str, req: Request):
    """Play a saved sequence by name."""
    if not SEQUENCES_FILE.exists():
        raise HTTPException(404, "No sequences file")

    data = json.loads(SEQUENCES_FILE.read_text())
    if name not in data:
        raise HTTPException(404, f"Sequence '{name}' not found")

    entry = data[name]
    steps_data = entry["steps"] if isinstance(entry, dict) else entry
    steps = [SequenceStep(**s) for s in steps_data]
    return await play_sequence(PlaySequenceRequest(steps=steps), req)

@router.get("/movement-steps/{name}")
async def get_movement_steps(name: str):
    """Extract move_legs steps from a named movement function."""
    from pathlib import Path as _Path
    src = _Path(__file__).parent.parent.parent.parent / "src" / "modules" / "module_movements.py"
    if not src.exists():
        raise HTTPException(404, "module_movements.py not found")

    text = src.read_text()

    # Find the function body
    fn_match = re.search(r"^def " + re.escape(name) + r"\(.*?\):(.*?)(?=^def |\Z)", text, re.MULTILINE | re.DOTALL)
    if not fn_match:
        raise HTTPException(404, f"Movement '{name}' not found")

    body = fn_match.group(1)

    steps = []
    lines = body.splitlines()
    for i, line in enumerate(lines):
        ml = re.search(r"move_legs\(([^)]+)\)", line)
        if not ml:
            continue
        args = [a.strip() for a in ml.group(1).split(",")]
        if len(args) < 5:
            continue
        def parse_val(v, default=50):
            try:
                return int(round(float(v)))
            except (ValueError, TypeError):
                return default
        lh = parse_val(args[0])
        rh = parse_val(args[1])
        ll = parse_val(args[2])
        rl = parse_val(args[3])
        spd = round(float(args[4]), 2) if re.match(r"[\d.]+", args[4]) else 0.85
        hold = 0.0
        # check next non-empty line for time.sleep
        for j in range(i + 1, min(i + 3, len(lines))):
            sl = re.search(r"time\.sleep\(([^)]+)\)", lines[j])
            if sl:
                try:
                    hold = float(sl.group(1))
                except ValueError:
                    pass
                break
        steps.append({
            "left_height": lh, "right_height": rh,
            "left_leg": ll, "right_leg": rl,
            "speed": spd, "hold_time": hold
        })

    if not steps:
        raise HTTPException(422, f"No move_legs calls found in '{name}'")

    return {"name": name, "steps": steps}

