"""
Module : Movement Registry
Author: Charles-Olivier Dion (AtomikSpace)
Contact: atomikspace.labs@gmail.com
Copyright (c) 2026 Charles-Olivier Dion

This file is authored by Charles-Olivier Dion and is dual-licensed.

Non-Commercial License:
This file is licensed under Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC 4.0).
You may use, modify, and redistribute this file for NON-COMMERCIAL purposes only, with attribution.

Commercial License:
Commercial use (including selling products, paid services, SaaS, subscriptions, Patreon rewards, or derivatives)
requires a separate written license from Charles-Olivier Dion (AtomikSpace).

This license applies only to this file and does not override licenses of other files in the repository.
"""

import re
import json
import time
from pathlib import Path

# Built-in movement metadata. Types follow the locomotion/gesture taxonomy.
MOVEMENTS = {
    # locomotion — robot displaces through space
    "step_forward":     {"name": "Step Forward",     "type": "locomotion"},
    "walk_forward":     {"name": "Walk Forward",     "type": "locomotion"},
    "step_backward":    {"name": "Step Backward",    "type": "locomotion"},
    "walk_backward":    {"name": "Walk Backward",    "type": "locomotion"},
    "turn_right":       {"name": "Turn Right",       "type": "locomotion"},
    "turn_right_slow":  {"name": "Turn Right Slow",  "type": "locomotion"},
    "turn_left":        {"name": "Turn Left",        "type": "locomotion"},
    "turn_left_slow":   {"name": "Turn Left Slow",   "type": "locomotion"},
    # gesture — servo movement, no displacement
    "pose":             {"name": "Pose",             "type": "gesture"},
    "bow":              {"name": "Bow",              "type": "gesture"},
    "tilt_right":       {"name": "Tilt Right",       "type": "gesture"},
    "tilt_left":        {"name": "Tilt Left",        "type": "gesture"},
    "side_side":        {"name": "Side Side",        "type": "gesture"},
    "wave_right":       {"name": "Wave Right",       "type": "gesture"},
    "wave_left":        {"name": "Wave Left",        "type": "gesture"},
    "neutral_legs":     {"name": "Neutral Legs",     "type": "gesture"},
    "laugh":            {"name": "Laugh",            "type": "gesture"},
    "swing_legs":       {"name": "Swing Legs",       "type": "gesture"},
    "tilt_quick_right": {"name": "Tilt Quick Right", "type": "gesture"},
    "tilt_quick_left":  {"name": "Tilt Quick Left",  "type": "gesture"},
    "wiggle":           {"name": "Wiggle",           "type": "gesture"},
    "wave_short":       {"name": "Wave Short",       "type": "gesture"},
}

_SEQUENCES_FILE = Path(__file__).parent.parent / "custom_sequences.json"


# ── Name normalization ─────────────────────────────────────────────────────────

def normalize_name(name: str) -> str:
    """Convert any name variant to snake_case.

    'Swing Legs'  -> 'swing_legs'
    'SwingLegs'   -> 'swing_legs'
    'swing-legs'  -> 'swing_legs'
    'swing_legs'  -> 'swing_legs'
    """
    s = re.sub(r'([a-z])([A-Z])', r'\1_\2', name.strip())
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


# ── Custom sequence CRUD ───────────────────────────────────────────────────────

def _load_custom() -> dict:
    if not _SEQUENCES_FILE.exists():
        return {}
    try:
        return json.loads(_SEQUENCES_FILE.read_text())
    except Exception:
        return {}


def _save_custom(data: dict) -> None:
    _SEQUENCES_FILE.write_text(json.dumps(data, indent=2))


def get_custom() -> dict:
    """Return all custom sequences."""
    return _load_custom()


def save(name: str, steps: list, seq_type: str = "gesture", quick: bool = False) -> str:
    """Normalize name and persist sequence to JSON. Returns the normalized key."""
    key = normalize_name(name)
    data = _load_custom()
    data[key] = {"type": seq_type, "quick": quick, "steps": steps}
    _save_custom(data)
    return key


def delete(name: str) -> None:
    """Normalize name and delete sequence. Raises KeyError if not found."""
    key = normalize_name(name)
    data = _load_custom()
    if key not in data:
        raise KeyError(f"Sequence '{key}' not found")
    del data[key]
    _save_custom(data)


# ── Step execution engine ──────────────────────────────────────────────────────

def _execute_steps(steps: list) -> dict:
    """Execute a list of servo steps synchronously.

    module_servoctl is imported lazily to avoid circular imports:
    module_servoctl imports module_movements at module level, and
    module_movements imports from module_servoctl.
    """
    import modules.module_servoctl as _sc

    if _sc.MOVING:
        raise RuntimeError("Robot is already moving")

    custom = _load_custom()

    def run_steps(step_list):
        for step in step_list:
            if step.get("repeat") is not None:
                for _ in range(step["repeat"]):
                    run_steps(step.get("steps", []))
            elif step.get("movement"):
                # Nested named movement — resolve through this registry
                sub_key = normalize_name(step["movement"])
                if sub_key in custom:
                    entry = custom[sub_key]
                    run_steps(entry["steps"] if isinstance(entry, dict) else entry)
                # Built-in nested movements not supported while MOVING=True;
                # not used in any current sequences.
            else:
                lh  = step.get("left_height", 50)
                rh  = step.get("right_height", 50)
                ll  = step.get("left_leg", 50)
                rl  = step.get("right_leg", 50)
                spd = step.get("speed", 0.85)
                _sc.move_legs(lh, rh, ll, rl, spd)

                if _sc.ARMS_PRESENT:
                    lm  = step.get("left_main")
                    lf  = step.get("left_forearm")
                    lhv = step.get("left_hand")
                    rm  = step.get("right_main")
                    rf  = step.get("right_forearm")
                    rhv = step.get("right_hand")
                    if any(v is not None for v in [lm, lf, lhv, rm, rf, rhv]):
                        _sc.move_arm(lm, lf, lhv, rm, rf, rhv, spd)

                hold = step.get("hold_time", 0.0)
                if hold > 0:
                    time.sleep(hold)

    _sc.MOVING = True
    _sc._notify_movement_start()
    start = time.time()
    try:
        run_steps(steps)
        _sc.move_legs(50, 50, 50, 50, 0.8)
        _sc.disable_all_servos()
        return {"success": True, "duration": time.time() - start}
    finally:
        _sc.MOVING = False
        _sc._notify_movement_end()


# ── Unified dispatch ───────────────────────────────────────────────────────────

def execute(name: str, speed: float = 1.0) -> dict:
    """Execute a movement by name. Custom sequences take priority over built-ins.

    Normalizes to snake_case before lookup so 'Swing Legs', 'SwingLegs',
    and 'swing_legs' all resolve to the same movement.

    Raises ValueError for unknown movements.
    Raises RuntimeError if the robot is already moving.
    """
    key = normalize_name(name)

    custom = _load_custom()
    if key in custom:
        entry = custom[key]
        steps = entry["steps"] if isinstance(entry, dict) else entry
        result = _execute_steps(steps)
        result["movement"] = key
        result["source"] = "custom"
        return result

    import modules.module_movements as _mm
    func = getattr(_mm, key, None)
    if func is None:
        raise ValueError(f"Unknown movement: '{name}' (normalized: '{key}')")
    func()
    return {"success": True, "movement": key, "source": "builtin"}


# ── Registry views ─────────────────────────────────────────────────────────────

def get_merged() -> dict:
    """Merged view: built-in movements plus custom sequences, custom shadowing built-ins."""
    result = {k: {"name": v["name"], "type": v["type"], "source": "builtin"}
              for k, v in MOVEMENTS.items()}
    for k, v in _load_custom().items():
        result[k] = {
            "name": k.replace("_", " ").title(),
            "type": v.get("type", "gesture"),
            "quick": v.get("quick", False),
            "source": "custom",
        }
    return result


def get_type(name: str):
    """Return the type string ('gesture' / 'locomotion') or None if unknown."""
    key = normalize_name(name)
    custom = _load_custom()
    if key in custom:
        return custom[key].get("type", "gesture")
    entry = MOVEMENTS.get(key)
    return entry["type"] if entry else None


# ── Backward-compatible helpers ────────────────────────────────────────────────

def get_all():
    return MOVEMENTS

def get_names():
    return [(v["name"], k) for k, v in MOVEMENTS.items()]
