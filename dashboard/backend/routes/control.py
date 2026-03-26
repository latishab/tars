"""Robot control API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger
import asyncio

import modules.module_movement_registry as registry

router = APIRouter()

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

class VentilateRequest(BaseModel):
    active: bool

class PlaySequenceRequest(BaseModel):
    steps: list[dict]

class SaveSequenceRequest(BaseModel):
    name: str
    steps: list[dict]
    type: str = "gesture"
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
    """List all movements with their type (locomotion or gesture).

    Merges the built-in registry with custom_sequences.json so that
    overridden entries report the type from the sequences file.
    Returns: {"movements": [{"name": str, "type": str}, ...]}
    """
    merged = registry.get_merged()
    movements = sorted(
        [{"name": k, "type": v["type"]} for k, v in merged.items()],
        key=lambda x: x["name"],
    )
    return {"movements": movements}

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

@router.post("/ventilate")
async def set_ventilate(request: VentilateRequest):
    """Enter or exit ventilate pose."""
    from modules.module_movements import ventilate_on, ventilate_off
    from modules.module_cputemp import is_ventilating
    loop = asyncio.get_event_loop()
    if request.active:
        await loop.run_in_executor(None, ventilate_on)
    else:
        await loop.run_in_executor(None, ventilate_off)
    return {"status": "ok", "ventilating": is_ventilating()}

@router.get("/ventilate")
async def get_ventilate():
    """Get current ventilate state."""
    from modules.module_cputemp import is_ventilating
    return {"ventilating": is_ventilating()}

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

    async def run_steps(steps):
        for step in steps:
            if step.get('repeat') is not None:
                for _ in range(step['repeat']):
                    await run_steps(step.get('steps', []))
            elif step.get('movement'):
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=step: daemon.hardware_controller.execute_movement(s['movement'])
                )
                if step.get('hold_time', 0) > 0:
                    await asyncio.sleep(step['hold_time'])
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda s=step: servo.move_legs(
                        s.get('left_height', 50), s.get('right_height', 50),
                        s.get('left_leg', 50), s.get('right_leg', 50),
                        s.get('speed', 0.85)
                    )
                )
                if step.get('hold_time', 0) > 0:
                    await asyncio.sleep(step['hold_time'])

    servo.MOVING = True
    servo._notify_movement_start()
    try:
        await run_steps(request.steps)
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
    """Save a named sequence to disk, normalizing the name to snake_case."""
    name = registry.save(request.name, request.steps, request.type, request.quick)
    return {"status": "ok", "name": name}

@router.get("/saved-sequences")
async def get_saved_sequences():
    """Return all saved sequences."""
    return registry.get_custom()

@router.delete("/saved-sequences/{name}")
async def delete_saved_sequence(name: str):
    """Delete a saved sequence by name (normalizes name)."""
    try:
        registry.delete(name)
    except KeyError as e:
        raise HTTPException(404, str(e))
    return {"status": "ok"}

@router.post("/play-saved/{name}")
async def play_saved_sequence(name: str, req: Request):
    """Play a saved sequence by name (normalizes name)."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")
    try:
        result = daemon.hardware_controller.execute_movement(name)
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"play-saved failed: {e}")
        raise HTTPException(500, str(e))

@router.get("/movement-steps/{name}")
async def get_movement_steps(name: str):
    """Extract move_legs steps from a named movement function."""
    import re
    from pathlib import Path as _Path
    # Custom sequences take priority over built-in movements
    key = registry.normalize_name(name)
    custom = registry.get_custom()
    if key in custom:
        entry = custom[key]
        steps = entry["steps"] if isinstance(entry, dict) else entry
        return {"steps": steps}

    src = _Path(__file__).parent.parent.parent.parent / "src" / "modules" / "module_movements.py"
    if not src.exists():
        raise HTTPException(404, "module_movements.py not found")

    text = src.read_text()

    # Find the function body (search by normalized key)
    fn_match = re.search(r"^def " + re.escape(key) + r"\(.*?\):(.*?)(?=^def |\Z)", text, re.MULTILINE | re.DOTALL)
    if not fn_match:
        raise HTTPException(404, f"Movement '{key}' not found")

    body = fn_match.group(1)

    def collect_block(lines, i, parent_indent):
        """Collect lines indented deeper than parent_indent, starting at i."""
        block = []
        while i < len(lines):
            bl = lines[i]
            if bl.strip() == "":
                i += 1
                continue
            if len(bl) - len(bl.lstrip()) > parent_indent:
                block.append(bl)
                i += 1
            else:
                break
        return block, i

    def resolve(v, variables):
        if v in variables:
            try:
                return int(round(float(variables[v])))
            except (ValueError, TypeError):
                return 50
        try:
            return int(round(float(v)))
        except (ValueError, TypeError):
            return 50

    def extract_steps(lines, variables=None):
        """Extract move_legs steps, handling range loops, tuple-unpacking loops,
        and list variable assignments."""
        if variables is None:
            variables = {}
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue

            indent = len(line) - len(line.lstrip())

            # List assignment: `name = [(a,b,c,d), ...]`
            var_m = re.match(r"\s*(\w+)\s*=\s*\[", line)
            if var_m:
                var_name = var_m.group(1)
                # Collect until closing bracket
                assign_text = line
                j = i + 1
                while j < len(lines) and "]" not in assign_text:
                    assign_text += lines[j]
                    j += 1
                tuples = re.findall(r"\(([^)]+)\)", assign_text)
                parsed = []
                for t in tuples:
                    vals = [v.strip() for v in t.split(",")]
                    parsed.append(vals)
                variables = dict(variables)
                variables[var_name] = parsed
                i = j
                continue

            # `if` block — recurse into body
            if_m = re.match(r"\s*if\s+(.+):", line)
            if if_m:
                block, i = collect_block(lines, i + 1, indent)
                result.extend(extract_steps(block, variables))
                continue

            # `for _ in range(N):` loop — preserve as repeat block
            range_m = re.search(r"for\s+\w+\s+in\s+range\((\d+)\)\s*:", line)
            if range_m:
                repeat = int(range_m.group(1))
                block, i = collect_block(lines, i + 1, indent)
                inner = extract_steps(block, variables)
                result.append({"repeat": repeat, "steps": inner})
                continue

            # `for a, b, c, d in varname[optional_slice]:` tuple-unpacking loop
            tuple_m = re.match(r"\s*for\s+([\w\s,]+)\s+in\s+(\w+)(\[.*?\])?\s*:", line)
            if tuple_m:
                var_names = [v.strip() for v in tuple_m.group(1).split(",")]
                seq_name = tuple_m.group(2)
                slice_part = tuple_m.group(3)
                block, i = collect_block(lines, i + 1, indent)
                seq = variables.get(seq_name, [])
                if slice_part:
                    try:
                        seq = eval(f"seq{slice_part}", {"seq": seq})
                    except Exception:
                        pass
                for tup in seq:
                    local = dict(variables)
                    for k, v in zip(var_names, tup):
                        local[k] = v
                    result.extend(extract_steps(block, local))
                continue

            # move_legs call (literal or variable args)
            ml = re.search(r"move_legs\(([^)]+)\)", line)
            if ml:
                args = [a.strip() for a in ml.group(1).split(",")]
                if len(args) >= 5:
                    lh = resolve(args[0], variables)
                    rh = resolve(args[1], variables)
                    ll = resolve(args[2], variables)
                    rl = resolve(args[3], variables)
                    spd_str = args[4]
                    try:
                        spd = round(float(variables[spd_str]) if spd_str in variables else float(spd_str), 2)
                    except (ValueError, TypeError):
                        spd = 0.85
                    hold = 0.0
                    for j in range(i + 1, min(i + 3, len(lines))):
                        sl = re.search(r"time\.sleep\(([^)]+)\)", lines[j])
                        if sl:
                            try:
                                hold = float(sl.group(1))
                            except ValueError:
                                pass
                            break
                    result.append({
                        "left_height": lh, "right_height": rh,
                        "left_leg": ll, "right_leg": rl,
                        "speed": spd, "hold_time": hold
                    })
            i += 1
        return result

    steps = extract_steps(body.splitlines())

    # Follow delegation to impl functions (e.g. turn_left -> _turn_left_impl)
    if not steps:
        impl_match = re.search(r"^def _" + re.escape(key) + r"_impl\(.*?\):(.*?)(?=^def |\Z)", text, re.MULTILINE | re.DOTALL)
        if impl_match:
            steps = extract_steps(impl_match.group(1).splitlines())

    if not steps:
        raise HTTPException(422, f"No move_legs calls found in '{key}'")

    return {"name": key, "steps": steps}

