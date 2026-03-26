"""Settings API routes."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

_CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "src" / "config.ini"


def _detect_layout(name: str) -> str:
    """Detect controller layout from device name."""
    n = name.lower()
    if any(k in n for k in ("dualshock", "dualsense", "wireless controller", "sony", "playstation")):
        return "playstation"
    if any(k in n for k in ("xbox", "microsoft", "xinput")):
        return "xbox"
    # Nintendo Switch Pro Controller, 8BitDo in Switch mode, etc.
    return "nintendo"


def _get_controller_name() -> str:
    """Read controller_name from config.ini."""
    try:
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(_CONFIG_FILE)
        return cfg.get("CONTROLS", "controller_name", fallback="")
    except Exception:
        return ""

router = APIRouter()

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "state" / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "display": {
        "brightness": 100,
        "default_emotion": "neutral",
        "screensaver_timeout": 300,
    },
    "audio": {
        "volume": 80,
        "mic_gain": 50,
    },
    "movement": {
        "speed_multiplier": 1.0,
        "enable_idle_animations": True,
    },
    "network": {
        "hostname": "tars",
        "mdns_enabled": True,
    },
    "controller": {
        "mappings": {
            "BTN_SOUTH": "pose",
            "BTN_SOUTH+R1": "wave_right",
            "BTN_EAST": "bow",
            "BTN_EAST+R1": "wave_left",
            "BTN_EAST+R2": "side_side",
            "BTN_NORTH": "laugh",
            "BTN_NORTH+R1": "tilt_right",
            "BTN_WEST": "wiggle",
            "BTN_WEST+R1": "tilt_left",
            "DPAD_UP": "walk_forward",
            "DPAD_UP+L2": "step_forward",
            "DPAD_DOWN": "walk_backward",
            "DPAD_DOWN+L2": "step_backward",
            "DPAD_LEFT": "turn_left_slow",
            "DPAD_LEFT+L2": "turn_left",
            "DPAD_RIGHT": "turn_right_slow",
            "DPAD_RIGHT+L2": "turn_right",
        }
    },
}


def load_settings() -> Dict[str, Any]:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                # Merge with defaults
                settings = DEFAULT_SETTINGS.copy()
                for key, value in saved.items():
                    if key in settings and isinstance(settings[key], dict):
                        settings[key].update(value)
                    else:
                        settings[key] = value
                return settings
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]):
    """Save settings to file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


class SettingsUpdate(BaseModel):
    display: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    movement: Optional[Dict[str, Any]] = None
    network: Optional[Dict[str, Any]] = None
    controller: Optional[Dict[str, Any]] = None


@router.get("/settings")
async def get_settings():
    """Get current settings."""
    return load_settings()


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """Update settings."""
    settings = load_settings()

    if update.display:
        settings["display"].update(update.display)
    if update.audio:
        settings["audio"].update(update.audio)
    if update.movement:
        settings["movement"].update(update.movement)
    if update.network:
        settings["network"].update(update.network)
    if update.controller:
        if "controller" not in settings:
            settings["controller"] = DEFAULT_SETTINGS["controller"].copy()
        settings["controller"].update(update.controller)

    save_settings(settings)

    return {"success": True, "settings": settings}


@router.get("/settings/controller-layout")
async def get_controller_layout():
    """Return detected controller layout based on connected device."""
    try:
        from evdev import list_devices, InputDevice
        controller_name = _get_controller_name()
        for path in list_devices():
            try:
                dev = InputDevice(path)
                if controller_name.lower() in dev.name.lower():
                    return {"name": dev.name, "layout": _detect_layout(dev.name)}
            except Exception:
                continue
    except ImportError:
        pass
    # Fallback: use config name
    name = _get_controller_name()
    return {"name": name, "layout": _detect_layout(name) if name else "nintendo"}
