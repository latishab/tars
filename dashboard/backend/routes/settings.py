"""Settings API routes."""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

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


class EmotionRequest(BaseModel):
    emotion: str


class EyeStateRequest(BaseModel):
    state: str


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

    save_settings(settings)

    return {"success": True, "settings": settings}


@router.post("/emotion")
async def set_emotion(request: EmotionRequest, req: Request):
    """Set display emotion (direct daemon access)."""
    valid_emotions = ['neutral', 'happy', 'sad', 'angry', 'excited', 'afraid', 'sideeye_left', 'sideeye_right', 'sleepy']
    if request.emotion not in valid_emotions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid emotion. Valid: {', '.join(valid_emotions)}"
        )

    try:
        daemon = req.app.state.daemon
        if daemon and daemon.display:
            daemon.display.set_emotion(request.emotion)
            return {"success": True, "emotion": request.emotion}
        else:
            raise HTTPException(status_code=503, detail="Display not available")
    except Exception as e:
        logger.error(f"Failed to set emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eye-state")
async def set_eye_state(request: EyeStateRequest, req: Request):
    """Set eye state (direct daemon access)."""
    valid_states = ["idle", "listening", "thinking", "speaking"]
    if request.state not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state. Valid: {', '.join(valid_states)}"
        )

    try:
        daemon = req.app.state.daemon
        if daemon and daemon.display:
            daemon.display.set_eye_state(request.state)
            return {"success": True, "state": request.state}
        else:
            raise HTTPException(status_code=503, detail="Display not available")
    except Exception as e:
        logger.error(f"Failed to set eye state: {e}")
        raise HTTPException(status_code=500, detail=str(e))
