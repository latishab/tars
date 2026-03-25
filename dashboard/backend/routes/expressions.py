"""Expression map API routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from pathlib import Path
from loguru import logger
import json

router = APIRouter()

STATE_FILE = Path(__file__).parent.parent.parent.parent / "state" / "expression_map.json"

DEFAULT_EXPRESSION_MAP = {
    "happy:high":     {"eyes": "happy",     "gesture": "wave_fast"},
    "sad:high":       {"eyes": "sad",        "gesture": "bow_fast"},
    "angry:medium":   {"eyes": "angry",      "gesture": "wiggle"},
    "angry:high":     {"eyes": "angry",      "gesture": "wiggle"},
    "excited:medium": {"eyes": "excited",    "gesture": "wiggle"},
    "excited:high":   {"eyes": "excited",    "gesture": "laugh_fast"},
    "afraid:high":    {"eyes": "afraid",     "gesture": "wiggle"},
    "curious:high":   {"eyes": "curious",    "gesture": "tilt_r_fast"},
    "skeptical:high": {"eyes": "skeptical",  "gesture": "wiggle"},
    "smug:high":      {"eyes": "smug",       "gesture": "tilt_r_fast"},
    "surprised:high": {"eyes": "surprised",  "gesture": "tilt_l_fast"},
}

from modules.module_movement_registry import MOVEMENTS as _MOVEMENT_REGISTRY

def _build_gesture_list() -> list[str]:
    """Return all gesture-type sequence names from registry + custom_sequences.json."""
    names: dict[str, str] = {k: v["type"] for k, v in _MOVEMENT_REGISTRY.items()}
    seqs_file = Path(__file__).parent.parent.parent.parent / "src" / "custom_sequences.json"
    if seqs_file.exists():
        try:
            seqs = json.loads(seqs_file.read_text())
            for name, entry in seqs.items():
                if isinstance(entry, dict) and "type" in entry:
                    names[name] = entry["type"]
        except Exception:
            pass
    return sorted(k for k, t in names.items() if t == "gesture")


def _load_custom() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_custom(data: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


def _merged_map() -> dict:
    custom = _load_custom()
    merged = {**DEFAULT_EXPRESSION_MAP, **custom}
    return merged


class MapEntriesRequest(BaseModel):
    entries: dict[str, dict]


class TriggerRequest(BaseModel):
    emotion: str
    intensity: str


@router.get("/map")
async def get_map():
    """Return merged expression map and list of custom-overridden keys."""
    custom = _load_custom()
    merged = {**DEFAULT_EXPRESSION_MAP, **custom}
    return {"map": merged, "custom_keys": list(custom.keys())}


@router.put("/map")
async def update_map(request: MapEntriesRequest):
    """Save custom mapping entries (merged with existing custom)."""
    custom = _load_custom()
    for key, value in request.entries.items():
        parts = key.split(":")
        if len(parts) != 2:
            raise HTTPException(400, f"Invalid key format: {key} (expected emotion:intensity)")
        custom[key] = value
    _save_custom(custom)
    return {"status": "ok", "custom_keys": list(custom.keys())}


@router.delete("/map/{emotion}/{intensity}")
async def delete_map_entry(emotion: str, intensity: str):
    """Remove a custom override, reverting to default."""
    key = f"{emotion}:{intensity}"
    custom = _load_custom()
    if key not in custom:
        raise HTTPException(404, f"No custom override for {key}")
    del custom[key]
    _save_custom(custom)
    return {"status": "ok", "removed": key}


@router.get("/gestures")
async def list_gestures():
    """List gesture-type movement names for editor dropdowns (excludes locomotion)."""
    return {"gestures": _build_gesture_list()}


@router.post("/trigger")
async def trigger_expression(request: TriggerRequest, req: Request):
    """Trigger emotion eyes + gesture if mapped."""
    daemon = req.app.state.daemon
    if not daemon.hardware_controller:
        raise HTTPException(503, "Hardware controller not available")

    key = f"{request.emotion}:{request.intensity}"
    merged = _merged_map()
    entry = merged.get(key)

    eyes = entry["eyes"] if entry else request.emotion
    gesture = entry.get("gesture") if entry else None

    try:
        daemon.hardware_controller.set_emotion(eyes)
    except Exception as e:
        logger.error(f"set_emotion failed: {e}")
        raise HTTPException(500, str(e))

    if gesture:
        try:
            daemon.hardware_controller.execute_movement(gesture)
        except Exception as e:
            logger.warning(f"execute_movement failed for gesture '{gesture}': {e}")

    return {"status": "ok", "eyes": eyes, "gesture": gesture, "key": key}
