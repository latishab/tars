"""Settings API routes."""

import json
import httpx
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent.parent.parent / "state" / "settings.json"

# Daemon URL (running on same host)
DAEMON_URL = "http://localhost:8001"

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
async def set_emotion(request: EmotionRequest):
    """Set display emotion by proxying to daemon."""
    valid_emotions = ["default", "happy", "angry", "tired", "surprised", "confused"]
    if request.emotion not in valid_emotions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid emotion. Valid: {', '.join(valid_emotions)}"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DAEMON_URL}/api/emotion",
                json={"emotion": request.emotion},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to daemon: {e}")
        raise HTTPException(status_code=503, detail="Daemon not available")
    except httpx.HTTPStatusError as e:
        logger.error(f"Daemon returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eye-state")
async def set_eye_state(request: EyeStateRequest):
    """Set eye state by proxying to daemon."""
    valid_states = ["idle", "listening", "thinking", "speaking"]
    if request.state not in valid_states:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state. Valid: {', '.join(valid_states)}"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DAEMON_URL}/api/eye-state",
                json={"state": request.state},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to daemon: {e}")
        raise HTTPException(status_code=503, detail="Daemon not available")
    except httpx.HTTPStatusError as e:
        logger.error(f"Daemon returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set eye state: {e}")
        raise HTTPException(status_code=500, detail=str(e))
